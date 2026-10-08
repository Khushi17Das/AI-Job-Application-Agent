import os
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.models import Resume
from app.utils.helpers import extract_text_from_pdf, extract_text_from_txt

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

def save_and_extract_resume(db: Session, file: UploadFile) -> Resume:
    """Saves uploaded CV file to disk and extracts plain text into database."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF (.pdf) or Text (.txt) file."
        )

    # Generate unique filename to avoid overwrites
    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Extract text based on file type
    if file_ext == ".pdf":
        extracted_text = extract_text_from_pdf(file_path)
    else:
        extracted_text = extract_text_from_txt(file_path)

    if not extracted_text or len(extracted_text.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded document contains insufficient or unreadable text."
        )

    resume_entry = Resume(
        filename=file.filename,
        file_path=file_path,
        extracted_text=extracted_text
    )
    db.add(resume_entry)
    db.commit()
    db.refresh(resume_entry)
    return resume_entry

def get_latest_resume(db: Session) -> Resume:
    """Fetches the most recently uploaded resume from DB."""
    resume = db.query(Resume).order_by(Resume.id.desc()).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_444_RESPONSE_HAS_NO_BODY if hasattr(status, 'HTTP_444_RESPONSE_HAS_NO_BODY') else status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please upload a CV first."
        )
    return resume

def get_resume_by_id(db: Session, resume_id: int) -> Resume:
    """Fetches a specific resume by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )
    return resume
