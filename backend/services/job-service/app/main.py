from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from uuid import UUID
from typing import List, Optional
import httpx
import uvicorn
import datetime

from backend.shared.models.base import Base
from backend.shared.database import SessionLocal, engine
from backend.shared.models.tables import (
    JobListing, JobApplication, JobSource, JobStatus, ApplicationStatus,
    User, RoleTemplate, Certificate, CompanyAccount
)
from backend.shared.schemas.job import (
    JobListingCreate, JobListingUpdate, JobListingResponse,
    JobApplicationCreate, JobApplicationResponse
)
from backend.shared.auth.dependencies import get_current_user_id, init_jwt_handler

from .config import settings

import os
try:
    
    init_jwt_handler("/app/keys/jwt_public.pem", algorithm="RS256")
except Exception as e:
    print(f"Warning: JWT init failed: {e}")

import google.generativeai as genai
import time as _time
import threading

class GeminiKeyRotator:
    def __init__(self):
        self._lock = threading.Lock()
        
        raw_keys = [
            settings.gemini_api_key,
            settings.gemini_api_key_2,
            settings.gemini_api_key_3,
            settings.gemini_api_key_4,
        ]
        self.keys = [k for k in raw_keys if k.strip()]
        self._index = 0
        print(f"[GeminiRotator] Loaded {len(self.keys)} API key(s) into rotation pool")

    def _is_rate_limit_error(self, err: Exception) -> bool:
        s = str(err).lower()
        return any(x in s for x in ('429', 'quota', 'resource_exhausted', 'rate limit', 'rateLimitExceeded'.lower()))

    def generate(self, prompt: str) -> str:

        if not self.keys:
            raise RuntimeError("No Gemini API keys configured")

        models_to_try = [settings.gemini_model]
        for fallback in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_err = None
        
        for model_name in models_to_try:
            
            for attempt in range(len(self.keys)):
                with self._lock:
                    key = self.keys[self._index]
                    key_label = f"Key {self._index + 1}"

                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return response.text.strip()

                except Exception as e:
                    last_err = e
                    if self._is_rate_limit_error(e):
                        with self._lock:
                            old_idx = self._index
                            self._index = (self._index + 1) % len(self.keys)
                            new_label = f"Key {self._index + 1}"
                        print(f"[GeminiRotator] {key_label} on {model_name} rate-limited, rotating to {new_label}")
                        _time.sleep(0.5)  
                    else:
                        raise e  
            
            print(f"[GeminiRotator] All {len(self.keys)} keys exhausted for {model_name}. Falling back to next model...")

        raise last_err

gemini_rotator = GeminiKeyRotator()

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not initialize DB tables on startup: {e}")
    print("Tables may already exist. Continuing...")

app = FastAPI(title="Job Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/jobs/extract-resume")
async def extract_resume_text(file: UploadFile = File(...)):

    import io
    
    contents = await file.read()
    filename = file.filename or "resume"
    
    try:
        if filename.lower().endswith(".pdf"):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            extracted_text = "\n".join(text_parts)
            
            if len(extracted_text.strip()) < 30:
                return {"success": False, "error": "Could not extract readable text from this PDF. It may be image-based. Try a text-based PDF or .txt file.", "text": ""}
            
            print(f"[ResumeExtract] Extracted {len(extracted_text)} chars from PDF ({len(pdf_reader.pages)} pages)")
            return {"success": True, "text": extracted_text.strip(), "pages": len(pdf_reader.pages), "chars": len(extracted_text.strip())}
        
        else:
            
            text = contents.decode("utf-8", errors="ignore")
            if len(text.strip()) < 20:
                return {"success": False, "error": "File appears to be empty or too short.", "text": ""}
            print(f"[ResumeExtract] Read {len(text)} chars from text file")
            return {"success": True, "text": text.strip(), "chars": len(text.strip())}
    
    except Exception as e:
        print(f"[ResumeExtract] Error: {e}")
        return {"success": False, "error": f"Failed to process file: {str(e)}", "text": ""}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "job-service"}

