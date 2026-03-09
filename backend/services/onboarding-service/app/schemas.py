
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ToneEnum(str, Enum):
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    ASSERTIVE = "assertive"
    WARM = "warm"

class LengthEnum(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"

class FormatEnum(str, Enum):
    STAR = "star"
    BULLET_POINTS = "bullet_points"
    FLOWING = "flowing"

class ResumeParseResponse(BaseModel):
    raw_text: str
    parsed: dict  
    resume_version_id: str

class ResumeVersionResponse(BaseModel):
    id: str
    label: str
    is_master: bool
    raw_text: Optional[str] = None
    parsed_json: Optional[dict] = None
    file_name: Optional[str] = None
    match_score: Optional[float] = None
    version_number: int
    created_at: datetime

    class Config:
        from_attributes = True

class JobTargetingRequest(BaseModel):
    target_role: str = Field(..., min_length=1, max_length=100)
    industry: Optional[str] = None
    target_companies: List[str] = Field(default_factory=list)
    years_of_experience: Optional[int] = None
    work_preference: Optional[str] = None  
    experience_level: Optional[str] = None  

class PersonalStoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    situation: str = Field(..., min_length=10)
    task: str = Field(..., min_length=10)
    action: str = Field(..., min_length=10)
    result: str = Field(..., min_length=10)
    tags: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
    role_at_time: Optional[str] = None

class PersonalStoryUpdate(BaseModel):
    title: Optional[str] = None
    situation: Optional[str] = None
    task: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    tags: Optional[List[str]] = None
    company_name: Optional[str] = None
    role_at_time: Optional[str] = None

class PersonalStoryResponse(BaseModel):
    id: str
    title: str
    situation: str
    task: str
    action: str
    result: str
    tags: List[str]
    company_name: Optional[str] = None
    role_at_time: Optional[str] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True

class PreferencesRequest(BaseModel):
    tone: ToneEnum = ToneEnum.CONVERSATIONAL
    answer_length: LengthEnum = LengthEnum.MEDIUM
    answer_format: FormatEnum = FormatEnum.STAR

class PreferencesResponse(BaseModel):
    id: str
    tone: str
    answer_length: str
    answer_format: str
    created_at: datetime

    class Config:
        from_attributes = True

class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    current_step: int  
    resume_uploaded: bool
    job_targeting_done: bool
    stories_count: int
    preferences_set: bool