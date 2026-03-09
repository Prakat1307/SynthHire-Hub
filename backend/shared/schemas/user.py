
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserProfileCreate(BaseModel):
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_language: str = "python"
    interview_timeline: Optional[str] = None
    timezone: Optional[str] = None
    self_assessed_weaknesses: List[str] = []
    coaching_mode: str = "training"
    webcam_enabled: bool = False

class UserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_language: str
    interview_timeline: Optional[str] = None
    self_assessed_weaknesses: List[str] = []
    onboarding_completed: bool
    coaching_mode: str
    webcam_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserQuotaResponse(BaseModel):
    user_id: str
    plan: str
    sessions_used: int
    sessions_limit: int
    can_create_session: bool