@app.post("/jobs", response_model=JobListingResponse)
def create_job_listing(
    data: JobListingCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user or user.account_type.value != "company":
        raise HTTPException(status_code=403, detail="Only companies can post jobs")
        
    company = db.query(CompanyAccount).join(User).filter(User.id == UUID(user_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    job = JobListing(
        company_id=company.id,
        role_template_id=data.role_template_id,
        title=data.title,
        description=data.description,
        requirements=data.requirements,
        location=data.location,
        is_remote=data.is_remote,
        salary_range=data.salary_range,
        expires_at=data.expires_at,
        status=JobStatus.PUBLISHED,
        published_at=datetime.datetime.utcnow()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job

@app.get("/jobs", response_model=List[JobListingResponse])
async def search_jobs(
    q: Optional[str] = None,
    remote_only: bool = False,
    company_id: Optional[UUID] = None,
    user_id: Optional[str] = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):

    query = db.query(JobListing).filter(JobListing.status == JobStatus.PUBLISHED)
    
    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            JobListing.title.ilike(search),
            JobListing.description.ilike(search)
        ))
        
    if remote_only:
        query = query.filter(JobListing.is_remote == True)
        
    if company_id:
        query = query.filter(JobListing.company_id == company_id)
        
    jobs = query.order_by(desc(JobListing.published_at)).limit(50).all()
    
    match_scores = {}
    if user_id:
        try:
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if user and user.account_type.value == "candidate":
                
                async with httpx.AsyncClient() as client:
                    job_ids = [str(j.id) for j in jobs]
                    payload = {"candidate_id": user_id, "job_ids": job_ids}
                    resp = await client.post(f"{settings.matching_service_url}/match/batch", json=payload, timeout=2.0)
                    if resp.status_code == 200:
                        match_scores = resp.json().get("scores", {})
        except Exception as e:
            
            print(f"Failed to get match scores: {e}")

    result = []
    for job in jobs:
        j_dict = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "location": job.location,
            "is_remote": job.is_remote,
            "salary_range": job.salary_range,
            "external_url": job.external_url,
            "company_id": job.company_id,
            "role_template_id": job.role_template_id,
            "source_id": job.source_id,
            "status": job.status,
            "published_at": job.published_at,
            "expires_at": job.expires_at,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "company_name": job.company.name if job.company else "External Company",
            "match_score": match_scores.get(str(job.id))
        }
        result.append(j_dict)
        
    if match_scores:
        result.sort(key=lambda x: x.get("match_score") or 0.0, reverse=True)
        
    return result

@app.get("/jobs/{job_id}", response_model=JobListingResponse)
def get_job_details(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    j_dict = {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "location": job.location,
        "is_remote": job.is_remote,
        "salary_range": job.salary_range,
        "external_url": job.external_url,
        "company_id": job.company_id,
        "role_template_id": job.role_template_id,
        "source_id": job.source_id,
        "status": job.status,
        "published_at": job.published_at,
        "expires_at": job.expires_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "company_name": job.company.name if job.company else "External Company",
        "match_score": None
    }
    return j_dict

@app.post("/jobs/{job_id}/apply", response_model=JobApplicationResponse)
def apply_to_job(
    job_id: UUID,
    data: JobApplicationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.candidate_id == UUID(user_id)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")
        
    if data.certificate_id:
        cert = db.query(Certificate).filter(
            Certificate.id == data.certificate_id,
            Certificate.user_id == UUID(user_id)
        ).first()
        if not cert:
            raise HTTPException(status_code=400, detail="Invalid certificate")

    app = JobApplication(
        job_id=job_id,
        candidate_id=UUID(user_id),
        certificate_id=data.certificate_id,
        cover_letter=data.cover_letter,
        status=ApplicationStatus.NEW
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)
    
    return {
        **app.__dict__,
        "job_title": job.title,
        "company_name": job.company.name if job.company else "External"
    }

@app.get("/applications/me", response_model=List[JobApplicationResponse])
def get_my_applications(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    apps = db.query(JobApplication).filter(JobApplication.candidate_id == UUID(user_id)).all()
    
    result = []
    for a in apps:
        result.append({
            **a.__dict__,
            "job_title": a.job.title if a.job else "Unknown",
            "company_name": a.job.company.name if a.job and a.job.company else "External"
        })
    return result

from .service import JobAggregationService
from backend.shared.schemas.job import JobSearchQuery

@app.post("/jobs/search/aggregate", response_model=List[dict])
async def aggregate_jobs(
    query: JobSearchQuery,
    db: Session = Depends(get_db)
):

    jobs = await JobAggregationService.fetch_jobs(
        query=query.query,
        location=query.location,
        page=query.page,
        db=db
    )
    
    return [job.dict() for job in jobs]

from pydantic import BaseModel
import google.generativeai as genai
import json

class MatchRequest(BaseModel):
    job_description: str
    job_title: str
    required_skills: List[str] = []
    resume_text: Optional[str] = None  

@app.post("/jobs/calculate-match", response_model=dict)
async def calculate_ai_match(
    request: MatchRequest,
    request_obj: Request = None,
    db: Session = Depends(get_db)
):

    resume_text = None

    if request.resume_text and request.resume_text.strip():
        resume_text = request.resume_text.strip()
        print(f"[MatchEngine] Using resume text from request ({len(resume_text)} chars)")

    if not resume_text:
        try:
            from backend.shared.models.tables import ResumeVersion as Resume
            
            auth_header = request_obj.headers.get("authorization", "") if request_obj else ""
            if auth_header.startswith("Bearer ") and auth_header != "Bearer null":
                token = auth_header.split(" ")[1]
                from backend.shared.auth.dependencies import _decode_token
                try:
                    payload = _decode_token(token)
                    uid = payload.get("sub") or payload.get("user_id")
                    if uid:
                        resume = db.query(Resume).filter(
                            Resume.user_id == UUID(uid),
                            Resume.is_active == True
                        ).first()
                        if not resume:
                            resume = db.query(Resume).filter(Resume.user_id == UUID(uid)).order_by(desc(Resume.created_at)).first()
                        if resume and resume.raw_text:
                            resume_text = resume.raw_text
                            print(f"[MatchEngine] Using resume from DB for user {uid}")
                except Exception as e:
                    print(f"[MatchEngine] Could not decode token for DB resume lookup: {e}")
        except Exception as e:
            print(f"[MatchEngine] DB resume lookup failed: {e}")

    if not resume_text:
        return {"match_score": 0, "details": {"error": "No resume provided. Please upload your resume on the Jobs page to enable AI Match Scoring."}}

    try:
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) evaluator and career advisor.
        Analyze how well the candidate's resume matches the job posting.

        SCORING GUIDELINES:
        - 85-100: Excellent match - candidate has most required skills and relevant experience
        - 70-84: Good match - candidate has many required skills, some gaps can be learned
        - 50-69: Moderate match - candidate has some relevant skills but significant gaps
        - 30-49: Below average - few matching skills but transferable experience exists
        - 0-29: Poor match - very few relevant qualifications

        Be fair and realistic. Even entry-level candidates can score 60%+ if their education and skills align.
        Focus on actual skills, education, experience, and certifications mentioned in the resume.

        CRITICAL: Output strictly VALID JSON ONLY. No markdown, no code blocks, no extra text.
        
        Output format:
        {{ 
            "match_score": <integer 0-100>,
            "key_strength_matches": ["Matched Skill/Experience 1", "Matched Skill/Experience 2", "..."],
            "missing_critical_skills": ["Gap 1", "Gap 2", "..."],
            "brief_summary": "2-3 sentence explanation of the match, highlighting what makes this candidate suitable or what they need to improve"
        }} 
        
        --- JOB POSTING ---
        Title: {request.job_title}
        Required Skills: {', '.join(request.required_skills) if request.required_skills else 'Not specified'}
        Description:
        {request.job_description[:3000]}

        --- CANDIDATE RESUME ---
        {resume_text[:6000]}
        """

        text_resp = gemini_rotator.generate(prompt)
        
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.startswith("```"):
            text_resp = text_resp[3:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        result = json.loads(text_resp.strip())
        
        return {
            "match_score": result.get("match_score", 0),
            "details": {
                "strengths": result.get("key_strength_matches", []),
                "weaknesses": result.get("missing_critical_skills", []),
                "summary": result.get("brief_summary", "")
            }
        }
        
    except Exception as e:
        print(f"[MatchEngine] Match evaluation failed: {e}")
        return {"match_score": 0, "details": {"error": f"AI Engine error: {str(e)}"}}

from backend.shared.schemas.job import ApplicationRequest
from .services.auto_apply import AutoApplyService

@app.post("/jobs/auto-apply", response_model=dict)
async def auto_apply_job(
    request: ApplicationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    from backend.shared.models.tables import ResumeVersion as Resume
    
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == request.job_id,
        JobApplication.user_id == UUID(user_id)
    ).first()
    
    if existing:
        return {"status": "failed", "error": "Already applied to this job."}

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    resume = db.query(Resume).filter(Resume.user_id == UUID(user_id), Resume.is_active == True).first()
    
    user_profile = {
        "name": user.full_name if user else "John Doe",
        "email": user.email if user else "test@example.com",
    }
    
    resume_path = None 

    try:
        
        auto_apply = AutoApplyService(api_key=settings.gemini_api_key)
        results = await auto_apply.execute_apply(
            job_url=request.job_url, 
            user_profile=user_profile, 
            resume_path=resume_path
        )
        
        if results.get("status") == "success":
            app = JobApplication(
                job_id=request.job_id,
                user_id=UUID(user_id),
                status=ApplicationStatus.APPLIED.value
            )
            db.add(app)
            db.commit()
            results["message"] = "Application successfully tracked in database."

        return results

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8016, reload=True)