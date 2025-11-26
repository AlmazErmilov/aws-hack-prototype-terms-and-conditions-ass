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


@app.post("/api/companies", response_model=CompanyResponse)
async def create_company(request: UploadTermsRequest):
    """Create a new company and analyze its terms"""
    # Get terms text - either from direct input or by scraping URL
    terms_text = request.terms_text

    if request.terms_url and not terms_text:
        try:
            terms_text = scraper_service.fetch_terms_from_url(request.terms_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not terms_text:
        raise HTTPException(status_code=400, detail="Either terms_text or terms_url is required")

    # Create company entry
    company = db_service.create_company(
        name=request.company_name,
        category=request.category,
        terms_text=terms_text
    )

    # Analyze terms using Bedrock
    try:
        analysis = bedrock_service.analyze_terms_and_conditions(
            company_name=request.company_name,
            terms_text=terms_text
        )

        # Update company with analysis
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

        # Return updated company
        return db_service.get_company(company['id'])

    except Exception as e:
        # Return company without analysis if Bedrock fails
        print(f"Bedrock analysis failed: {e}")
        return company


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

        # Index cookie policy in vector database for RAG
        try:
            vector_service.index_company_cookie(
                company_id=company_id,
                company_name=company['name'],
                cookie_text=cookie_text
            )
        except Exception as ve:
            print(f"Cookie vector indexing failed: {ve}")

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

        # Re-index cookie policy in vector database
        try:
            vector_service.index_company_cookie(
                company_id=company_id,
                company_name=company['name'],
                cookie_text=company['cookie_text']
            )
        except Exception as ve:
            print(f"Cookie vector indexing failed: {ve}")

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

        # Index privacy policy in vector database for RAG
        try:
            vector_service.index_company_privacy(
                company_id=company_id,
                company_name=company['name'],
                privacy_text=privacy_text
            )
        except Exception as ve:
            print(f"Privacy vector indexing failed: {ve}")

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

        # Re-index privacy policy in vector database
        try:
            vector_service.index_company_privacy(
                company_id=company_id,
                company_name=company['name'],
                privacy_text=company['privacy_text']
            )
        except Exception as ve:
            print(f"Privacy vector indexing failed: {ve}")

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
                    "response": "I don't have any policies indexed yet. Please add some companies first, or try re-analyzing existing ones.",
                    "sources": []
                }

            # Format sources for frontend (include policy type)
            sources = []
            seen = set()
            policy_type_labels = {
                "terms": "Terms & Conditions",
                "cookie": "Cookie Policy",
                "privacy": "Privacy Policy"
            }
            for chunk in chunks:
                company_name = chunk.get('company_name')
                policy_type = chunk.get('policy_type', 'terms')
                source_key = f"{company_name}_{policy_type}"
                if company_name and source_key not in seen:
                    sources.append({
                        "company_id": chunk.get('company_id'),
                        "company_name": company_name,
                        "policy_type": policy_type,
                        "policy_label": policy_type_labels.get(policy_type, 'Terms & Conditions')
                    })
                    seen.add(source_key)

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
    """Index all existing companies in the vector database (all policy types)"""
    companies = db_service.get_all_companies()
    indexed_counts = {"terms": 0, "cookie": 0, "privacy": 0}
    errors = []

    for company in companies:
        # Index terms
        if company.get('terms_text'):
            try:
                vector_service.index_company_terms(
                    company_id=company['id'],
                    company_name=company['name'],
                    terms_text=company['terms_text']
                )
                indexed_counts["terms"] += 1
            except Exception as e:
                errors.append(f"{company['name']} (terms): {str(e)}")

        # Index cookie policy
        if company.get('cookie_text'):
            try:
                vector_service.index_company_cookie(
                    company_id=company['id'],
                    company_name=company['name'],
                    cookie_text=company['cookie_text']
                )
                indexed_counts["cookie"] += 1
            except Exception as e:
                errors.append(f"{company['name']} (cookie): {str(e)}")

        # Index privacy policy
        if company.get('privacy_text'):
            try:
                vector_service.index_company_privacy(
                    company_id=company['id'],
                    company_name=company['name'],
                    privacy_text=company['privacy_text']
                )
                indexed_counts["privacy"] += 1
            except Exception as e:
                errors.append(f"{company['name']} (privacy): {str(e)}")

    return {
        "status": "completed",
        "indexed": indexed_counts,
        "total_companies": len(companies),
        "errors": errors
    }


@app.get("/api/vector-stats")
async def get_vector_stats():
    """Get vector database statistics"""
    stats = vector_service.get_stats()
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
