from sqlalchemy.orm import Session
from app.schemas import MatchAnalysisRequest, MatchAnalysisResponse, SkillGapAnalysis
from app.services.llm_service import analyze_candidate_match
from app.services.resume_service import get_latest_resume, get_resume_by_id

def match_cv_with_job(db: Session, request: MatchAnalysisRequest) -> MatchAnalysisResponse:
    """Matches a CV (by text or ID) against a job description."""
    # Resolve CV text
    if request.resume_text and request.resume_text.strip():
        resume_text = request.resume_text.strip()
    elif request.resume_id:
        resume = get_resume_by_id(db, request.resume_id)
        resume_text = resume.extracted_text
    else:
        # Fallback to latest resume uploaded
        resume = get_latest_resume(db)
        resume_text = resume.extracted_text

    raw_match = analyze_candidate_match(resume_text, request.job_description)

    skill_gap_raw = raw_match.get("skill_gap", {})
    skill_gap = SkillGapAnalysis(
        strong_match=skill_gap_raw.get("strong_match", []),
        partial_match=skill_gap_raw.get("partial_match", []),
        missing=skill_gap_raw.get("missing", [])
    )

    return MatchAnalysisResponse(
        match_score=int(raw_match.get("match_score", 0)),
        matched_skills=raw_match.get("matched_skills", []),
        missing_skills=raw_match.get("missing_skills", []),
        relevant_experience=raw_match.get("relevant_experience", []),
        skill_gap=skill_gap
    )
