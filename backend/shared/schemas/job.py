from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class JobListingBase(BaseModel):
    title: str
    description: str
    requirements: List[str] = []
    location: Optional[str] = None
    is_remote: bool = False
    salary_range: Optional[str] = None
    external_url: Optional[str] = None

class JobListingCreate(JobListingBase):
    role_template_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None

class JobListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    salary_range: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None

class JobListingResponse(JobListingBase):
    id: UUID
    company_id: Optional[UUID]
    role_template_id: Optional[UUID]
    source_id: Optional[UUID]
    status: str
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None
    match_score: Optional[float] = None

    class Config:
        from_attributes = True

class JobApplicationCreate(BaseModel):
    job_id: UUID
    cover_letter: Optional[str] = None
    certificate_id: Optional[UUID] = None

class JobApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    certificate_id: Optional[UUID]
    status: str
    cover_letter: Optional[str]
    ai_match_score: Optional[float]
    applied_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True

class JobSearchQuery(BaseModel):
    query: str
    location: Optional[str] = None
    remote_only: bool = False
    employment_types: Optional[List[str]] = None
    page: int = 1

class JobPostingItem(BaseModel):
    job_id: str
    source: str
    title: str
    company: str
    company_logo_url: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    required_skills: List[str] = []
    experience_level: Optional[str] = None
    apply_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    match_score: Optional[int] = None
    match_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserJobPreferenceUpdate(BaseModel):
    target_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    remote_preference: Optional[str] = None
    company_sizes: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    daily_apply_limit: Optional[int] = None
    require_review: Optional[bool] = None
    alert_frequency: Optional[str] = None

class ApplicationRequest(BaseModel):
    job_id: str
    job_url: str
    require_manual_review: bool = True