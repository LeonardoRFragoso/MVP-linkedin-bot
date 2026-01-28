"""
FastAPI Application for LinkedIn Bot White Label MVP.
Provides REST API for managing tenants, users, and job applications.

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.database import get_db, init_db, DatabaseManager
from backend.core.models import Tenant, User, JobApplication, QuestionBank
from backend.core.config_service import ConfigService
from backend.core.encryption_service import EncryptionService, get_encryption_service
from backend.api.auth import router as auth_router
from backend.api.user_routes import router as user_router
from backend.api.bot_routes import router as bot_router

# ============================================================================
# Pydantic Schemas
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    database: dict
    timestamp: str
    version: str


class TenantBase(BaseModel):
    name: str
    slug: str


class TenantCreate(TenantBase):
    branding: dict = Field(default_factory=dict)
    features: dict = Field(default_factory=dict)
    settings: dict = Field(default_factory=dict)


class TenantResponse(TenantBase):
    id: str
    branding: dict
    features: dict
    settings: dict
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    personal_info: dict = Field(default_factory=dict)
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    search_preferences: dict = Field(default_factory=dict)


class UserResponse(UserBase):
    id: str
    tenant_id: str
    personal_info: dict
    status: str
    is_admin: bool
    total_applications: int
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserConfigResponse(BaseModel):
    personal_info: dict
    search_preferences: dict
    resume_paths: dict
    ai_config: dict


class JobApplicationResponse(BaseModel):
    id: str
    linkedin_job_id: Optional[str]
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    job_link: Optional[str]
    status: str
    application_type: str
    applied_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    total_applications: int
    successful_applications: int
    failed_applications: int
    companies_applied: int
    last_application_date: Optional[datetime]


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="LinkedIn Bot White Label API",
    description="REST API for managing LinkedIn job application automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(bot_router, prefix="/api/v1")

# ============================================================================
# Startup Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health."""
    db_health = DatabaseManager.health_check()
    
    return HealthResponse(
        status="healthy" if db_health["connected"] else "unhealthy",
        database=db_health,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "LinkedIn Bot White Label API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Tenant Endpoints
# ============================================================================

@app.get("/api/v1/tenants", response_model=List[TenantResponse], tags=["Tenants"])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all tenants."""
    tenants = db.query(Tenant).offset(skip).limit(limit).all()
    return tenants


@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse, tags=["Tenants"])
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Get tenant by ID or slug."""
    tenant = db.query(Tenant).filter(
        (Tenant.id == tenant_id) | (Tenant.slug == tenant_id)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=201, tags=["Tenants"])
async def create_tenant(tenant_data: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant."""
    # Check if slug exists
    existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    tenant = Tenant(
        slug=tenant_data.slug,
        name=tenant_data.name,
        branding=tenant_data.branding,
        features=tenant_data.features,
        settings=tenant_data.settings
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return tenant


# ============================================================================
# User Endpoints
# ============================================================================

@app.get("/api/v1/tenants/{tenant_id}/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    tenant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List users for a tenant."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(
        (Tenant.id == tenant_id) | (Tenant.slug == tenant_id)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    users = db.query(User).filter(User.tenant_id == tenant.id).offset(skip).limit(limit).all()
    return users


@app.get("/api/v1/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.get("/api/v1/users/{user_id}/config", response_model=UserConfigResponse, tags=["Users"])
async def get_user_config(user_id: str, db: Session = Depends(get_db)):
    """Get user configuration (from ConfigService)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Use ConfigService to get full config
    config = ConfigService(tenant_id=user.tenant_id, user_id=user_id)
    
    return UserConfigResponse(
        personal_info=config.get_personal_info().to_dict(),
        search_preferences=config.get_search_preferences().to_dict(),
        resume_paths=config.get_resume_paths(),
        ai_config={
            k: v for k, v in config.get_ai_config().items() 
            if k != 'api_key'  # Don't expose API key
        }
    )


@app.post("/api/v1/tenants/{tenant_id}/users", response_model=UserResponse, status_code=201, tags=["Users"])
async def create_user(
    tenant_id: str,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    # Verify tenant
    tenant = db.query(Tenant).filter(
        (Tenant.id == tenant_id) | (Tenant.slug == tenant_id)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if email exists
    existing = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.email == user_data.email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Encrypt LinkedIn password if provided
    linkedin_credentials = {}
    if user_data.linkedin_email:
        encryption = get_encryption_service()
        linkedin_credentials = {
            "email": user_data.linkedin_email,
            "password": encryption.encrypt(user_data.linkedin_password or "")
        }
    
    user = User(
        tenant_id=tenant.id,
        email=user_data.email,
        personal_info=user_data.personal_info,
        linkedin_credentials=linkedin_credentials,
        search_preferences=user_data.search_preferences
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


# ============================================================================
# Job Application Endpoints
# ============================================================================

@app.get("/api/v1/users/{user_id}/applications", tags=["Applications"])
async def list_applications(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    company: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List job applications for a user with pagination."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(JobApplication).filter(JobApplication.user_id == user_id)
    
    if status:
        query = query.filter(JobApplication.status == status)
    
    if company:
        query = query.filter(JobApplication.company.ilike(f"%{company}%"))
    
    # Count total
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    applications = query.order_by(JobApplication.applied_at.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[app.to_dict() for app in applications],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/v1/users/{user_id}/stats", response_model=StatsResponse, tags=["Applications"])
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Get application statistics for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get stats
    total = db.query(JobApplication).filter(JobApplication.user_id == user_id).count()
    
    successful = db.query(JobApplication).filter(
        JobApplication.user_id == user_id,
        JobApplication.status == "applied"
    ).count()
    
    failed = db.query(JobApplication).filter(
        JobApplication.user_id == user_id,
        JobApplication.status == "failed"
    ).count()
    
    companies = db.query(JobApplication.company).filter(
        JobApplication.user_id == user_id,
        JobApplication.company.isnot(None)
    ).distinct().count()
    
    last_app = db.query(JobApplication).filter(
        JobApplication.user_id == user_id
    ).order_by(JobApplication.applied_at.desc()).first()
    
    return StatsResponse(
        total_applications=total,
        successful_applications=successful,
        failed_applications=failed,
        companies_applied=companies,
        last_application_date=last_app.applied_at if last_app else None
    )


# ============================================================================
# Questions Bank Endpoints
# ============================================================================

@app.get("/api/v1/questions", tags=["Questions"])
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    question_type: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """List questions from the shared questions bank."""
    query = db.query(QuestionBank)
    
    if question_type:
        query = query.filter(QuestionBank.question_type == question_type)
    
    if verified_only:
        query = query.filter(QuestionBank.verified == True)
    
    total = query.count()
    offset = (page - 1) * page_size
    questions = query.order_by(QuestionBank.times_seen.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[q.to_dict() for q in questions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/v1/questions/stats", tags=["Questions"])
async def get_questions_stats(db: Session = Depends(get_db)):
    """Get statistics about the questions bank."""
    total = db.query(QuestionBank).count()
    verified = db.query(QuestionBank).filter(QuestionBank.verified == True).count()
    
    # Count by type
    from sqlalchemy import func
    by_type = db.query(
        QuestionBank.question_type,
        func.count(QuestionBank.id)
    ).group_by(QuestionBank.question_type).all()
    
    return {
        "total_questions": total,
        "verified_questions": verified,
        "unverified_questions": total - verified,
        "by_type": {t: c for t, c in by_type}
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv('DEBUG') == 'true' else "An unexpected error occurred"
        }
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Starting API server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Docs available at: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=debug
    )
