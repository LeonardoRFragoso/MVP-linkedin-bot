"""
SQLAlchemy models for LinkedIn Bot White Label MVP.
Defines the database schema for multi-tenant support.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .database import Base


# ============================================================================
# Helper for UUID columns (works with both PostgreSQL and SQLite)
# ============================================================================

def get_uuid_column(primary_key: bool = False):
    """Get UUID column that works with both PostgreSQL and SQLite."""
    return Column(
        String(36),
        primary_key=primary_key,
        default=lambda: str(uuid.uuid4())
    )


# ============================================================================
# Tenant Model
# ============================================================================

class Tenant(Base):
    """
    Tenant (organization/company) for multi-tenant support.
    Each tenant can have multiple users.
    """
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Branding configuration (JSON)
    branding = Column(JSON, default=dict)
    # Example: {"logo_url": "", "colors": {"primary": "#0077B5"}, "theme": "light"}
    
    # Feature configuration (JSON)
    features = Column(JSON, default=dict)
    # Example: {"max_users": 10, "ai_enabled": true, "max_applications_per_day": 100}
    
    # General settings (JSON)
    settings = Column(JSON, default=dict)
    # Example: {"timezone": "America/Sao_Paulo", "language": "pt-BR"}
    
    # Billing (optional)
    billing_plan = Column(String(50), default="free")
    billing_status = Column(String(50), default="active")
    stripe_customer_id = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(50), default="active")  # active, suspended, deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, slug={self.slug}, name={self.name})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "branding": self.branding,
            "features": self.features,
            "settings": self.settings,
            "billing_plan": self.billing_plan,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# User Model
# ============================================================================

class User(Base):
    """
    User within a tenant.
    Contains personal info, LinkedIn credentials, and preferences.
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Authentication
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # For app login, not LinkedIn
    
    # Personal info (JSON)
    personal_info = Column(JSON, default=dict)
    # Example: {"first_name": "", "last_name": "", "phone": "", "address": {}}
    
    # LinkedIn credentials (JSON, encrypted)
    linkedin_credentials = Column(JSON, default=dict)
    # Example: {"email": "", "password": "enc:xxx"}
    
    # Search preferences (JSON)
    search_preferences = Column(JSON, default=dict)
    # Example: {"search_terms": [], "location": "", "filters": {}}
    
    # Question answers (JSON)
    question_answers = Column(JSON, default=dict)
    # Example: {"experience_by_technology": {}, "years_of_experience": "5"}
    
    # Resume paths (JSON)
    resume_config = Column(JSON, default=dict)
    # Example: {"default": "", "national": "", "international": ""}
    
    # Bot settings (JSON)
    bot_settings = Column(JSON, default=dict)
    
    # Status
    status = Column(String(50), default="active")  # active, suspended, deleted
    is_admin = Column(Boolean, default=False)
    
    # Stats
    total_applications = Column(Integer, default=0)
    last_application_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    
    # Unique constraint for email within tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
        Index('ix_user_tenant_email', 'tenant_id', 'email'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        result = {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "personal_info": self.personal_info,
            "search_preferences": self.search_preferences,
            "status": self.status,
            "is_admin": self.is_admin,
            "total_applications": self.total_applications,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            result["linkedin_credentials"] = self.linkedin_credentials
            result["question_answers"] = self.question_answers
        
        return result


# ============================================================================
# Job Application Model
# ============================================================================

class JobApplication(Base):
    """
    Record of a job application submitted by the bot.
    """
    __tablename__ = "job_applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # LinkedIn job info
    linkedin_job_id = Column(String(100), nullable=True, index=True)
    title = Column(String(500), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    job_link = Column(Text, nullable=True)
    external_job_link = Column(Text, nullable=True)
    
    # HR/Recruiter info
    hr_name = Column(String(255), nullable=True)
    hr_link = Column(Text, nullable=True)
    
    # Application status
    status = Column(String(50), default="applied")  # applied, failed, skipped, external
    application_type = Column(String(50), default="easy_apply")  # easy_apply, external
    
    # Additional data (JSON)
    job_description = Column(Text, nullable=True)
    questions_answered = Column(JSON, default=list)  # List of Q&A pairs
    extra_data = Column(JSON, default=dict)  # Additional metadata (renamed from 'metadata' - reserved)
    
    # Error info (if failed)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    applied_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_applications")
    
    # Indexes
    __table_args__ = (
        Index('ix_job_app_user_date', 'user_id', 'applied_at'),
        Index('ix_job_app_tenant_date', 'tenant_id', 'applied_at'),
        Index('ix_job_app_company', 'company'),
    )
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, title={self.title}, company={self.company})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "linkedin_job_id": self.linkedin_job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "job_link": self.job_link,
            "external_job_link": self.external_job_link,
            "hr_name": self.hr_name,
            "status": self.status,
            "application_type": self.application_type,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None
        }


# ============================================================================
# Questions Bank Model
# ============================================================================

class QuestionBank(Base):
    """
    Shared bank of application questions and answers.
    Questions are deduplicated by hash and can be shared across users.
    """
    __tablename__ = "questions_bank"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Question identification
    question_hash = Column(String(32), unique=True, nullable=False, index=True)
    
    # Question content
    label = Column(Text, nullable=False)
    normalized_label = Column(Text, nullable=True)
    question_type = Column(String(50), nullable=False)  # text, textarea, select, radio, checkbox
    
    # Default answer
    default_answer = Column(Text, nullable=True)
    
    # Options for select/radio/checkbox
    options = Column(JSON, default=list)
    
    # Statistics
    times_seen = Column(Integer, default=1)
    verified = Column(Boolean, default=False)
    
    # Metadata
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_question_type', 'question_type'),
        Index('ix_question_verified', 'verified'),
    )
    
    def __repr__(self):
        return f"<QuestionBank(hash={self.question_hash}, type={self.question_type})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question_hash": self.question_hash,
            "label": self.label,
            "question_type": self.question_type,
            "default_answer": self.default_answer,
            "options": self.options,
            "times_seen": self.times_seen,
            "verified": self.verified
        }


