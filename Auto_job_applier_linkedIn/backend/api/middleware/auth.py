"""
Authentication Middleware
JWT token validation and user authentication
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Validate JWT token and return current user.
    For MVP, this is a simplified implementation.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # TODO: Implement proper JWT validation
    # For now, just check if token exists
    if token:
        return {"token": token, "tenant_id": getattr(request.state, "tenant_id", "default")}
    
    return None


async def require_auth(
    user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """Require authentication for endpoint."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
