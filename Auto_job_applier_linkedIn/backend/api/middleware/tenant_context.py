"""
Tenant Context Middleware
Extracts and validates tenant information from requests
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant context from requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from header or subdomain
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            # Try to extract from subdomain
            host = request.headers.get("host", "")
            if "." in host:
                tenant_id = host.split(".")[0]
        
        # Default to 'default' tenant
        if not tenant_id or tenant_id in ["localhost", "127"]:
            tenant_id = "default"
        
        # Store in request state
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response


def get_tenant_id(request: Request) -> str:
    """Get tenant ID from request state."""
    return getattr(request.state, "tenant_id", "default")
