from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# User Schemas

class UserCreate(BaseModel):
    """Request body for POST /users """
    email: EmailStr
    name: str
    password: str = Field(min_length=8, description="Minimum 8 characters")


class UserResponse(BaseModel):
    """Response for user endpoints """
    id: UUID
    email: EmailStr
    name: str
    created_at: datetime

    class Config:
        from_attributes = True   # allows building from SQLAlchemy ORM objects
        
from task import (
    Document_Verification_Output,
    Financial_Analysis_Output,    
    Investment_Analysis_Output,
    Risk_Assessment_Output,
)

# Analysis Job Schema
class JobSubmitResponse(BaseModel):
    """Response for POST /analyze """
    job_id: UUID
    status: str
    message: str
    filename: str
    query: str
    created_at: datetime


class JobStatusResponse(BaseModel):
    """Response for GET /jobs/{job_id}"""
    job_id: UUID
    user_id: Optional[UUID] = None
    filename: str
    query: str
    status: str                                             # pending / processing / completed / failed
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None        # computed from created_at and completed_at
    # All 4 task outputs 
    verification: Optional[Document_Verification_Output] = None
    financial_analysis: Optional[Financial_Analysis_Output] = None
    investment_analysis: Optional[Investment_Analysis_Output] = None
    risk_assessment: Optional[Risk_Assessment_Output] = None

    error_message: Optional[str] = None                    # populated only on failure

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response for GET /jobs """
    total: int
    jobs: List[JobStatusResponse]



# User with Job History
class UserWithJobsResponse(BaseModel):
    """Response for GET /users/{user_id} """
    id: UUID
    email: EmailStr
    name: str
    created_at: datetime
    total_jobs: int
    jobs: List[JobStatusResponse]

    class Config:
        from_attributes = True