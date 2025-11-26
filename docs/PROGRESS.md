# Project Progress

## Terms & Conditions Risk Analyzer

### Overview
A RAG-based web application that analyzes Terms and Conditions from major companies and presents privacy risks in a user-friendly interface.

### Tech Stack
- **Backend**: FastAPI (Python)
- **AI/LLM**: AWS Bedrock (Claude Sonnet 4)
- **Embeddings**: Amazon Titan Embeddings V1
- **Database**: AWS DynamoDB
- **Vector Search**: OpenSearch Serverless
- **Frontend**: Vanilla HTML/CSS/JavaScript

### Completed Features

#### Backend (2024-11-26)
- [x] FastAPI application structure
- [x] AWS Bedrock integration for T&C analysis (Claude Sonnet 4)
- [x] DynamoDB service for data persistence
- [x] OpenSearch Serverless for vector storage
- [x] RAG-powered chat functionality
- [x] URL scraping for T&C documents
- [x] REST API endpoints:
  - GET /api/companies - List all companies
  - GET /api/companies/{id} - Get company details
  - POST /api/companies - Create new company with T&C (supports URL scraping)
  - POST /api/companies/{id}/analyze - Analyze company's T&C
  - POST /api/companies/{id}/chat - Chat about specific company
  - POST /api/chat - RAG chat across all companies
  - POST /api/index-all - Index all companies in vector DB
  - GET /api/vector-stats - Get vector database statistics
  - DELETE /api/companies/{id} - Delete company
  - POST /api/seed - Seed sample data

#### Frontend (2024-11-26)
- [x] Company cards grid layout
- [x] Modal popup for company details
- [x] Risk severity indicators (high/medium/low)
- [x] Add company form
- [x] Sample data loading button
- [x] Responsive design

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/companies | Get all companies |
| GET | /api/companies/{id} | Get company by ID |
| POST | /api/companies | Create company (supports URL scraping) |
| POST | /api/companies/{id}/analyze | Analyze T&C |
| POST | /api/companies/{id}/chat | Chat about specific company |
| POST | /api/chat | RAG chat across all companies |
| POST | /api/index-all | Index all companies in vector DB |
| GET | /api/vector-stats | Vector database statistics |
| DELETE | /api/companies/{id} | Delete company |
| POST | /api/seed | Load sample data |

### Sample Companies Included
- Facebook
- TikTok
- Tinder
- X (Twitter)
- Instagram
- LinkedIn

### How to Run

1. Set AWS credentials:
```bash
export AWS_DEFAULT_REGION="us-west-2"
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_SESSION_TOKEN="your_token"
```

2. Run the application:
```bash
chmod +x run.sh
./run.sh
```

3. Open http://localhost:8000 in your browser

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                   │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Company Cards│  │ Risk Modal  │  │  Add Form   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       │
│                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐│
│  │  REST API │ │  Bedrock  │ │ DynamoDB  │ │ Vector  ││
│  │ Endpoints │ │  Service  │ │  Service  │ │   DB    ││
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘│
└─────────────────────────────────────────────────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
┌──────────┐       ┌──────────┐       ┌────────────┐
│ Bedrock  │       │ DynamoDB │       │ OpenSearch │
│(Claude 4)│       │  (Data)  │       │ Serverless │
└──────────┘       └──────────┘       └────────────┘
```

### Next Steps
- [ ] Add more company templates
- [ ] Add user authentication
- [ ] Implement S3 for document storage
- [ ] Add export functionality (PDF/CSV)
- [ ] Add comparison feature between companies
- [ ] Improve chat UI in frontend
