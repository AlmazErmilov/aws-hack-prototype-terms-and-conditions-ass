from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import os

from models import Company, CompanyCreate, CompanyResponse, Risk, UploadTermsRequest, UploadCookieRequest, UploadPrivacyRequest
from services import BedrockService, DynamoDBService, ScraperService, VectorDBService

app = FastAPI(
    title="Terms & Conditions Risk Analyzer",
    description="Analyze privacy risks in Terms and Conditions using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = DynamoDBService()
bedrock_service = BedrockService()
scraper_service = ScraperService()
vector_service = VectorDBService(bedrock_service)

# Serve static files
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page"""
    index_path = os.path.join(frontend_path, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>Terms & Conditions Risk Analyzer API</h1><p>Frontend not found. Use /docs for API documentation.</p>")


@app.get("/api/companies", response_model=List[CompanyResponse])
async def get_companies():
    """Get all companies"""
    companies = db_service.get_all_companies()
    return companies


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """Get a single company by ID"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.post("/api/companies/auto-create", response_model=CompanyResponse)
async def auto_create_company(request: dict):
    """Auto-create a company by fetching all available policies from known URLs"""
    company_name = request.get('company_name')
    category = request.get('category')
    
    if not company_name or not category:
        raise HTTPException(status_code=400, detail="Company name and category are required")
    
    # Check if company already exists
    existing = [c for c in db_service.get_all_companies() if c.get('name').lower() == company_name.lower()]
    if existing:
        raise HTTPException(status_code=400, detail=f"Company '{company_name}' already exists")
    
    # Fetch all available policies
    terms_text = ""
    cookie_text = ""
    privacy_text = ""
    
    try:
        terms_url = scraper_service.get_known_url(company_name.lower(), 'terms')
        if terms_url:
            terms_text = scraper_service.fetch_terms_from_url(terms_url)
    except Exception as e:
        print(f"Failed to fetch terms for {company_name}: {e}")
        
    try:
        cookie_url = scraper_service.get_known_url(company_name.lower(), 'cookie')
        if cookie_url:
            cookie_text = scraper_service.fetch_terms_from_url(cookie_url)
    except Exception as e:
        print(f"Failed to fetch cookie policy for {company_name}: {e}")
        
    try:
        privacy_url = scraper_service.get_known_url(company_name.lower(), 'privacy')
        if privacy_url:
            privacy_text = scraper_service.fetch_terms_from_url(privacy_url)
    except Exception as e:
        print(f"Failed to fetch privacy policy for {company_name}: {e}")
    
    if not terms_text and not cookie_text and not privacy_text:
        raise HTTPException(status_code=400, detail=f"No known URLs found for '{company_name}' or failed to fetch any policies")
    
    # Create company
    company = db_service.create_company(
        name=company_name,
        category=category,
        terms_text=terms_text,
        cookie_text=cookie_text,
        privacy_text=privacy_text
    )
    
    # Analyze each document type
    if terms_text:
        try:
            analysis = bedrock_service.analyze_terms_and_conditions(company_name, terms_text)
            db_service.update_company_analysis(
                company_id=company['id'],
                terms_risks=analysis.get('risks', []),
                terms_summary=analysis.get('summary', '')
            )
            # Index in vector database
            vector_service.index_company_terms(
                company_id=company['id'],
                company_name=company_name,
                terms_text=terms_text
            )
        except Exception as e:
            print(f"Failed to analyze terms for {company_name}: {e}")
    
    if cookie_text:
        try:
            analysis = bedrock_service.analyze_cookie_policy(company_name, cookie_text)
            db_service.update_company_cookie_analysis(
                company_id=company['id'],
                cookie_risks=analysis.get('cookie_risks', []),
                cookie_summary=analysis.get('cookie_summary', '')
            )
        except Exception as e:
            print(f"Failed to analyze cookie policy for {company_name}: {e}")
    
    if privacy_text:
        try:
            analysis = bedrock_service.analyze_privacy_policy(company_name, privacy_text)
            db_service.update_company_privacy_analysis(
                company_id=company['id'],
                privacy_risks=analysis.get('privacy_risks', []),
                privacy_summary=analysis.get('privacy_summary', '')
            )
        except Exception as e:
            print(f"Failed to analyze privacy policy for {company_name}: {e}")
    
    return db_service.get_company(company['id'])


@app.post("/api/companies", response_model=CompanyResponse)
async def create_company(request: UploadTermsRequest):
    """Create a new company and analyze its documents"""
    
    # Get document texts - either from direct input or by scraping URLs
    terms_text = request.terms_text
    cookie_text = request.cookie_text
    privacy_text = request.privacy_text

    # Fetch terms
    if request.terms_url and not terms_text:
        try:
            terms_text = scraper_service.fetch_terms_from_url(request.terms_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Terms URL error: {str(e)}")

    # Fetch cookie policy
    if request.cookie_url and not cookie_text:
        try:
            cookie_text = scraper_service.fetch_terms_from_url(request.cookie_url)
        except ValueError as e:
            print(f"Cookie URL error: {e}")  # Don't fail for optional documents

    # Fetch privacy policy
    if request.privacy_url and not privacy_text:
        try:
            privacy_text = scraper_service.fetch_terms_from_url(request.privacy_url)
        except ValueError as e:
            print(f"Privacy URL error: {e}")  # Don't fail for optional documents

    # At least terms are required
    if not terms_text:
        raise HTTPException(status_code=400, detail="Either terms_text or terms_url is required")

    # Create company entry
    company = db_service.create_company(
        name=request.company_name,
        category=request.category,
        terms_text=terms_text,
        cookie_text=cookie_text or '',
        privacy_text=privacy_text or ''
    )

    # Analyze terms using Bedrock
    if terms_text:
        try:
            analysis = bedrock_service.analyze_terms_and_conditions(
                company_name=request.company_name,
                terms_text=terms_text
            )
            db_service.update_company_analysis(
                company_id=company['id'],
                terms_risks=analysis.get('risks', []),
                terms_summary=analysis.get('summary', '')
            )
            # Index terms in vector database for RAG
            try:
                vector_service.index_company_terms(
                    company_id=company['id'],
                    company_name=request.company_name,
                    terms_text=terms_text
                )
            except Exception as ve:
                print(f"Vector indexing failed: {ve}")
        except Exception as e:
            print(f"Terms analysis failed: {e}")

    # Analyze cookie policy
    if cookie_text:
        try:
            analysis = bedrock_service.analyze_cookie_policy(
                company_name=request.company_name,
                cookie_text=cookie_text
            )
            db_service.update_company_cookie_analysis(
                company_id=company['id'],
                cookie_risks=analysis.get('cookie_risks', []),
                cookie_summary=analysis.get('cookie_summary', '')
            )
        except Exception as e:
            print(f"Cookie analysis failed: {e}")

    # Analyze privacy policy
    if privacy_text:
        try:
            analysis = bedrock_service.analyze_privacy_policy(
                company_name=request.company_name,
                privacy_text=privacy_text
            )
            db_service.update_company_privacy_analysis(
                company_id=company['id'],
                privacy_risks=analysis.get('privacy_risks', []),
                privacy_summary=analysis.get('privacy_summary', '')
            )
        except Exception as e:
            print(f"Privacy analysis failed: {e}")

    return db_service.get_company(company['id'])


@app.post("/api/companies/{company_id}/analyze")
async def analyze_company(company_id: str):
    """Analyze or re-analyze a company's terms"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.get('terms_text'):
        raise HTTPException(status_code=400, detail="No terms text available for analysis")

    try:
        analysis = bedrock_service.analyze_terms_and_conditions(
            company_name=company['name'],
            terms_text=company['terms_text']
        )

        db_service.update_company_analysis(
            company_id=company_id,
            terms_risks=analysis.get('risks', []),
            terms_summary=analysis.get('summary', '')
        )

        # Re-index terms in vector database
        try:
            vector_service.index_company_terms(
                company_id=company_id,
                company_name=company['name'],
                terms_text=company['terms_text']
            )
        except Exception as ve:
            print(f"Vector indexing failed: {ve}")

        return db_service.get_company(company_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/companies/{company_id}/cookie", response_model=CompanyResponse)
async def upload_cookie_policy(company_id: str, request: UploadCookieRequest):
    """Upload cookie policy for a company"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get cookie text - either from direct input or by scraping URL
    cookie_text = request.cookie_text

    if request.cookie_url and not cookie_text:
        try:
            cookie_text = scraper_service.fetch_terms_from_url(request.cookie_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not cookie_text:
        raise HTTPException(status_code=400, detail="Either cookie_text or cookie_url is required")

    # Update company with cookie text
    db_service.update_cookie_text(company_id, cookie_text)

    # Analyze cookie policy using Bedrock
    try:
        analysis = bedrock_service.analyze_cookie_policy(
            company_name=company['name'],
            cookie_text=cookie_text
        )

        # Update company with cookie analysis
        db_service.update_company_cookie_analysis(
            company_id=company_id,
            cookie_risks=analysis.get('cookie_risks', []),
            cookie_summary=analysis.get('cookie_summary', '')
        )

        return db_service.get_company(company_id)

    except Exception as e:
        print(f"Cookie analysis failed: {e}")
        return db_service.get_company(company_id)


@app.post("/api/companies/{company_id}/analyze-cookie", response_model=CompanyResponse)
async def analyze_cookie_policy(company_id: str):
    """Analyze or re-analyze a company's cookie policy"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.get('cookie_text'):
        raise HTTPException(status_code=400, detail="No cookie policy text available for analysis")

    try:
        analysis = bedrock_service.analyze_cookie_policy(
            company_name=company['name'],
            cookie_text=company['cookie_text']
        )

        db_service.update_company_cookie_analysis(
            company_id=company_id,
            cookie_risks=analysis.get('cookie_risks', []),
            cookie_summary=analysis.get('cookie_summary', '')
        )

        return db_service.get_company(company_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cookie analysis failed: {str(e)}")


@app.post("/api/companies/{company_id}/privacy", response_model=CompanyResponse)
async def upload_privacy_policy(company_id: str, request: UploadPrivacyRequest):
    """Upload privacy policy for a company"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get privacy text - either from direct input or by scraping URL
    privacy_text = request.privacy_text

    if request.privacy_url and not privacy_text:
        try:
            privacy_text = scraper_service.fetch_terms_from_url(request.privacy_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not privacy_text:
        raise HTTPException(status_code=400, detail="Either privacy_text or privacy_url is required")

    # Update company with privacy text
    db_service.update_privacy_text(company_id, privacy_text)

    # Analyze privacy policy using Bedrock
    try:
        analysis = bedrock_service.analyze_privacy_policy(
            company_name=company['name'],
            privacy_text=privacy_text
        )

        # Update company with privacy analysis
        db_service.update_company_privacy_analysis(
            company_id=company_id,
            privacy_risks=analysis.get('privacy_risks', []),
            privacy_summary=analysis.get('privacy_summary', '')
        )

        return db_service.get_company(company_id)

    except Exception as e:
        print(f"Privacy analysis failed: {e}")
        return db_service.get_company(company_id)


@app.post("/api/companies/{company_id}/analyze-privacy", response_model=CompanyResponse)
async def analyze_privacy_policy(company_id: str):
    """Analyze or re-analyze a company's privacy policy"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.get('privacy_text'):
        raise HTTPException(status_code=400, detail="No privacy policy text available for analysis")

    try:
        analysis = bedrock_service.analyze_privacy_policy(
            company_name=company['name'],
            privacy_text=company['privacy_text']
        )

        db_service.update_company_privacy_analysis(
            company_id=company_id,
            privacy_risks=analysis.get('privacy_risks', []),
            privacy_summary=analysis.get('privacy_summary', '')
        )

        return db_service.get_company(company_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Privacy analysis failed: {str(e)}")


@app.delete("/api/companies/{company_id}")
async def delete_company(company_id: str):
    """Delete a company"""
    # Remove from vector database
    try:
        vector_service.remove_company(company_id)
    except Exception as e:
        print(f"Error removing from vector DB: {e}")

    if db_service.delete_company(company_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Company not found")


@app.post("/api/seed")
async def seed_database():
    """Seed database with sample companies"""
    created = db_service.seed_sample_data()
    return {"status": "seeded", "companies_created": len(created)}


@app.post("/api/seed-with-real-data")
async def seed_with_real_data():
    """Seed database with real data fetched from company websites"""
    companies_to_fetch = [
        {"name": "Facebook", "category": "social", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg"},
        {"name": "LinkedIn", "category": "professional", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"},
        {"name": "TikTok", "category": "social", "icon_url": "https://upload.wikimedia.org/wikipedia/en/a/a9/TikTok_logo.svg"},
        {"name": "Instagram", "category": "social", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png"},
    ]
    
    created_companies = []
    errors = []
    
    for company_info in companies_to_fetch:
        try:
            # Check if company already exists
            existing = [c for c in db_service.get_all_companies() if c.get('name') == company_info['name']]
            if existing:
                continue
                
            # Fetch terms, cookie, and privacy policies
            terms_text = ""
            cookie_text = ""
            privacy_text = ""
            
            try:
                terms_url = scraper_service.get_known_url(company_info['name'].lower(), 'terms')
                if terms_url:
                    terms_text = scraper_service.fetch_terms_from_url(terms_url)
            except Exception as e:
                print(f"Failed to fetch terms for {company_info['name']}: {e}")
                
            try:
                cookie_url = scraper_service.get_known_url(company_info['name'].lower(), 'cookie')
                if cookie_url:
                    cookie_text = scraper_service.fetch_terms_from_url(cookie_url)
            except Exception as e:
                print(f"Failed to fetch cookie policy for {company_info['name']}: {e}")
                
            try:
                privacy_url = scraper_service.get_known_url(company_info['name'].lower(), 'privacy')
                if privacy_url:
                    privacy_text = scraper_service.fetch_terms_from_url(privacy_url)
            except Exception as e:
                print(f"Failed to fetch privacy policy for {company_info['name']}: {e}")
            
            # Create company with fetched data
            company = db_service.create_company(
                name=company_info['name'],
                category=company_info['category'],
                terms_text=terms_text,
                icon_url=company_info['icon_url'],
                cookie_text=cookie_text,
                privacy_text=privacy_text
            )
            
            # Analyze each document type if text was fetched
            if terms_text:
                try:
                    analysis = bedrock_service.analyze_terms_and_conditions(company_info['name'], terms_text)
                    db_service.update_company_analysis(
                        company_id=company['id'],
                        terms_risks=analysis.get('risks', []),
                        terms_summary=analysis.get('summary', '')
                    )
                except Exception as e:
                    print(f"Failed to analyze terms for {company_info['name']}: {e}")
            
            if cookie_text:
                try:
                    analysis = bedrock_service.analyze_cookie_policy(company_info['name'], cookie_text)
                    db_service.update_company_cookie_analysis(
                        company_id=company['id'],
                        cookie_risks=analysis.get('cookie_risks', []),
                        cookie_summary=analysis.get('cookie_summary', '')
                    )
                except Exception as e:
                    print(f"Failed to analyze cookie policy for {company_info['name']}: {e}")
            
            if privacy_text:
                try:
                    analysis = bedrock_service.analyze_privacy_policy(company_info['name'], privacy_text)
                    db_service.update_company_privacy_analysis(
                        company_id=company['id'],
                        privacy_risks=analysis.get('privacy_risks', []),
                        privacy_summary=analysis.get('privacy_summary', '')
                    )
                except Exception as e:
                    print(f"Failed to analyze privacy policy for {company_info['name']}: {e}")
            
            # Index in vector database
            if terms_text:
                try:
                    vector_service.index_company_terms(
                        company_id=company['id'],
                        company_name=company_info['name'],
                        terms_text=terms_text
                    )
                except Exception as e:
                    print(f"Failed to index terms for {company_info['name']}: {e}")
            
            created_companies.append(company)
            
        except Exception as e:
            errors.append(f"{company_info['name']}: {str(e)}")
    
    return {
        "status": "completed",
        "companies_created": len(created_companies),
        "errors": errors
    }


@app.post("/api/migrate-schema")
async def migrate_schema():
    """
    One-time migration: Update schema to new naming convention.
    - Renames 'risks' → 'terms_risks'
    - Renames 'summary' → 'terms_summary'
    - Initializes cookie_* and privacy_* fields if missing
    Safe to run multiple times - only updates what needs updating.
    """
    result = db_service.migrate_schema()
    return {
        "status": "completed",
        "migrated": result['migrated'],
        "skipped": result['skipped'],
        "total": result['total'],
        "errors": result['errors']
    }


@app.post("/api/companies/{company_id}/chat")
async def chat_about_company(company_id: str, request: dict):
    """Chat about a specific company's terms"""
    company = db_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    question = request.get('question', '')
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        response = bedrock_service.chat_about_terms(
            company_name=company['name'],
            terms_text=company.get('terms_text', ''),
            user_question=question
        )
        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/chat")
async def rag_chat(request: dict):
    """
    RAG-powered chat about terms and conditions.
    - If company_id provided: uses full T&C text directly from DynamoDB
    - If no company_id: uses vector search across all companies
    """
    question = request.get('question', '')
    company_id = request.get('company_id')  # Optional - filter to specific company
    conversation_history = request.get('history', [])

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        # If specific company selected, get full T&C from DynamoDB (no vector search)
        if company_id:
            company = db_service.get_company(company_id)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            if not company.get('terms_text'):
                return {
                    "response": "This company doesn't have any terms and conditions text stored.",
                    "sources": []
                }

            # Use full T&C text as context
            chunks = [{
                "text": company['terms_text'],
                "company_id": company_id,
                "company_name": company['name']
            }]
            sources = [{"company_id": company_id, "company_name": company['name']}]

        else:
            # No company filter - use vector search across all companies
            chunks = vector_service.search(
                query=question,
                n_results=5
            )

            if not chunks:
                return {
                    "response": "I don't have any terms and conditions indexed yet. Please add some companies first, or try re-analyzing existing ones.",
                    "sources": []
                }

            # Format sources for frontend
            sources = []
            seen = set()
            for chunk in chunks:
                company_name = chunk.get('company_name')
                if company_name and company_name not in seen:
                    sources.append({
                        "company_id": chunk.get('company_id'),
                        "company_name": company_name
                    })
                    seen.add(company_name)

        # Generate response using RAG
        response = bedrock_service.rag_chat(
            user_question=question,
            context_chunks=chunks,
            conversation_history=conversation_history
        )

        return {
            "response": response,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/index-all")
async def index_all_companies():
    """Index all existing companies in the vector database"""
    companies = db_service.get_all_companies()
    indexed = 0
    errors = []

    for company in companies:
        if company.get('terms_text'):
            try:
                chunks = vector_service.index_company_terms(
                    company_id=company['id'],
                    company_name=company['name'],
                    terms_text=company['terms_text']
                )
                indexed += 1
            except Exception as e:
                errors.append(f"{company['name']}: {str(e)}")

    return {
        "status": "completed",
        "indexed": indexed,
        "total": len(companies),
        "errors": errors
    }


@app.get("/api/vector-stats")
async def get_vector_stats():
    """Get vector database statistics"""
    stats = vector_service.get_stats()
    return stats


@app.post("/api/analyze-all")
async def analyze_all_companies():
    """Analyze all companies that don't have analysis yet"""
    companies = db_service.get_all_companies()
    analyzed = 0
    errors = []
    
    for company in companies:
        try:
            # Analyze terms if missing
            if company.get('terms_text') and not company.get('terms_risks'):
                try:
                    analysis = bedrock_service.analyze_terms_and_conditions(
                        company_name=company['name'],
                        terms_text=company['terms_text']
                    )
                    db_service.update_company_analysis(
                        company_id=company['id'],
                        terms_risks=analysis.get('risks', []),
                        terms_summary=analysis.get('summary', '')
                    )
                    analyzed += 1
                except Exception as e:
                    errors.append(f"{company['name']} terms: {str(e)}")
            
            # Analyze cookie policy if missing
            if company.get('cookie_text') and not company.get('cookie_risks'):
                try:
                    analysis = bedrock_service.analyze_cookie_policy(
                        company_name=company['name'],
                        cookie_text=company['cookie_text']
                    )
                    db_service.update_company_cookie_analysis(
                        company_id=company['id'],
                        cookie_risks=analysis.get('cookie_risks', []),
                        cookie_summary=analysis.get('cookie_summary', '')
                    )
                    analyzed += 1
                except Exception as e:
                    errors.append(f"{company['name']} cookie: {str(e)}")
            
            # Analyze privacy policy if missing
            if company.get('privacy_text') and not company.get('privacy_risks'):
                try:
                    analysis = bedrock_service.analyze_privacy_policy(
                        company_name=company['name'],
                        privacy_text=company['privacy_text']
                    )
                    db_service.update_company_privacy_analysis(
                        company_id=company['id'],
                        privacy_risks=analysis.get('privacy_risks', []),
                        privacy_summary=analysis.get('privacy_summary', '')
                    )
                    analyzed += 1
                except Exception as e:
                    errors.append(f"{company['name']} privacy: {str(e)}")
                    
        except Exception as e:
            errors.append(f"{company['name']}: {str(e)}")
    
    return {
        "status": "completed",
        "companies_analyzed": analyzed,
        "total_companies": len(companies),
        "errors": errors
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
