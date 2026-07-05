# DecisionAI Backend

Autonomous AI Business Analyst — a production-ready FastAPI backend that automatically analyzes business datasets, diagnoses issues, trains ML models, predicts outcomes, and generates executive reports using Google Gemini.

## Architecture

```
backend/
├── app/
│   ├── api/              # FastAPI route handlers (auth, upload, analysis, prediction, chat, reports)
│   ├── auth/             # JWT authentication, password hashing, role-based authorization
│   ├── database/         # SQLAlchemy engine, session, Base
│   ├── models/           # ORM models (users, datasets, analyses, predictions, etc.)
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Gemini service, RAG service, analysis service
│   ├── agents/           # Multi-agent orchestration (Data, Business, ML, Risk, Strategy, Executive)
│   ├── ml/               # AutoML pipeline (regression, classification, time series)
│   ├── reports/          # PDF report generation (ReportLab)
│   ├── prompts/          # System prompt + Gemini prompt templates
│   ├── utils/            # Logging, dataset helpers
│   ├── config/           # Pydantic settings
│   └── main.py           # FastAPI app factory
├── alembic/              # Database migrations
├── tests/                # Unit, integration, and API tests
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Tech Stack

- **Python 3.12** / **FastAPI** / **Pydantic** / **SQLAlchemy** / **Alembic**
- **PostgreSQL** (Supabase)
- **JWT Authentication** with role-based authorization
- **Pandas** / **NumPy** / **Scikit-learn** / **XGBoost** / **LightGBM**
- **Google Gemini API** for natural-language business insights
- **FAISS** for Retrieval-Augmented Generation (RAG)
- **ReportLab** for PDF report generation
- **Plotly** for chart generation

## Quick Start

### Local Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in DATABASE_URL and GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
docker-compose up --build
```

The API is available at `http://localhost:8000` with Swagger docs at `/docs`.

## API Endpoints

All routes are prefixed with `/api/v1`.

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT tokens |
| POST | `/auth/logout` | Logout (client discards token) |
| GET | `/auth/me` | Get current user profile |
| POST | `/auth/refresh` | Refresh access token |

### Dataset
| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload CSV/Excel dataset |
| GET | `/upload/{dataset_id}` | Get dataset metadata |
| DELETE | `/upload/{dataset_id}` | Delete dataset |

### Analysis
| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Full dataset analysis (summary, KPIs, quality/health scores) |
| POST | `/diagnosis` | Business diagnosis (issues, severity, impact) |
| POST | `/root-cause` | Root cause analysis via Gemini |

### Prediction
| Method | Path | Description |
|--------|------|-------------|
| POST | `/predict` | AutoML: train all models, return best + predictions |
| POST | `/simulate` | What-if simulation with Gemini explanation |

### Insights
| Method | Path | Description |
|--------|------|-------------|
| POST | `/recommendations` | AI-generated business recommendations |
| POST | `/summary` | Executive summary for C-suite |
| POST | `/chat` | Conversational AI with RAG context retrieval |

### Reports
| Method | Path | Description |
|--------|------|-------------|
| POST | `/report` | Generate downloadable PDF report |
| GET | `/reports/download/{filename}` | Download a report |
| GET | `/reports` | List all reports |

## Multi-Agent Architecture

DecisionAI orchestrates six specialized agents:

1. **Data Agent** — profiles the dataset, detects feature types and business context
2. **Business Analyst Agent** — computes KPIs, health scores, and detects business issues
3. **ML Engineer Agent** — runs the AutoML pipeline (trains 6+ models, selects the best)
4. **Risk Analyst Agent** — performs root cause analysis using Gemini
5. **Strategy Agent** — generates prioritized business recommendations
6. **Executive Report Agent** — produces C-suite executive summaries

## AutoML Pipeline

The system automatically determines the prediction task (regression, classification, or time series) and trains all of the following models, then selects the best performer:

- Random Forest
- Gradient Boosting
- Decision Tree
- Linear/Logistic Regression
- XGBoost
- LightGBM

## RAG Implementation

Dataset rows are chunked, embedded, and stored in a FAISS index. When a user asks a question, relevant chunks are retrieved and sent to Gemini alongside the dataset summary, KPIs, and ML results — ensuring Gemini never answers without retrieved context.

## Database

PostgreSQL with 9 tables: `users`, `datasets`, `analyses`, `predictions`, `recommendations`, `reports`, `chat_history`, `uploaded_files`, `audit_logs`.

Run migrations:
```bash
alembic upgrade head
```

## Testing

```bash
cd backend
pytest -v
```

Tests cover auth utilities, analysis services, the AutoML pipeline, and API integration.

## Security

- JWT authentication with access + refresh tokens
- bcrypt password hashing
- Role-based authorization (analyst, admin, viewer)
- CORS configuration
- File upload validation (type + size limits)
- Input validation via Pydantic
- Audit logging middleware

## Environment Variables

See `.env.example` for all required configuration. Key variables:

- `DATABASE_URL` — PostgreSQL connection string
- `GEMINI_API_KEY` — Google Gemini API key
- `SECRET_KEY` — JWT signing secret
