from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    JobAnalysisRequest,
    JobRequirementExtract,
    MatchAnalysisRequest,
    MatchAnalysisResponse,
    GenerateAnswersRequest,
    TailoredAnswersResponse,
    VerifyAnswerRequest,
    VerifyAnswerResponse,
)
from app.services.job_service import analyze_job_description
from app.services.matching_service import match_cv_with_job
from app.services.verification_service import verify_claim_against_cv
from app.services.llm_service import generate_application_answers
from app.services.resume_service import get_latest_resume, get_resume_by_id

router = APIRouter(prefix="/api", tags=["AI Analysis & Generation"])


@router.post("/analyze/job", response_model=JobRequirementExtract)
def analyze_job(request: JobAnalysisRequest):
    """
    Extracts structured requirements (required skills, preferred skills, role, experience)
    from a pasted job description text using OpenAI.
    """
    if not request.job_description or not request.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description cannot be empty."
        )
    return analyze_job_description(request.job_description.strip())


@router.post("/analyze/match", response_model=MatchAnalysisResponse)
def analyze_match(request: MatchAnalysisRequest, db: Session = Depends(get_db)):
    """
    Compares the uploaded CV against the provided Job Description.
    Returns match score, matched skills, missing skills, and skill gap breakdown.
    """
    if not request.job_description or not request.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is required for matching."
        )
    return match_cv_with_job(db, request)


@router.post("/generate/answers", response_model=TailoredAnswersResponse)
def generate_answers(request: GenerateAnswersRequest, db: Session = Depends(get_db)):
    """
    Generates 5 tailored job application answers grounded strictly in the candidate's CV:
    1. Why are you a good fit?
    2. Describe your relevant experience.
    3. Describe one relevant project.
    4. Why do you want this role?
    5. Recruiter application message.
    """
    if not request.job_description or not request.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is required to generate answers."
        )

    # Resolve CV text
    if request.resume_text and request.resume_text.strip():
        resume_text = request.resume_text.strip()
    elif request.resume_id:
        resume = get_resume_by_id(db, request.resume_id)
        resume_text = resume.extracted_text
    else:
        resume = get_latest_resume(db)
        resume_text = resume.extracted_text

    raw_answers = generate_application_answers(resume_text, request.job_description.strip())

    return TailoredAnswersResponse(
        why_good_fit=raw_answers.get("why_good_fit", ""),
        relevant_experience=raw_answers.get("relevant_experience", ""),
        relevant_project=raw_answers.get("relevant_project", ""),
        why_this_role=raw_answers.get("why_this_role", ""),
        recruiter_message=raw_answers.get("recruiter_message", "")
    )


@router.post("/verify/answer", response_model=VerifyAnswerResponse)
def verify_answer(request: VerifyAnswerRequest, db: Session = Depends(get_db)):
    """
    Verifies an AI-generated answer against the original CV text to detect
    unsupported claims, exaggerated metrics, or non-existent tools/experience.
    """
    if not request.answer_text or not request.answer_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer text is required for claim verification."
        )
    return verify_claim_against_cv(db, request)
