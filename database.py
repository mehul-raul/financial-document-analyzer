from sqlalchemy import Index, create_engine, ForeignKey, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from config import settings


class Base(DeclarativeBase):
    pass

engine = create_engine(settings.DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    jobs = relationship("Analysis_Job", back_populates="user")


class Analysis_Job(Base):
    __tablename__ = "analysis_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # foreign key
    filename = Column(String, nullable=False)
    query = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / processing / completed / failed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)  # set only when job finishes
    verification = Column(JSONB, nullable=True)
    financial_analysis = Column(JSONB, nullable=True)
    investment_analysis = Column(JSONB, nullable=True)
    risk_assessment = Column(JSONB, nullable=True)
    error_message = Column(String, nullable=True)

    user = relationship("Users", back_populates="jobs")


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created")