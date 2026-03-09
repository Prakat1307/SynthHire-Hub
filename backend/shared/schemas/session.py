
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class SessionCreate(BaseModel):
    session_type: str = Field(..., pattern="^(coding|system_design|behavioral|mixed)$")
    persona_type: str = Field(default="kind_mentor")
    coaching_mode: str = Field(default="training", pattern="^(training|simulation)$")
    assessment_mode: str = Field(default="practice", pattern="^(practice|timed_mock|certified)$")
    difficulty_level: int = Field(default=5, ge=1, le=10)
    company_id: Optional[str] = None
    company_slug: Optional[str] = None
    custom_company_name: Optional[str] = None
    resume_text: Optional[str] = None
    target_role: Optional[str] = None
    webcam_enabled: bool = False
    time_limit_minutes: Optional[int] = None

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_type: str
    persona_type: str
    coaching_mode: str
    assessment_mode: str
    difficulty_level: int
    company_slug: Optional[str] = None
    target_role: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    dimension_scores: Optional[Dict[str, float]] = None
    emotional_summary: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int

class SessionStateResponse(BaseModel):
    session_id: str
    status: str
    current_phase: str
    exchange_count: int
    difficulty_level: int
    dimension_scores: Dict[str, float]
    time_elapsed_seconds: Optional[int] = None

class ExchangeRequest(BaseModel):
    text: Optional[str] = None
    audio_base64: Optional[str] = None

class ExchangeResponse(BaseModel):
    exchange_number: int
    response_text: str
    audio_url: Optional[str] = None
    question_type: str
    phase_suggestion: str
    dimension_scores: Optional[Dict[str, float]] = None
    coaching_hints: Optional[List[Dict[str, Any]]] = None

class TemplateCreate(BaseModel):
    role: str
    round_type: str
    experience_level: Optional[str] = None
    persona_type: str = "kind_mentor"
    system_prompt: str
    difficulty_range: Dict[str, int] = {"min": 1, "max": 10}
    duration_minutes: int = 45
    is_public: bool = True

class TemplateResponse(BaseModel):
    id: UUID
    creator_id: Optional[UUID] = None
    role: str
    round_type: str
    experience_level: Optional[str] = None
    persona_type: str
    difficulty_range: Dict[str, int]
    duration_minutes: int
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
