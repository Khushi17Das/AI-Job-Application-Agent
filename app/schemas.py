from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# --- Document & Resume Schemas ---
class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str
    text_snippet: str
    total_characters: int


class ResumeResponse(BaseModel):
    id: int
    filename: str
    extracted_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Job Analysis Schemas ---
class JobAnalysisRequest(BaseModel):
    job_description: str = Field(..., min_length=10, description="Raw job description text")


class JobRequirementExtract(BaseModel):
    role: str = Field(default="Not Specified")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)


# --- Match & Skill Gap Schemas ---
class MatchAnalysisRequest(BaseModel):
    job_description: str
    resume_text: Optional[str] = None
    resume_id: Optional[int] = None


class SkillGapAnalysis(BaseModel):
    strong_match: List[str] = Field(default_factory=list)
    partial_match: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)


class MatchAnalysisResponse(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    relevant_experience: List[str] = Field(default_factory=list)
    skill_gap: SkillGapAnalysis


# --- Tailored Answer Schemas ---
class GenerateAnswersRequest(BaseModel):
    job_description: str
    resume_text: Optional[str] = None
    resume_id: Optional[int] = None


class TailoredAnswersResponse(BaseModel):
    why_good_fit: str
    relevant_experience: str
    relevant_project: str
    why_this_role: str
    recruiter_message: str


# --- Claim Verification Schemas ---
class VerifyAnswerRequest(BaseModel):
    answer_text: str
    resume_text: Optional[str] = None
    resume_id: Optional[int] = None
    question_context: Optional[str] = None


class VerifyAnswerResponse(BaseModel):
    verified: bool
    issues: List[str] = Field(default_factory=list)


# --- Application Tracker Schemas ---
class ApplicationCreate(BaseModel):
    company: str
    job_title: str
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    match_score: Optional[int] = None
    status: str = "Saved"
    notes: Optional[str] = None
    date_applied: Optional[str] = None


class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    match_score: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    date_applied: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    company: str
    job_title: str
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    match_score: Optional[int] = None
    status: str
    notes: Optional[str] = None
    date_applied: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_applications: int
    saved: int
    applied: int
    interview: int
    rejected: int
    offer: int
    recent_applications: List[ApplicationResponse] = Field(default_factory=list)
