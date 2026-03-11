from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class DimensionScores(BaseModel):
    technical_correctness: float = 0.0
    problem_decomposition: float = 0.0
    communication_clarity: float = 0.0
    handling_ambiguity: float = 0.0
    edge_case_awareness: float = 0.0
    time_management: float = 0.0
    collaborative_signals: float = 0.0
    growth_mindset: float = 0.0

class AssessmentRequest(BaseModel):
    session_id: str
    exchange_number: int
    response_text: str
    question_text: Optional[str] = None
    session_type: str = 'coding'
    provider: Optional[str] = 'openai'

class AssessmentResponse(BaseModel):
    scores: DimensionScores
    confidence: float = 0.0
    feedback: Optional[str] = None

class CoachingHint(BaseModel):
    hint: str
    dimension: str
    priority: str = 'medium'
    timestamp: Optional[datetime] = None

class CoachingHintsRequest(BaseModel):
    scores: Dict[str, float]
    session_type: str
    exchange_number: int
    coaching_mode: str = 'training'

class CoachingHintsResponse(BaseModel):
    hints: List[CoachingHint]

class ReportRequest(BaseModel):
    session_id: str

class ReportResponse(BaseModel):
    id: UUID
    session_id: UUID
    overall_score: Optional[float] = None
    dimension_details: Optional[Dict[str, Any]] = None
    coaching_narrative: Optional[str] = None
    strengths: Optional[List[Dict[str, Any]]] = None
    improvement_areas: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    readiness_score: Optional[float] = None
    generation_status: str
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = Field(..., pattern='^(python|javascript|java|cpp|go|rust)$')
    session_id: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None

class CodeExecutionResponse(BaseModel):
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    test_results: Optional[List[Dict[str, Any]]] = None
    passed: int = 0
    total: int = 0
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    complexity_analysis: Optional[Dict[str, Any]] = None