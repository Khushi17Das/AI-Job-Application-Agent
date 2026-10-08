from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class Resume(Base):
    """Database model for storing candidate CV / resume text and file info."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    """Database model for tracking job applications."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_url = Column(String(500), nullable=True)
    job_description = Column(Text, nullable=True)
    match_score = Column(Integer, nullable=True)
    status = Column(String(50), default="Saved")  # Saved, Applied, Interview, Rejected, Offer
    notes = Column(Text, nullable=True)
    date_applied = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
