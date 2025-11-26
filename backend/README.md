# Backend - Terms & Conditions Risk Analyzer

FastAPI backend for analyzing Terms and Conditions using AWS Bedrock and OpenSearch Serverless.

## Quick Start

```bash
# From the backend directory
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the backend directory or export these variables:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
AWS_DEFAULT_REGION=us-west-2
```

## Project Structure

```
backend/
├── main.py              # FastAPI app, routes, middleware
├── models.py            # Pydantic models
└── services/
    ├── __init__.py      # Service exports
    ├── bedrock.py       # AWS Bedrock (Claude Sonnet 4, Titan Embeddings)
    ├── dynamodb.py      # DynamoDB CRUD operations
    ├── vector_db.py     # OpenSearch Serverless vector search
    └── scraper.py       # URL scraping for T&C documents
```

## Services

### BedrockService (`services/bedrock.py`)

Handles AI operations using AWS Bedrock:

| Method | Description |
|--------|-------------|
| `analyze_terms_and_conditions()` | Analyze T&C text, returns risks and summary |
| `analyze_cookie_policy()` | Analyze cookie policy, returns cookie_risks and cookie_summary |
| `chat_about_terms()` | Answer questions about specific company's terms |
| `generate_embedding()` | Generate 1536-dim vectors using Titan Embeddings |
| `rag_chat()` | RAG-powered chat with context from vector search |

**Models used:**
- Analysis/Chat: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- Embeddings: `amazon.titan-embed-text-v1`

### DynamoDBService (`services/dynamodb.py`)

Manages company data in DynamoDB:

| Method | Description |
|--------|-------------|
| `get_all_companies()` | List all companies |
| `get_company(id)` | Get single company by ID |
| `create_company()` | Create new company entry |
| `update_company_analysis()` | Update T&C risks and summary |
| `update_cookie_text()` | Update cookie policy text |
| `update_company_cookie_analysis()` | Update cookie risks and summary |
| `delete_company(id)` | Delete company |
| `seed_sample_data()` | Load sample companies |

**Table:** `TermsAndConditions` (auto-created on first use)

### VectorDBService (`services/vector_db.py`)

Manages vector storage in OpenSearch Serverless:

| Method | Description |
|--------|-------------|
| `index_company_terms()` | Chunk and index T&C text |
| `search()` | kNN vector search for relevant chunks |
| `remove_company()` | Remove all chunks for a company |
| `get_stats()` | Get index statistics |

**Config:**
- Collection: `tc-vectors`
- Index: `tc-chunks`
- Chunk size: 1000 chars with 200 char overlap
- Vector dimensions: 1536

### ScraperService (`services/scraper.py`)

Fetches T&C from URLs:

| Method | Description |
|--------|-------------|
| `fetch_terms_from_url()` | Scrape and extract text from URL |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies` | List all companies |
| GET | `/api/companies/{id}` | Get company by ID |
| POST | `/api/companies` | Create company (accepts `terms_text` or `terms_url`) |
| POST | `/api/companies/{id}/analyze` | Re-analyze T&C |
| POST | `/api/companies/{id}/cookie` | Upload cookie policy (accepts `cookie_text` or `cookie_url`) |
| POST | `/api/companies/{id}/analyze-cookie` | Re-analyze cookie policy |
| POST | `/api/companies/{id}/chat` | Chat about specific company |
| POST | `/api/chat` | RAG chat (optional `company_id` filter) |
| POST | `/api/index-all` | Index all companies in vector DB |
| GET | `/api/vector-stats` | Vector database statistics |
| DELETE | `/api/companies/{id}` | Delete company |
| POST | `/api/seed` | Load sample data |

## Pydantic Models

```python
class Risk:
    title: str
    description: str
    severity: str  # "low", "medium", "high"

class Company:
    id: str
    name: str
    category: str  # "social", "dating", "professional", etc.
    icon_url: Optional[str]
    terms_text: Optional[str]
    summary: Optional[str]
    risks: List[Risk]
    # Cookie policy fields
    cookie_text: Optional[str]
    cookie_summary: Optional[str]
    cookie_risks: List[Risk]
    last_updated: Optional[str]

class UploadTermsRequest:
    company_name: str
    category: str
    terms_text: Optional[str]  # Either this...
    terms_url: Optional[str]   # ...or this is required

class UploadCookieRequest:
    cookie_text: Optional[str]  # Either this...
    cookie_url: Optional[str]   # ...or this is required
```

## AWS Resources

| Service | Resource | Region |
|---------|----------|--------|
| DynamoDB | `TermsAndConditions` table | us-west-2 |
| OpenSearch Serverless | `tc-vectors` collection | us-west-2 |
| Bedrock | Claude Sonnet 4, Titan Embeddings | us-west-2 |

## Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": "arn:aws:dynamodb:us-west-2:*:table/TermsAndConditions"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:*"
      ],
      "Resource": "*"
    }
  ]
}
```
