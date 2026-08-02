"""Consent-related models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ConsentRecord(BaseModel):
    user_id: str
    scope: str
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ConsentCheckResult(BaseModel):
    allowed: bool
    missing_scopes: list[str] = []
