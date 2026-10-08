import os
import json
import logging
from typing import Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger("llm_service")

def get_openai_client():
    """Initializes and returns the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY environment variable is not configured. Please set it in your .env file."
        )
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI Python library is not installed."
        )

def get_model_name() -> str:
    """Returns the configured model name or defaults to gpt-4o-mini."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

def _call_llm_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Helper method to invoke OpenAI API with JSON output mode."""
    client = get_openai_client()
    model = get_model_name()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        # Provide a clear, actionable HTTP exception
        error_msg = str(e)
        if "Incorrect API key" in error_msg or "invalid_api_key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OpenAI API key provided in environment variables."
            )
        elif "quota" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OpenAI API quota exceeded or billing limit reached."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {error_msg}"
            )


def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """Extracts structured requirements from raw job description text."""
    system_prompt = (
        "You are an expert HR analyst and technical recruiter. "
        "Extract structured details from the job description provided. "
        "You MUST return a JSON object with the exact keys:\n"
        "{\n"
        '  "role": "Role title",\n'
        '  "required_skills": ["skill1", "skill2"],\n'
        '  "preferred_skills": ["skill1", "skill2"],\n'
        '  "experience_requirements": ["req1", "req2"],\n'
        '  "responsibilities": ["resp1", "resp2"],\n'
        '  "education_requirements": ["edu1"]\n'
        "}"
    )
    user_prompt = f"Job Description:\n```\n{job_description}\n```"
    return _call_llm_json(system_prompt, user_prompt)


def analyze_candidate_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Compares candidate CV with job description and returns match analysis and skill gap."""
    system_prompt = (
        "You are an AI Job Matching Engine. Compare the candidate's CV with the Job Description.\n"
        "Evaluate matched skills, missing skills, relevant experience, and skill gaps.\n"
        "You MUST return a JSON object with the exact keys:\n"
        "{\n"
        '  "match_score": 82, // Integer between 0 and 100\n'
        '  "matched_skills": ["skill1", "skill2"],\n'
        '  "missing_skills": ["skill1", "skill2"],\n'
        '  "relevant_experience": ["experience point 1", "experience point 2"],\n'
        '  "skill_gap": {\n'
        '    "strong_match": ["skill1", "skill2"],\n'
        '    "partial_match": ["skill with related concept"],\n'
        '    "missing": ["completely missing skill"]\n'
        "  }\n"
        "}"
    )
    user_prompt = f"Candidate CV:\n```\n{resume_text}\n```\n\nJob Description:\n```\n{job_description}\n```"
    return _call_llm_json(system_prompt, user_prompt)


def generate_application_answers(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Generates 5 tailored application responses grounded strictly in the CV."""
    system_prompt = (
        "You are an expert AI Career Coach. Generate tailored application responses for the candidate.\n"
        "STRICT GROUNDING RULES:\n"
        "- Base answers ONLY on actual experience, skills, and projects found in the Candidate CV.\n"
        "- Do NOT invent companies, dates, metrics, certifications, or technologies not in the CV.\n"
        "- Be natural, professional, concise, and compelling.\n"
        "You MUST return a JSON object with the exact keys:\n"
        "{\n"
        '  "why_good_fit": "Clear response explaining fit based on actual skills and experience.",\n'
        '  "relevant_experience": "Overview of relevant experience matching the job requirement.",\n'
        '  "relevant_project": "Description of a specific relevant project from the CV.",\n'
        '  "why_this_role": "Motivated response explaining interest in this specific position.",\n'
        '  "recruiter_message": "Short, professional application email/message for a recruiter."\n'
        "}"
    )
    user_prompt = f"Candidate CV:\n```\n{resume_text}\n```\n\nJob Description:\n```\n{job_description}\n```"
    return _call_llm_json(system_prompt, user_prompt)


def verify_generated_answer(answer_text: str, resume_text: str, question_context: str = "") -> Dict[str, Any]:
    """Verifies that an AI-generated answer contains no unsupported claims relative to the CV."""
    system_prompt = (
        "You are a strict factual claim verification engine.\n"
        "Compare the AI-generated Answer against the candidate's Original CV.\n"
        "Check for:\n"
        "1. Unsupported claims (e.g. scale, metrics, tools, or responsibilities not mentioned in CV).\n"
        "2. Fabricated companies, titles, or dates.\n"
        "3. Exaggerations that go beyond reasonable phrasing of CV facts.\n"
        "You MUST return a JSON object with the exact keys:\n"
        "{\n"
        '  "verified": true, // false if any unsupported claim or exaggeration is found\n'
        '  "issues": ["Issue detail 1", "Issue detail 2"] // empty array if verified=true\n'
        "}"
    )
    user_prompt = (
        f"Original CV:\n```\n{resume_text}\n```\n\n"
        f"Question/Context: {question_context or 'Application Response'}\n\n"
        f"Answer to Verify:\n```\n{answer_text}\n```"
    )
    return _call_llm_json(system_prompt, user_prompt)
