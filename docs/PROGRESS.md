# Project Progress

## Terms & Conditions Risk Analyzer

### Overview
A RAG-based web application that analyzes Terms and Conditions from major companies and presents privacy risks in a user-friendly interface.

### Tech Stack
- **Backend**: FastAPI (Python)
- **AI/LLM**: AWS Bedrock (Claude 3 Sonnet)
- **Database**: AWS DynamoDB
- **Frontend**: Vanilla HTML/CSS/JavaScript

### Completed Features

#### Backend (2024-11-26)
- [x] FastAPI application structure
- [x] AWS Bedrock integration for T&C analysis
- [x] DynamoDB service for data persistence
- [x] REST API endpoints:
  - GET /api/companies - List all companies
  - GET /api/companies/{id} - Get company details
  - POST /api/companies - Create new company with T&C
  - POST /api/companies/{id}/analyze - Analyze company's T&C
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
| POST | /api/companies | Create company |
| POST | /api/companies/{id}/analyze | Analyze T&C |
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
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   REST API  │  │   Bedrock   │  │  DynamoDB   │    │
│  │  Endpoints  │  │   Service   │  │   Service   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Bedrock  │   │ DynamoDB │   │    S3    │
    │ (Claude) │   │  (Data)  │   │  (Docs)  │
    └──────────┘   └──────────┘   └──────────┘
```

### Next Steps
- [ ] Add more company templates
- [ ] Implement chat feature for Q&A about specific T&C
- [ ] Add user authentication
- [ ] Implement S3 for document storage
- [ ] Add export functionality
