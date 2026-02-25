
# Financial Document Analyzer

an AI-powered financial document analysis system built with FastAPI and CrewAI. upload any financial PDF and get back structured analysis from a team of 4 specialized AI agents — document verifier, financial analyst, investment advisor, and risk assessor.

---

## what it does

- upload a financial PDF (earnings report, 10-K, balance sheet, etc.)
- 4 CrewAI agents run sequentially, each with a specific job
- results are stored in PostgreSQL and returned as structured JSON
- non-blocking — submit a document, get a job_id back instantly, poll for results

---

## project structure

```
financial-document-analyzer/
├── main.py           # FastAPI app, endpoints, background worker
├── agents.py         # 4 CrewAI agents with proper roles and goals
├── task.py           # 4 tasks with pydantic output schemas
├── tools.py          # PDF reader tool + search tool
├── database.py       # PostgreSQL setup, ORM models, session management
├── models.py         # Pydantic request/response schemas
├── config.py         # Pydantic settings, loads and validates .env
├── requirements.txt
├── BUG_LOG.md
└── .env              # not committed - create this yourself
```

---

## setup

### 1. clone and create virtual environment
```bash
git clone <repo>
cd financial-document-analyzer
python -m venv venv

# windows
venv\Scripts\activate

# mac/linux
source venv/bin/activate
```

### 2. install dependencies
```bash
pip install -r requirements.txt
```

### 3. create `.env` file
```env
GOOGLE_API_KEY=your_google_api_key_here
SERPER_API_KEY=your_serper_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/financial_analyzer
```

getting API keys:
- `GOOGLE_API_KEY` → https://aistudio.google.com/app/apikey
- `SERPER_API_KEY` → https://serper.dev
- `DATABASE_URL` → your local or hosted PostgreSQL instance

### 4. create the database
```bash
# make sure PostgreSQL is running, then create the database
psql -U postgres -c "CREATE DATABASE financial_analyzer;"
```

tables are created automatically on startup via `init_db()`.

### 5. run the server
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

open http://localhost:8000/docs for the interactive Swagger UI.

---

## sample document for testing

download the Tesla Q2 2025 financial update:
```
https://www.tesla.com/sites/default/files/downloads/TSLA-Q2-2025-Update.pdf
```
upload it through the `/analyze` endpoint to test the full pipeline.

---

## API reference

### health check

```
GET /
```
returns server status.

```json
{
  "message": "Financial Document Analyzer API is running",
  "version": "1.0.0"
}
```

---

### users

#### create user
```
POST /users
```

request body:
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "mypassword123"
}
```

response `201`:
```json
{
  "id": "39112317-f014-4b5e-ad20-354b7d4712af",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2026-02-25T17:33:38.002490+05:30"
}
```

errors:
- `400` — email already registered

---

#### get user + job history
```
GET /users/{user_id}
```

response `200`:
```json
{
  "id": "39112317-...",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "...",
  "total_jobs": 3,
  "jobs": [ ... ]
}
```

errors:
- `404` — user not found

---

### analysis jobs

#### submit document for analysis
```
POST /analyze
```

multipart/form-data:
| field | type | required | description |
|---|---|---|---|
| file | PDF file | yes | financial document to analyze |
| query | string | no | specific question (defaults to general analysis) |
| user_id | UUID string | no | associate job with a user |

response `202` — returns immediately, does not wait for analysis:
```json
{
  "job_id": "f6339536-15b5-452a-9f17-bd36c258fbfa",
  "status": "pending",
  "message": "Document submitted. Poll GET /jobs/{job_id} for results.",
  "filename": "TSLA-Q2-2025-Update.pdf",
  "query": "Analyze revenue trends and key risks",
  "created_at": "2026-02-25T17:35:40.152133+05:30"
}
```

> status `202 Accepted` means the request was received and is being processed. use the `job_id` to poll for results.

---

#### poll job status and results
```
GET /jobs/{job_id}
```

response `200`:

while processing:
```json
{
  "job_id": "f6339536-...",
  "status": "processing",
  "verification": null,
  "financial_analysis": null,
  "investment_analysis": null,
  "risk_assessment": null
}
```

when completed (~60-120 seconds):
```json
{
  "job_id": "f6339536-15b5-452a-9f17-bd36c258fbfa",
  "user_id": "39112317-f014-4b5e-ad20-354b7d4712af",
  "filename": "TSLA-Q2-2025-Update.pdf",
  "query": "Analyze revenue trends and key risks",
  "status": "completed",
  "created_at": "2026-02-25T17:35:40+05:30",
  "completed_at": "2026-02-25T17:37:07+05:30",
  "processing_time_seconds": 87.37,
  "verification": {
    "is_financial_document": true,
    "document_type": "Quarterly Earnings Report",
    "confidence": "high",
    "key_sections_found": ["Revenue", "Balance Sheet", "Cash Flow", "..."],
    "notes": "..."
  },
  "financial_analysis": {
    "summary": "...",
    "key_metrics": ["GAAP operating income: $0.9B", "..."],
    "trends": ["Total revenues decreased 12% YoY", "..."],
    "answer_to_query": "...",
    "data_sources": ["Page 3: Highlights", "..."]
  },
  "investment_analysis": {
    "strengths": ["Strong liquidity with $36.8B cash", "..."],
    "weaknesses": ["Revenue down 12% YoY", "..."],
    "opportunities": ["Robotaxi launch", "..."],
    "key_ratios": ["GAAP Gross Margin: 17.2%", "..."],
    "disclaimer": "This analysis is for informational purposes only..."
  },
  "risk_assessment": {
    "overall_risk_level": "Medium",
    "liquidity_risk": "...",
    "market_risk": "...",
    "operational_risk": "...",
    "key_risk_factors": ["Free cash flow down 89% YoY", "..."],
    "risk_mitigants": ["$36.8B cash reserves", "..."]
  },
  "error_message": null
}
```

if failed:
```json
{
  "status": "failed",
  "error_message": "description of what went wrong"
}
```

errors:
- `404` — job not found

---

#### list all jobs
```
GET /jobs
GET /jobs?status=completed
GET /jobs?user_id=39112317-...
GET /jobs?user_id=39112317-...&status=completed
```

query params:
| param | type | description |
|---|---|---|
| user_id | UUID | filter by user |
| status | string | pending / processing / completed / failed |

response `200`:
```json
{
  "total": 5,
  "jobs": [ ... ]
}
```

---

## agent pipeline

the 4 agents run sequentially, each feeding into the next:

```
1. verifier          → checks if uploaded file is actually a financial document
         ↓
