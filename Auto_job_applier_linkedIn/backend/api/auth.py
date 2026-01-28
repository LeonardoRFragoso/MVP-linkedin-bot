"""
Authentication module for LinkedIn Bot White Label.
Handles user registration, login, and JWT token management.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import bcrypt
import jwt

from backend.core.database import get_db
from backend.core.models import User, Tenant

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT Configuration - Use fixed key for development (set JWT_SECRET_KEY in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "linkedin-bot-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    phone_number: Optional[str] = None
    current_city: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    current_city: Optional[str]
    tenant_id: str
    is_admin: bool
    status: str
    total_applications: int
    question_answers: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    current_city: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# ============================================================================
# Helper Functions
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    
    return user


def get_or_create_default_tenant(db: Session) -> Tenant:
    """Get or create default tenant for new users."""
    tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
    if not tenant:
        tenant = Tenant(
            name="Default",
            slug="default",
            branding={},
            features={"max_users": 100, "max_applications_per_day": 50, "ai_enabled": True},
            settings={"timezone": "America/Sao_Paulo", "language": "pt-BR"},
            status="active"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get or create default tenant
    tenant = get_or_create_default_tenant(db)
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        tenant_id=tenant.id,
        email=user_data.email,
        password_hash=hashed_password,
        personal_info={
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "full_name": f"{user_data.first_name} {user_data.last_name}",
            "phone_number": user_data.phone_number or "",
            "current_city": user_data.current_city or "",
        },
        status="active",
        is_admin=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": user.tenant_id}
    )
    
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
        }
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": user.tenant_id}
    )
    
    personal_info = user.personal_info or {}
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "first_name": personal_info.get("first_name", ""),
            "last_name": personal_info.get("last_name", ""),
            "full_name": personal_info.get("full_name", user.email.split("@")[0]),
        }
    )


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    personal_info = current_user.personal_info or {}
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        first_name=personal_info.get("first_name", ""),
        last_name=personal_info.get("last_name", ""),
        full_name=personal_info.get("full_name", current_user.email.split("@")[0]),
        phone_number=personal_info.get("phone_number"),
        current_city=personal_info.get("current_city"),
        tenant_id=current_user.tenant_id,
        is_admin=current_user.is_admin,
        status=current_user.status,
        total_applications=current_user.total_applications,
        question_answers=current_user.question_answers,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserProfile)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    personal_info = current_user.personal_info.copy()
    
    if user_update.first_name:
        personal_info["first_name"] = user_update.first_name
    if user_update.last_name:
        personal_info["last_name"] = user_update.last_name
    if user_update.phone_number is not None:
        personal_info["phone_number"] = user_update.phone_number
    if user_update.current_city is not None:
        personal_info["current_city"] = user_update.current_city
    
    # Update full name
    personal_info["full_name"] = f"{personal_info['first_name']} {personal_info['last_name']}"
    
    current_user.personal_info = personal_info
    db.commit()
    db.refresh(current_user)
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        phone_number=current_user.personal_info.get("phone_number"),
        current_city=current_user.personal_info.get("current_city"),
        tenant_id=current_user.tenant_id,
        is_admin=current_user.is_admin,
        status=current_user.status,
        total_applications=current_user.total_applications,
        created_at=current_user.created_at
    )


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)."""
    return {"message": "Logged out successfully"}
