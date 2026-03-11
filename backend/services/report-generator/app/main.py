from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from shared.llm.gemini_client import GeminiClient
from shared.models import get_engine, get_session_factory, InterviewSession, AssessmentReport
from shared.auth import init_jwt_handler, get_current_user_id
from shared.constants import DIMENSION_LABELS, DIMENSION_WEIGHTS
from .config import settings
app = FastAPI(title='Report Generator', version='1.0.0')
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)
init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)
llm_client = GeminiClient(api_key=settings.gemini_api_key)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ReportGenerationRequest(BaseModel):
    session_id: str

class ReportResponse(BaseModel):
    id: str
    session_id: str
    dimension_details: Dict[str, Any]
    coaching_narrative: str
    strengths: List[str]
    improvement_areas: List[str]
    action_items: List[str]
    readiness_score: Optional[float]

async def generate_coaching_narrative(session: InterviewSession, dimension_scores: Dict[str, float]) -> str:
    prompt = f"You are an expert interview coach. Generate a personalized, encouraging coaching narrative based on this interview performance.\n\n**Session Details**:\n- Interview Type: {session.session_type}\n- Company: {session.company_slug or 'General'}\n- Role: {session.target_role or 'Software Engineer'}\n- Difficulty: {session.difficulty_level}/10\n- Duration: {(session.duration_seconds // 60 if session.duration_seconds else 0)} minutes\n\n**Dimension Scores** (0.0 to 1.0):\n{chr(10).join((f'- {DIMENSION_LABELS[dim]}: {score:.2f}' for dim, score in dimension_scores.items()))}\n\n**Overall Score**: {session.overall_score:.2f}\n\nWrite a warm, constructive 3-paragraph narrative that:\n1. Celebrates their strengths\n2. Identifies 2-3 key growth areas\n3. Provides specific, actionable advice\n\nKeep it motivating and specific to their performance. 250 words max."
    return await llm_client.generate_content(prompt=prompt, model_name='gemini-2.5-flash', temperature=0.7)

def identify_strengths(dimension_scores: Dict[str, float]) -> List[str]:
    strengths = []
    for dim, score in dimension_scores.items():
        if score >= 0.7:
            strengths.append(f"{DIMENSION_LABELS[dim]}: Demonstrated strong {dim.replace('_', ' ')}")
    if not strengths:
        best_dim = max(dimension_scores.items(), key=lambda x: x[1])
        strengths.append(f'{DIMENSION_LABELS[best_dim[0]]}: Your strongest area')
    return strengths[:3]

def identify_improvement_areas(dimension_scores: Dict[str, float]) -> List[str]:
    areas = []
    for dim, score in dimension_scores.items():
        if score < 0.5:
            areas.append(f"{DIMENSION_LABELS[dim]}: Focus on improving {dim.replace('_', ' ')}")
    if not areas:
        worst_dim = min(dimension_scores.items(), key=lambda x: x[1])
        areas.append(f'{DIMENSION_LABELS[worst_dim[0]]}: Minor refinement needed')
    return areas[:3]

def generate_action_items(session_type: str, improvement_areas: List[str]) -> List[str]:
    actions = []
    if 'technical_correctness' in str(improvement_areas).lower():
        actions.append('Practice 5 LeetCode Medium problems focused on your weak algorithm topics')
    if 'communication' in str(improvement_areas).lower():
        actions.append('Record yourself explaining solutions and review for clarity')
    if 'edge_case' in str(improvement_areas).lower():
        actions.append('Create a checklist of common edge cases to review before coding')
    if session_type == 'behavioral':
        actions.append('Prepare 3 STAR stories for each common behavioral question category')
    elif session_type == 'system_design':
        actions.append('Study system design patterns from real companies (e.g., YouTube, Twitter)')
    else:
        actions.append('Complete 2-3 mock interviews with peers this week')
    actions.append('Schedule your next practice session within 48 hours to maintain momentum')
    return actions[:4]

def calculate_readiness_score(session: InterviewSession, dimension_scores: Dict[str, float]) -> float:
    weights = DIMENSION_WEIGHTS.get(session.session_type, DIMENSION_WEIGHTS['mixed'])
    weighted_score = sum((score * weights.get(dim, 0.125) for dim, score in dimension_scores.items()))
    difficulty_factor = 1.0 - (session.difficulty_level - 5) * 0.05
    readiness = weighted_score * difficulty_factor * 100
    return min(100.0, max(0.0, readiness))

@app.post('/generate', response_model=ReportResponse)
async def generate_report(data: ReportGenerationRequest, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == data.session_id, InterviewSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    if session.dimension_scores is None:
        raise HTTPException(status_code=400, detail='Session not completed yet')
    existing_report = db.query(AssessmentReport).filter(AssessmentReport.session_id == data.session_id).first()
    if existing_report:
        return ReportResponse(id=str(existing_report.id), session_id=str(existing_report.session_id), dimension_details=existing_report.dimension_details or {}, coaching_narrative=existing_report.coaching_narrative or '', strengths=existing_report.strengths or [], improvement_areas=existing_report.improvement_areas or [], action_items=existing_report.action_items or [], readiness_score=existing_report.readiness_score)
    dimension_scores = session.dimension_scores
    strengths = identify_strengths(dimension_scores)
    improvement_areas = identify_improvement_areas(dimension_scores)
    action_items = generate_action_items(session.session_type, improvement_areas)
    readiness_score = calculate_readiness_score(session, dimension_scores)
    narrative = await generate_coaching_narrative(session, dimension_scores)
    report = AssessmentReport(id=uuid.uuid4(), session_id=session.id, user_id=session.user_id, dimension_details=dimension_scores, coaching_narrative=narrative, strengths=strengths, improvement_areas=improvement_areas, action_items=action_items, readiness_score=readiness_score, generation_status='completed', generated_at=datetime.utcnow())
    db.add(report)
    session.status = 'report_ready'
    db.commit()
    db.refresh(report)
    return ReportResponse(id=str(report.id), session_id=str(report.session_id), dimension_details=report.dimension_details or {}, coaching_narrative=report.coaching_narrative or '', strengths=report.strengths or [], improvement_areas=report.improvement_areas or [], action_items=report.action_items or [], readiness_score=report.readiness_score)

@app.get('/report/{session_id}', response_model=ReportResponse)
async def get_report(session_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    report = db.query(AssessmentReport).filter(AssessmentReport.session_id == session_id, AssessmentReport.user_id == user_id).first()
    if not report:
        raise HTTPException(status_code=404, detail='Report not found')
    return ReportResponse(id=str(report.id), session_id=str(report.session_id), dimension_details=report.dimension_details or {}, coaching_narrative=report.coaching_narrative or '', strengths=report.strengths or [], improvement_areas=report.improvement_areas or [], action_items=report.action_items or [], readiness_score=report.readiness_score)

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'report-generator'}
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)