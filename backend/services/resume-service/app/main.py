
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn

from .config import settings
from .database import get_db, create_tables
from .service import ResumeService
from .schemas import (
    ATSAnalyzeRequest, ATSAnalyzeResponse,
    BulletRewriteRequest, BulletRewriteResponse,
    CoverLetterRequest, CoverLetterResponse,
    ResumeOptimizeRequest, ResumeOptimizeResponse,
    PrepEvaluateRequest, PrepEvaluateResponse,
    PrepJdAnalyzeRequest, PrepJdAnalyzeResponse,
    PrepHistoryResponse, PrepDraftRequest, PrepDraftResponse,
    LinkedInOptimizeRequest, LinkedInOptimizeResponse,
    LinkedInKeywordMatchRequest, LinkedInKeywordMatchResponse,
    LinkedInFetchRequest, LinkedInFetchResponse
)
from shared.auth.jwt_handler import JWTHandler

jwt_handler: Optional[JWTHandler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwt_handler
    print(f"Initializing {settings.service_name}...")
    create_tables()
    jwt_handler = JWTHandler(
        public_key_path=settings.jwt_public_key_path,
        private_key_path=settings.jwt_private_key_path,
        algorithm=settings.jwt_algorithm,
    )
    print(f"{settings.service_name} started on port {settings.service_port}")
    yield

app = FastAPI(
    title="SynthHire Resume Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8888"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.replace("Bearer ", "")
    payload = jwt_handler.validate_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload.get("sub") or payload.get("user_id")

def get_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(
        db=db,
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
    )

@app.post("/resume/analyze", response_model=ATSAnalyzeResponse)
async def analyze_ats(
    data: ATSAnalyzeRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.analyze_ats(user_id, data.resume_text, data.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ATS analysis failed: {str(e)}")

@app.post("/resume/rewrite-bullet", response_model=BulletRewriteResponse)
async def rewrite_bullet(
    data: BulletRewriteRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.rewrite_bullet(data.original_bullet, data.job_description, data.tone)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bullet rewrite failed: {str(e)}")

@app.post("/resume/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    data: CoverLetterRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.generate_cover_letter(
            user_id,
            data.job_description,
            data.company_name,
            data.hiring_manager or "Hiring Manager",
            data.angle,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")

@app.post("/resume/optimize", response_model=ResumeOptimizeResponse)
async def optimize_resume(
    data: ResumeOptimizeRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.optimize_resume(user_id, data.resume_version_id, data.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume optimization failed: {str(e)}")

@app.post("/prep/evaluate-answer", response_model=PrepEvaluateResponse)
async def evaluate_prep_answer(
    data: PrepEvaluateRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.evaluate_prep_answer(user_id, data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {str(e)}")

@app.post("/prep/generate-draft", response_model=PrepDraftResponse)
async def generate_prep_draft(
    data: PrepDraftRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.generate_prep_draft(user_id, data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Draft generation failed: {str(e)}")

@app.post("/prep/analyze-jd", response_model=PrepJdAnalyzeResponse)
async def analyze_prep_jd(
    data: PrepJdAnalyzeRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.analyze_prep_jd(user_id, data)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"JD analysis failed: {str(e)}")

@app.get("/prep/history/{question_id}", response_model=PrepHistoryResponse)
async def get_prep_history(
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.get_prep_history(user_id, question_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@app.post("/linkedin/optimize", response_model=LinkedInOptimizeResponse)
async def linkedin_optimize(
    data: LinkedInOptimizeRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.linkedin_optimize(
            section=data.section, 
            resume_data=data.resume_data, 
            target_role=data.target_role, 
            jd=data.job_description, 
            existing=data.existing_linkedin_text
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LinkedIn optimization failed: {str(e)}")

@app.post("/linkedin/keyword-match", response_model=LinkedInKeywordMatchResponse)
async def linkedin_keyword_match(
    data: LinkedInKeywordMatchRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.linkedin_keyword_match(
            resume_skills=data.resume_skills,
            jd_keywords=data.jd_keywords,
            linkedin_skills=data.linkedin_skills
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LinkedIn keyword match failed: {str(e)}")

@app.post("/linkedin/fetch-profile", response_model=LinkedInFetchResponse)
async def linkedin_fetch_profile(
    data: LinkedInFetchRequest,
    user_id: str = Depends(get_current_user_id),
    service: ResumeService = Depends(get_service),
):

    try:
        result = await service.fetch_linkedin_profile(data.url)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LinkedIn fetch failed: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name, "port": settings.service_port}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)