# ============================================================================
# User Question Answer Model
# ============================================================================

class UserQuestionAnswer(Base):
    """
    User-specific answers to questions.
    Allows each user to have custom answers that override the default.
    """
    __tablename__ = "user_question_answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    question_hash = Column(String(32), nullable=False)
    
    # Custom answer
    custom_answer = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'question_hash', name='uq_user_question'),
        Index('ix_uqa_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<UserQuestionAnswer(user_id={self.user_id}, hash={self.question_hash})>"


# ============================================================================
# Bot Run Log Model
# ============================================================================

class BotRunLog(Base):
    """
    Log of bot execution runs for analytics and debugging.
    """
    __tablename__ = "bot_run_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Run info
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed, stopped
    
    # Statistics
    jobs_found = Column(Integer, default=0)
    jobs_applied = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    jobs_skipped = Column(Integer, default=0)
    
    # Search parameters used
    search_params = Column(JSON, default=dict)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_bot_run_user_date', 'user_id', 'started_at'),
    )
    
    def __repr__(self):
        return f"<BotRunLog(id={self.id}, status={self.status}, applied={self.jobs_applied})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "jobs_found": self.jobs_found,
            "jobs_applied": self.jobs_applied,
            "jobs_failed": self.jobs_failed,
            "jobs_skipped": self.jobs_skipped
        }


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Database Models Test")
    print("=" * 60)
    
    from .database import init_db, engine
    
    print("\nCreating all tables...")
    init_db()
    
    print("\nTables created:")
    for table in Base.metadata.tables:
        print(f"  - {table}")
    
    print("\n✅ Models loaded successfully!")
