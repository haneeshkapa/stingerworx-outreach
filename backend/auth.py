"""
Authentication and tenant isolation middleware
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_current_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> int:
    """
    Extract tenant ID from request header.
    
    In production, this would verify JWT tokens and extract tenant from claims.
    For MVP, we accept X-Tenant-ID header with default fallback to Stingerworx (ID 1).
    """
    if x_tenant_id:
        try:
            return int(x_tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    return 1

class TenantContext:
    """Stores current request tenant context"""
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
