from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ResumeUploadResponse, ResumeResponse
from app.services.resume_service import save_and_extract_resume, get_latest_resume, get_resume_by_id

router = APIRouter(prefix="/api/resume", tags=["Resume Documents"])

@router.post("/upload", response_model=ResumeUploadResponse)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a CV/resume document (PDF or TXT).
    Extracts plain text and stores it in the SQLite database.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )
    
    resume = save_and_extract_resume(db, file)
    snippet = resume.extracted_text[:200] + "..." if len(resume.extracted_text) > 200 else resume.extracted_text
    
    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=resume.filename,
        text_snippet=snippet,
        total_characters=len(resume.extracted_text)
    )

@router.get("/latest", response_model=ResumeResponse)
def fetch_latest_resume(db: Session = Depends(get_db)):
    """Retrieves the most recently uploaded resume."""
    return get_latest_resume(db)

@router.get("/{resume_id}", response_model=ResumeResponse)
def fetch_resume_by_id(resume_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific resume by its ID."""
    return get_resume_by_id(db, resume_id)