2. financial_analyst → reads document, extracts metrics, answers the query
         ↓
3. investment_advisor → identifies strengths, weaknesses, opportunities, key ratios
         ↓
4. risk_assessor     → evaluates liquidity, market, and operational risk
```

each agent output is typed and validated by a pydantic schema before being saved to the database.

---

## bugs fixed

14 bugs were identified and fixed across all files. here is a summary:

| # | file | type | fix |
|---|---|---|---|
| 1 | agents.py | ImportError | `from crewai import Agent` not `crewai.agents` |
| 2 | tools.py | ImportError | `from crewai_tools import SerperDevTool` not internal submodule |
| 3 | agents.py | NameError | LLM was never initialized, `llm = llm` is meaningless |
| 4 | tools.py | ValidationError | plain class → `@tool` decorator, `Pdf` → `PyPDFLoader` |
| 5 | main.py | Name collision | endpoint function overwrote imported Task object |
| 6 | main.py | Wrong file path | `file_path` never passed into `crew.kickoff()` |
| 7 | main.py | Hardcoded default | removed `"data/sample.pdf"` default, made mandatory |
| 8 | agents.py | Hallucination prompts | rewrote all agent goals and backstories |
| 9 | task.py | Hallucination prompts | rewrote all task descriptions, fixed wrong agent assignments |
| 10 | tools.py | Dead code | removed `InvestmentTool` and `RiskTool` stub classes |
| 11 | main.py | Dead import + incomplete crew | removed `asyncio`, wired all 4 agents and tasks |
| 12 | main.py | bcrypt error | dropped passlib, use bcrypt directly with SHA256 pre-hash |


full details for each issue are in `BUG_LOG.md`.

---

## improvements made

beyond just fixing bugs, a few things were upgraded:

**singleton LLM** — LLM loads once and is shared across all 4 agents instead of initializing 4 separate clients.

**pydantic settings** — replaced scattered `load_dotenv()` calls with a single `config.py` that validates all required env vars at startup and fails immediately if anything is missing.

**pydantic output schemas** — all 4 task outputs are typed and validated, no free-form LLM text blobs.

**async job processing** — POST /analyze returns in under 1 second, crew runs in background, results polled via GET /jobs/{job_id}.

**postgresql integration** — all results stored as JSONB, queryable, with user association and job history.

---

## known limitations

- FastAPI BackgroundTasks runs in the same process — if the server restarts mid-job, that job is lost. for true production use, replace with Celery + Redis.
- no authentication on endpoints — user_id is passed as a form field, not verified via JWT or session token.
- one agent reads the PDF per task — for very large documents this means 4 separate PDF loads. a future improvement would be to read once and pass extracted text as context.

---
