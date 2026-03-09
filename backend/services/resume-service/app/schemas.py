
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ATSAnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=50)

class KeywordMatch(BaseModel):
    keyword: str
    found: bool
    context: Optional[str] = None  

class ATSAnalyzeResponse(BaseModel):
    match_score: float  
    matched_keywords: List[KeywordMatch]
    missing_keywords: List[str]
    suggestions: List[str]
    category_scores: dict  

class BulletRewriteRequest(BaseModel):
    original_bullet: str = Field(..., min_length=5)
    job_description: str = Field(..., min_length=50)
    tone: str = "professional"  

class BulletRewriteResponse(BaseModel):
    original: str
    rewritten: str
    improvement_notes: str

class ResumeOptimizeRequest(BaseModel):
    resume_version_id: str
    job_description: str = Field(..., min_length=50)

class ResumeOptimizeResponse(BaseModel):
    new_version_id: str
    match_score_before: float
    match_score_after: float
    changes_made: List[str]

class CoverLetterRequest(BaseModel):
    job_description: str = Field(..., min_length=50)
    company_name: str = Field(..., min_length=1)
    hiring_manager: Optional[str] = None
    angle: str = "balanced"  

class CoverLetterResponse(BaseModel):
    cover_letter: str
    word_count: int
    key_points: List[str]

class PrepEvaluateRequest(BaseModel):
    question: str
    answer: str
    job_description: Optional[str] = None
    resume_summary: Optional[str] = None

class PrepEvaluateResponse(BaseModel):
    scores: dict
    star_detected: dict
    tone: str
    hedging_words_found: List[str]
    improvement_tips: List[str]
    improved_answer: str
    overall_score: float

class PrepJdAnalyzeRequest(BaseModel):
    job_description: str
    resume_summary: Optional[str] = None
    practice_types: Optional[List[str]] = None

class PrepQuestion(BaseModel):
    id: str
    text: str
    category: str
    difficulty: str
    tags: List[str]

class PrepRound(BaseModel):
    title: str
    description: str
    questions: List[PrepQuestion]

class PrepJdAnalyzeResponse(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    culture_signals: List[str]
    keyword_gaps: List[str]
    interview_rounds: List[PrepRound] = Field(default_factory=list)

class PrepHistoryRecord(BaseModel):
    id: str
    created_at: str
    answer_text: str
    scores_json: dict
    overall_score: float

class PrepHistoryResponse(BaseModel):
    history: List[PrepHistoryRecord]

class PrepDraftRequest(BaseModel):
    question: str
    job_description: Optional[str] = None
    resume_summary: Optional[str] = None

class PrepDraftResponse(BaseModel):
    draft_text: str

class ExportRequest(BaseModel):
    resume_version_id: str
    template: str = "modern"  
    format: str = "pdf"  

class ExportResponse(BaseModel):
    download_url: str
    file_name: str

class LinkedInOptimizeRequest(BaseModel):
    section: str = Field(..., description="headline | about | experience | skills | projects | open_to_work")
    resume_data: str = Field(..., description="Full text or data of the resume to extract from.")
    target_role: Optional[str] = None
    job_description: Optional[str] = None
    existing_linkedin_text: Optional[str] = None

class LinkedInOptimizeResponse(BaseModel):
    optimized_text: str
    char_count: int
    char_limit: int
    keywords_added: List[str]
    score_before: int
    score_after: int
    tips: List[str]

class LinkedInKeywordMatchRequest(BaseModel):
    resume_skills: List[str]
    jd_keywords: List[str]
    linkedin_skills: Optional[List[str]] = None

class LinkedInKeywordMatchResponse(BaseModel):
    matched: List[str]
    missing_from_resume: List[str]
    missing_from_linkedin: List[str]
    priority_adds: List[str]

class LinkedInFetchRequest(BaseModel):
    url: str = Field(..., description="LinkedIn profile URL to fetch")

class LinkedInFetchResponse(BaseModel):
    profile_text: str
    is_auth_wall: bool