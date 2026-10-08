from sqlalchemy.orm import Session
from app.schemas import VerifyAnswerRequest, VerifyAnswerResponse
from app.services.llm_service import verify_generated_answer
from app.services.resume_service import get_latest_resume, get_resume_by_id

def verify_claim_against_cv(db: Session, request: VerifyAnswerRequest) -> VerifyAnswerResponse:
    """Verifies that an AI-generated answer only makes claims supported by the CV."""
    if request.resume_text and request.resume_text.strip():
        resume_text = request.resume_text.strip()
    elif request.resume_id:
        resume = get_resume_by_id(db, request.resume_id)
        resume_text = resume.extracted_text
    else:
        resume = get_latest_resume(db)
        resume_text = resume.extracted_text

    result = verify_generated_answer(
        answer_text=request.answer_text,
        resume_text=resume_text,
        question_context=request.question_context or ""
    )

    return VerifyAnswerResponse(
        verified=bool(result.get("verified", False)),
        issues=result.get("issues", [])
    )
