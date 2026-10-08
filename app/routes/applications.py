from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Application
from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    DashboardStats
)

router = APIRouter(prefix="/api/applications", tags=["Application Tracker"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db)):
    """Creates a new tracked job application entry."""
    app_entry = Application(
        company=app_in.company.strip(),
        job_title=app_in.job_title.strip(),
        job_url=app_in.job_url.strip() if app_in.job_url else None,
        job_description=app_in.job_description.strip() if app_in.job_description else None,
        match_score=app_in.match_score,
        status=app_in.status if app_in.status else "Saved",
        notes=app_in.notes.strip() if app_in.notes else None,
        date_applied=app_in.date_applied.strip() if app_in.date_applied else None
    )
    db.add(app_entry)
    db.commit()
    db.refresh(app_entry)
    return app_entry


@router.get("", response_model=List[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    """Lists all saved job applications, ordered by creation date descending."""
    return db.query(Application).order_by(Application.id.desc()).all()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Returns aggregated summary metrics for the dashboard."""
    apps = db.query(Application).all()
    
    total = len(apps)
    saved = sum(1 for a in apps if a.status.lower() == "saved")
    applied = sum(1 for a in apps if a.status.lower() == "applied")
    interview = sum(1 for a in apps if a.status.lower() == "interview")
    rejected = sum(1 for a in apps if a.status.lower() == "rejected")
    offer = sum(1 for a in apps if a.status.lower() == "offer")

    recent = db.query(Application).order_by(Application.id.desc()).limit(5).all()

    return DashboardStats(
        total_applications=total,
        saved=saved,
        applied=applied,
        interview=interview,
        rejected=rejected,
        offer=offer,
        recent_applications=recent
    )


@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: int, db: Session = Depends(get_db)):
    """Retrieves a single application by ID."""
    app_entry = db.query(Application).filter(Application.id == app_id).first()
    if not app_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{app_id} not found."
        )
    return app_entry


@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: int, app_in: ApplicationUpdate, db: Session = Depends(get_db)):
    """Updates an existing job application."""
    app_entry = db.query(Application).filter(Application.id == app_id).first()
    if not app_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{app_id} not found."
        )

    update_data = app_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(app_entry, field, val)

    db.commit()
    db.refresh(app_entry)
    return app_entry


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    """Deletes a tracked job application."""
    app_entry = db.query(Application).filter(Application.id == app_id).first()
    if not app_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{app_id} not found."
        )
    db.delete(app_entry)
    db.commit()
    return None
