# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Terms & Conditions Risk Analyzer - A RAG-based web application that analyzes Terms and Conditions using AWS Bedrock (Claude Sonnet 4) and presents privacy risks. The application uses DynamoDB for storage and OpenSearch Serverless for vector search.

## Development Commands

```bash
# Run the application (from project root)
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative: use the run script
./run.sh

# Install dependencies
pip install -r requirements.txt
```

Access at http://localhost:8000. API docs at http://localhost:8000/docs.

## Architecture

```
backend/
├── main.py              # FastAPI app with all REST endpoints
├── models.py            # Pydantic models (Company, Risk, UploadTermsRequest)
└── services/
    ├── bedrock.py       # AWS Bedrock: T&C analysis, embeddings (Titan), RAG chat
    ├── dynamodb.py      # DynamoDB CRUD operations, table: TermsAndConditions
    ├── vector_db.py     # OpenSearch Serverless: vector indexing and kNN search
    └── scraper.py       # URL scraping for T&C documents

frontend/
├── index.html           # Main page structure
├── styles.css           # Styling
└── app.js               # Frontend logic
```

## Key Services

- **BedrockService**: Uses Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`) for analysis and chat. Uses Amazon Titan Embeddings V1 for 1536-dimensional vectors.
- **DynamoDBService**: Table `TermsAndConditions` with `id` (UUID) as partition key. Stores company metadata, T&C text, risks, and summaries.
- **VectorDBService**: OpenSearch Serverless collection `tc-vectors`, index `tc-chunks`. Text chunked at 1000 chars with 200 char overlap.
- **ScraperService**: Fetches T&C text from URLs using BeautifulSoup.

## AWS Configuration

Region: `us-west-2`. Requires environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if using temporary credentials)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/companies` | GET/POST | List all / Create with analysis (supports URL scraping) |
| `/api/companies/{id}` | GET/DELETE | Get / Delete company |
| `/api/companies/{id}/analyze` | POST | Re-analyze T&C |
| `/api/companies/{id}/cookie` | POST | Upload and analyze cookie policy |
| `/api/companies/{id}/analyze-cookie` | POST | Re-analyze cookie policy |
| `/api/companies/{id}/chat` | POST | Chat about specific company |
| `/api/chat` | POST | RAG chat (optional `company_id` filter) |
| `/api/index-all` | POST | Index all companies in vector DB |
| `/api/vector-stats` | GET | Vector DB statistics |
| `/api/seed` | POST | Load sample data |
| `/api/migrate-risks` | POST | Migrate risks → terms_risks (one-time) |

## Progress Tracking

Development progress is tracked in `docs/PROGRESS.md`. Update this file when making significant changes.
