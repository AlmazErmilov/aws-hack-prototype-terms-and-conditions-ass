# Terms & Conditions Risk Analyzer

A privacy-focused web application that analyzes Terms and Conditions from major platforms and presents privacy risks in a user-friendly interface. Built with AWS Bedrock (Claude AI) and DynamoDB.

## Overview

Most users never read Terms & Conditions before accepting them. This tool helps users understand what they're agreeing to by:

- Analyzing T&C documents using AI (Claude 3 Haiku via AWS Bedrock)
- Identifying and categorizing privacy risks (High/Medium/Low)
- Presenting findings in an intuitive card-based UI
- Allowing users to add and analyze new company T&Cs

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        Frontend (HTML/JS/CSS)                    │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │   │
│  │  │ Company Cards │  │  Risk Modal   │  │  Upload Form  │       │   │
│  │  │    Grid       │  │   (Popup)     │  │  (Add T&C)    │       │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (Python)                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         REST API Endpoints                       │   │
│  │  GET /api/companies      POST /api/companies                    │   │
│  │  GET /api/companies/{id} POST /api/companies/{id}/analyze       │   │
│  │  DELETE /api/companies   POST /api/seed                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                         │                    │                          │
│              ┌──────────┴──────────┐  ┌─────┴─────┐                    │
│              │                     │  │           │                    │
│              ▼                     ▼  ▼           │                    │
│  ┌─────────────────────┐  ┌─────────────────────┐│                    │
│  │  DynamoDB Service   │  │  Bedrock Service    ││                    │
│  │  - CRUD operations  │  │  - T&C Analysis     ││                    │
│  │  - Data persistence │  │  - Risk extraction  ││                    │
│  └─────────────────────┘  └─────────────────────┘│                    │
└──────────────│────────────────────────│──────────┘
               │                        │
               ▼                        ▼
┌──────────────────────┐  ┌──────────────────────┐
│   AWS DynamoDB       │  │   AWS Bedrock        │
│   ┌──────────────┐   │  │   ┌──────────────┐   │
│   │TermsAnd     │   │  │   │ Claude 3     │   │
│   │Conditions   │   │  │   │ Haiku        │   │
│   │ Table       │   │  │   │              │   │
│   └──────────────┘   │  │   └──────────────┘   │
└──────────────────────┘  └──────────────────────┘
```

## Data Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │    │ Frontend │    │ Backend  │    │   AWS    │
│          │    │          │    │          │    │          │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     │ Click Company │               │               │
     │──────────────>│               │               │
     │               │ GET /api/     │               │
     │               │ companies/{id}│               │
     │               │──────────────>│               │
     │               │               │ Query DynamoDB│
     │               │               │──────────────>│
     │               │               │<──────────────│
     │               │<──────────────│ Company Data  │
     │ Show Modal    │               │               │
     │<──────────────│               │               │
     │               │               │               │
     │ Click Analyze │               │               │
     │──────────────>│               │               │
     │               │ POST /analyze │               │
     │               │──────────────>│               │
     │               │               │ Invoke Bedrock│
     │               │               │──────────────>│
     │               │               │<──────────────│
     │               │               │ AI Analysis   │
     │               │               │               │
     │               │               │ Save to DB    │
     │               │               │──────────────>│
     │               │<──────────────│               │
     │ Show Risks    │               │               │
     │<──────────────│               │               │
     │               │               │               │
```

## Features

| Feature | Description |
|---------|-------------|
| Company Cards | Visual grid of companies with risk indicators |
| Risk Analysis | AI-powered analysis using Claude 3 Haiku |
| Risk Severity | Color-coded risk levels (High/Medium/Low) |
| Add Companies | Upload new T&C for any company |
| Sample Data | Pre-loaded data for Facebook, TikTok, Tinder, X, Instagram, LinkedIn |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 + FastAPI |
| AI/LLM | AWS Bedrock (Claude 3 Haiku) |
| Database | AWS DynamoDB |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Authentication | AWS IAM (Session Token) |

## Prerequisites

- Python 3.9+
- AWS Account with Bedrock and DynamoDB access
- AWS credentials with permissions for:
  - `bedrock:InvokeModel`
  - `dynamodb:*`

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlmazErmilov/aws-hack-prototype-terms-and-conditions-ass.git
   cd aws-hack-prototype-terms-and-conditions-ass
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS credentials**

   Create a `.env` file in the root directory:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
   ```

5. **Run the application**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

## Usage

### Loading Sample Data
Click "Load Sample Data" to populate the database with pre-configured companies.

### Viewing Risks
Click on any company card to view:
- Summary of what users agree to
- List of privacy risks with severity levels
- Detailed descriptions of each risk

### Analyzing T&C
Click "Analyze with AI" to generate or refresh the risk analysis using Claude.

### Adding New Companies
1. Click "+ Add Company"
2. Enter company name and category
3. Paste the Terms & Conditions text
4. Submit to analyze

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/companies` | List all companies |
| `GET` | `/api/companies/{id}` | Get company by ID |
| `POST` | `/api/companies` | Create company + analyze T&C |
| `POST` | `/api/companies/{id}/analyze` | Re-analyze company T&C |
| `DELETE` | `/api/companies/{id}` | Delete company |
| `POST` | `/api/seed` | Load sample data |

### Example Response

```json
{
  "id": "uuid-here",
  "name": "Facebook",
  "category": "social",
  "summary": "Users agree to allow Facebook to collect, share, and commercially exploit their data...",
  "risks": [
    {
      "title": "Extensive Data Collection",
      "description": "Facebook collects information you provide, content you create, and information about your connections.",
      "severity": "high"
    }
  ]
}
```

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI application & routes
│   ├── models.py            # Pydantic data models
│   └── services/
│       ├── __init__.py
│       ├── bedrock.py       # AWS Bedrock integration
│       └── dynamodb.py      # DynamoDB operations
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── styles.css           # CSS styling
│   └── app.js               # Frontend JavaScript
├── docs/
│   └── PROGRESS.md          # Development progress
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
├── run.sh                   # Quick start script
└── README.md
```

## Risk Categories

The AI analyzes T&C documents for these privacy concerns:

| Category | Description |
|----------|-------------|
| Data Collection | What personal data is gathered |
| Data Sharing | Who receives your data |
| User Tracking | How your activity is monitored |
| Content Rights | Licensing of your content |
| Account Termination | Platform's right to remove you |
| Arbitration | Dispute resolution limitations |
| Financial Impact | Hidden costs or implications |

## Sample Companies Included

- **Facebook** - Social media platform
- **TikTok** - Short video platform
- **Tinder** - Dating application
- **X (Twitter)** - Microblogging platform
- **Instagram** - Photo sharing platform
- **LinkedIn** - Professional networking

## Development

### Running in Development Mode
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Access Swagger UI at: `http://localhost:8000/docs`

## License

MIT License

## Acknowledgments

- Built during AWS Hackathon
- Powered by AWS Bedrock and Claude AI
- Privacy awareness inspired by GDPR principles
