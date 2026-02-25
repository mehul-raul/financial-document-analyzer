import config  

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import os
import uuid

from passlib.context import CryptContext
import hashlib
from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import verification, analyze_financial_document, investment_analysis, risk_assessment
from database import get_db, init_db, Users, Analysis_Job, SessionLocal
from schema import (
    UserCreate, UserResponse, UserWithJobsResponse,
    JobSubmitResponse, JobStatusResponse, JobListResponse,
)


# Password hashing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_password(password: str) -> str:
    """
    Pre hashed password with SHA256 to avoid bcrypt 72 byte limit.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    """
    Get final hashed password
    """
    normalized = _normalize_password(password)
    return pwd_context.hash(normalized)


# runs init_db once on start to create tables if they don't exist

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database ready")
    yield
    print("App shutting down.")


# App

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI powered financial document analysis using CrewAI agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_crew(query: str, file_path: str) -> dict:
    """To run the whole crew"""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
    )

    financial_crew.kickoff({'query': query, 'file_path': file_path})

    # Extract every tasks output individually
    task_map = {
        "verification": verification,
        "financial_analysis": analyze_financial_document,
        "investment_analysis": investment_analysis,
        "risk_assessment": risk_assessment,
    }

    outputs = {}
    for key, task in task_map.items():
        try:
            output = task.output
            outputs[key] = (
                output.pydantic.model_dump()
                if output and hasattr(output, "pydantic") and output.pydantic
                else output.raw if output
                else None
            )
        except Exception:
            outputs[key] = None

    return outputs



def process_document_background(job_id: str, query: str, file_path: str):
    """
    Runs after POST /analyze returns.
    Saves all 4 task outputs to DB.

    """
    db = SessionLocal()

    try:
        # Mark job as processing
        job = db.query(Analysis_Job).filter(Analysis_Job.job_id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # Run the full crew
        outputs = run_crew(query=query, file_path=file_path)

        # Save all 4 results and mark completed
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.verification = outputs.get("verification")
        job.financial_analysis = outputs.get("financial_analysis")
        job.investment_analysis = outputs.get("investment_analysis")
        job.risk_assessment = outputs.get("risk_assessment")
        db.commit()

    except Exception as e:
        try:
            job = db.query(Analysis_Job).filter(Analysis_Job.job_id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass

    finally:
        # Always clean up file 
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        db.close()



def build_job_response(job: Analysis_Job) -> JobStatusResponse:
    processing_time = None
    if job.completed_at and job.created_at:
        processing_time = (job.completed_at - job.created_at).total_seconds()

    return JobStatusResponse(
        **{c.name: getattr(job, c.name) for c in job.__table__.columns},
        processing_time_seconds=processing_time,
    )



@app.get("/")
def root():
    return {"message": "Financial Document Analyzer API is running", "version": "1.0.0"}



#user endpoints
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    existing = db.query(Users).filter(Users.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = Users(
        email=user.email,
        name=user.name,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/{user_id}", response_model=UserWithJobsResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get user profile and full job history"""
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    jobs = db.query(Analysis_Job).filter(
        Analysis_Job.user_id == user_id
    ).order_by(Analysis_Job.created_at.desc()).all()

    return UserWithJobsResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        total_jobs=len(jobs),
        jobs=[build_job_response(job) for job in jobs],
    )




@app.post("/analyze", response_model=JobSubmitResponse, status_code=202)
def analyze_document_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    user_id: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Submit a financial document for analysis.
    Returns immediately (202) with a job_id.
    """
    # Save uploaded file with unique name
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    os.makedirs("data", exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    if not query or query.strip() == "":
        query = "Analyze this financial document for investment insights"

    # Validate optional user_id
    parsed_user_id = None
    if user_id:
        try:
            parsed_user_id = UUID(user_id)
            user = db.query(Users).filter(Users.id == parsed_user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")

    # Create job record 
    job = Analysis_Job(
        job_id=uuid.uuid4(),
        user_id=parsed_user_id,
        filename=file.filename,
        query=query.strip(),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        process_document_background,
        job_id=str(job.job_id),
        query=query.strip(),
        file_path=file_path,
    )

    return JobSubmitResponse(
        job_id=job.job_id,
        status=job.status,
        message="Document submitted. Poll GET /jobs/{job_id} for results.",
        filename=file.filename,
        query=query.strip(),
        created_at=job.created_at,
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """Poll for job status and results"""
    job = db.query(Analysis_Job).filter(Analysis_Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response(job)


@app.get("/jobs", response_model=JobListResponse)
def list_jobs(
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all jobs with optional filters.
    GET /jobs
    GET /jobs?status=completed
    GET /jobs?user_id=...&status=completed
    """
    query_filter = db.query(Analysis_Job)

    if user_id:
        query_filter = query_filter.filter(Analysis_Job.user_id == user_id)
    if status:
        query_filter = query_filter.filter(Analysis_Job.status == status)

    jobs = query_filter.order_by(Analysis_Job.created_at.desc()).all()

    return JobListResponse(
        total=len(jobs),
        jobs=[build_job_response(job) for job in jobs],
    )


# Entry point

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)