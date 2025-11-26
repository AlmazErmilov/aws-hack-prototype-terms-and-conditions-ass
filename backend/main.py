from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import os

from models import Company, CompanyCreate, CompanyResponse, Risk, UploadTermsRequest
from services import BedrockService, DynamoDBService

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
    # Create company entry
    company = db_service.create_company(
        name=request.company_name,
        category=request.category,
        terms_text=request.terms_text
    )

    # Analyze terms using Bedrock
    try:
        analysis = bedrock_service.analyze_terms_and_conditions(
            company_name=request.company_name,
            terms_text=request.terms_text
        )

        # Update company with analysis
        db_service.update_company_analysis(
            company_id=company['id'],
            risks=analysis.get('risks', []),
            summary=analysis.get('summary', '')
        )

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
            risks=analysis.get('risks', []),
            summary=analysis.get('summary', '')
        )

        return db_service.get_company(company_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.delete("/api/companies/{company_id}")
async def delete_company(company_id: str):
    """Delete a company"""
    if db_service.delete_company(company_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Company not found")


@app.post("/api/seed")
async def seed_database():
    """Seed database with sample companies"""
    created = db_service.seed_sample_data()
    return {"status": "seeded", "companies_created": len(created)}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
