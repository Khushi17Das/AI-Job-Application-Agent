from app.schemas import JobRequirementExtract
from app.services.llm_service import extract_job_requirements

def analyze_job_description(job_description: str) -> JobRequirementExtract:
    """Processes job description text and returns structured requirements."""
    raw_data = extract_job_requirements(job_description)
    return JobRequirementExtract(
        role=raw_data.get("role", "Not Specified"),
        required_skills=raw_data.get("required_skills", []),
        preferred_skills=raw_data.get("preferred_skills", []),
        experience_requirements=raw_data.get("experience_requirements", []),
        responsibilities=raw_data.get("responsibilities", []),
        education_requirements=raw_data.get("education_requirements", [])
    )
