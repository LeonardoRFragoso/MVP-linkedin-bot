"""
User Routes for onboarding and profile management.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import User
from backend.core.encryption_service import get_encryption_service
from backend.api.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

# Data directory for uploads
DATA_DIR = Path(__file__).parent.parent.parent / "backend" / "data"
RESUMES_DIR = DATA_DIR / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)


class UserAnswersRequest(BaseModel):
    answers: dict


class LinkedInCredentialsRequest(BaseModel):
    email: str
    password: str


class OnboardingStatus(BaseModel):
    profile_complete: bool
    resume_uploaded: bool
    questions_answered: bool
    linkedin_configured: bool
    is_complete: bool


@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user resume (PDF)."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique filename
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = RESUMES_DIR / filename
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update user resume config
    resume_config = current_user.resume_config or {}
    resume_config["default"] = str(filepath)
    resume_config["uploaded_at"] = datetime.utcnow().isoformat()
    resume_config["original_name"] = file.filename
    current_user.resume_config = resume_config
    
    db.commit()
    
    return {"message": "Resume uploaded successfully", "filename": filename}


@router.post("/answers")
async def save_user_answers(
    request: UserAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user's answers to common questions."""
    from sqlalchemy.orm.attributes import flag_modified
    
    question_answers = dict(current_user.question_answers or {})
    question_answers.update(request.answers)
    question_answers["updated_at"] = datetime.utcnow().isoformat()
    current_user.question_answers = question_answers
    
    # Flag as modified for SQLAlchemy to detect JSON changes
    flag_modified(current_user, "question_answers")
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Answers saved successfully", "count": len(request.answers)}


@router.post("/linkedin-credentials")
async def save_linkedin_credentials(
    request: LinkedInCredentialsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save LinkedIn credentials (encrypted)."""
    encryption_service = get_encryption_service()
    
    # Encrypt credentials
    linkedin_credentials = {
        "email": request.email,
        "password": encryption_service.encrypt(request.password),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    current_user.linkedin_credentials = linkedin_credentials
    db.commit()
    
    return {"message": "LinkedIn credentials saved successfully"}


@router.get("/onboarding-status", response_model=OnboardingStatus)
async def get_onboarding_status(current_user: User = Depends(get_current_user)):
    """Get user's onboarding completion status."""
    personal_info = current_user.personal_info or {}
    
    profile_complete = bool(
        personal_info.get("first_name") and
        personal_info.get("last_name") and
        personal_info.get("job_title")
    )
    
    resume_uploaded = bool(
        current_user.resume_config and
        current_user.resume_config.get("default")
    )
    
    questions_answered = bool(
        current_user.question_answers and
        len(current_user.question_answers) >= 3
    )
    
    linkedin_configured = bool(
        current_user.linkedin_credentials and
        current_user.linkedin_credentials.get("email") and
        current_user.linkedin_credentials.get("password")
    )
    
    return OnboardingStatus(
        profile_complete=profile_complete,
        resume_uploaded=resume_uploaded,
        questions_answered=questions_answered,
        linkedin_configured=linkedin_configured,
        is_complete=profile_complete and linkedin_configured
    )


@router.get("/answers")
async def get_user_answers(current_user: User = Depends(get_current_user)):
    """Get user's saved answers."""
    return current_user.question_answers or {}


@router.get("/resume")
async def get_resume_info(current_user: User = Depends(get_current_user)):
    """Get user's resume information."""
    resume_config = current_user.resume_config or {}
    return {
        "has_resume": bool(resume_config.get("default")),
        "original_name": resume_config.get("original_name"),
        "uploaded_at": resume_config.get("uploaded_at")
    }
