import json
import logging
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uvicorn
from .config import settings
from shared.models.base import get_engine, get_session_factory
from shared.models.tables import CompanyAccount, RoleTemplate, ScoringProfile, CandidateAssignment, AssignmentStatus, ATSIntegration, User
from shared.auth.dependencies import init_jwt_handler, get_current_user_id
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shortlisting-service')
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)
init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)
app = FastAPI(title='SynthHire Shortlisting Service', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://synthhire.me", "https://www.synthhire.me"], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProcessAssignmentRequest(BaseModel):
    assignment_id: str

class ProcessAssignmentResponse(BaseModel):
    assignment_id: str
    previous_status: str
    new_status: str
    auto_shortlisted: bool
    weighted_score: Optional[float] = None
    fit_score: Optional[float] = None

class BatchShortlistRequest(BaseModel):
    assignment_ids: List[str]

class CandidateRankingResponse(BaseModel):
    assignment_id: str
    candidate_name: str
    candidate_email: str
    status: str
    overall_score: float
    weighted_score: float
    fit_score: float
    dimension_scores: dict
    rank: int

async def _trigger_ats_webhook(db: Session, company_id: UUID, event_type: str, payload: dict):
    integrations = db.query(ATSIntegration).filter(ATSIntegration.company_id == company_id, ATSIntegration.is_active == True).all()
    for ats in integrations:
        if not ats.events_enabled or event_type not in ats.events_enabled:
            continue
        if not ats.webhook_url:
            continue
        logger.info(f'Triggering ATS webhook ({ats.provider}) for {event_type}')
        try:
            headers = {'Content-Type': 'application/json'}
            if ats.api_key_encrypted:
                headers['Authorization'] = f'Bearer {ats.api_key_encrypted}'
            async with httpx.AsyncClient() as client:
                await client.post(ats.webhook_url, json=payload, headers=headers, timeout=5.0)
            ats.last_sync_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as e:
            logger.error(f'ATS webhook failed: {e}')
            ats.last_error = str(e)
            db.commit()

def calculate_weighted_score(raw_scores: Dict[str, float], weights: Dict[str, float]) -> float:
    if not weights or not raw_scores:
        return 0.0
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, weight in weights.items():
        if dim in raw_scores:
            weighted_sum += raw_scores[dim] * weight
            total_weight += weight
    if total_weight == 0:
        return 0.0
    if total_weight < 0.99 or total_weight > 1.01:
        weighted_sum = weighted_sum / total_weight
    return round(weighted_sum, 2)

def calculate_fit_score(raw_scores: Dict[str, float], thresholds: Dict[str, float]) -> float:
    if not thresholds or not raw_scores:
        return 1.0
    misses = 0
    total_checks = 0
    for dim, min_req in thresholds.items():
        if dim in raw_scores:
            total_checks += 1
            score_100 = raw_scores[dim] * 100 if raw_scores[dim] <= 1.0 else raw_scores[dim]
            if score_100 < min_req:
                misses += 1
    if total_checks == 0:
        return 1.0
    fit = 1.0 - misses / total_checks
    return max(0.0, round(fit, 2))

@app.post('/assignments/{assignment_id}/process', response_model=ProcessAssignmentResponse)
async def process_assignment(assignment_id: str, background_tasks: BackgroundTasks, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    assignment = db.query(CandidateAssignment).filter(CandidateAssignment.id == UUID(assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail='Assignment not found')
    role = db.query(RoleTemplate).filter(RoleTemplate.id == assignment.role_template_id).first()
    if not role:
        raise HTTPException(status_code=404, detail='Role template not found')
    scoring_profile = None
    if role.scoring_profile_id:
        scoring_profile = db.query(ScoringProfile).filter(ScoringProfile.id == role.scoring_profile_id).first()
    elif role.company_id:
        company = db.query(CompanyAccount).filter(CompanyAccount.id == role.company_id).first()
        if company and company.default_scoring_profile_id:
            scoring_profile = db.query(ScoringProfile).filter(ScoringProfile.id == company.default_scoring_profile_id).first()
    previous_status = assignment.status.value if assignment.status else 'pending'
    raw_scores = assignment.dimension_scores or {}
    weighted_score = None
    fit_score = None
    if scoring_profile and raw_scores:
        weighted_score = calculate_weighted_score(raw_scores, scoring_profile.weights)
        fit_score = calculate_fit_score(raw_scores, scoring_profile.thresholds)
        if weighted_score <= 1.0:
            weighted_score *= 100
        try:
            async with httpx.AsyncClient() as client:
                match_res = await client.post('http://matching-service:8015/match', json={'candidate_id': str(assignment.candidate_id), 'role_id': str(role.id)}, timeout=5.0)
                if match_res.status_code == 200:
                    m_data = match_res.json()
                    ai_fit_score = m_data.get('match_score', 1.0)
                    fit_score = (fit_score + ai_fit_score) / 2.0
                await client.post('http://matching-service:8015/trust-signals', json={'user_id': str(assignment.candidate_id), 'session_id': str(assignment.session_id) if assignment.session_id else None, 'signal_type': 'resume_vs_performance'}, timeout=2.0)
        except Exception as e:
            logger.error(f'Matching service integration failed: {e}')
        assignment.weighted_score = weighted_score
        assignment.fit_score = fit_score
    auto_shortlisted = False
    new_status = assignment.status.value if assignment.status else 'assessed'
    if new_status in ('pending', 'assessed') and role.auto_shortlist_enabled:
        threshold = role.auto_shortlist_threshold or (scoring_profile.pass_threshold if scoring_profile else 70.0)
        metric = assignment.weighted_score if assignment.weighted_score is not None else assignment.overall_score or 0.0
        passed_strict_rules = True
        if role.auto_shortlist_rules:
            for dim, min_score in role.auto_shortlist_rules.items():
                dim_score = raw_scores.get(dim, 0)
                dim_score_100 = dim_score * 100 if dim_score <= 1.0 else dim_score
                if dim_score_100 < min_score:
                    passed_strict_rules = False
                    break
        if metric >= threshold and passed_strict_rules and (fit_score >= 1.0):
            new_status = 'shortlisted'
            auto_shortlisted = True
            assignment.decision_at = datetime.now(timezone.utc)
            if role.candidates_shortlisted is not None:
                role.candidates_shortlisted += 1
        elif scoring_profile and metric < scoring_profile.pass_threshold:
            pass
    if assignment.status != AssignmentStatus(new_status) or assignment.status == AssignmentStatus.PENDING:
        assignment.status = AssignmentStatus(new_status)
        assignment.assessed_at = datetime.now(timezone.utc)
        if role.candidates_assessed is not None:
            role.candidates_assessed += 1
    db.commit()
    if role.company_id:
        candidate = db.query(User).filter(User.id == assignment.candidate_id).first()
        payload = {'assignment_id': str(assignment.id), 'candidate_id': str(assignment.candidate_id), 'candidate_email': candidate.email if candidate else '', 'role_id': str(role.id), 'status': new_status, 'overall_score': assignment.overall_score, 'weighted_score': assignment.weighted_score, 'fit_score': assignment.fit_score, 'auto_shortlisted': auto_shortlisted}
        background_tasks.add_task(_trigger_ats_webhook, db, role.company_id, 'candidate_assessed' if not auto_shortlisted else 'candidate_shortlisted', payload)
    return ProcessAssignmentResponse(assignment_id=str(assignment.id), previous_status=previous_status, new_status=new_status, auto_shortlisted=auto_shortlisted, weighted_score=assignment.weighted_score, fit_score=assignment.fit_score)

@app.get('/roles/{role_id}/ranking', response_model=List[CandidateRankingResponse])
async def get_candidate_ranking(role_id: str, limit: int=50, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    role = db.query(RoleTemplate).filter(RoleTemplate.id == UUID(role_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    assignments = db.query(CandidateAssignment).filter(CandidateAssignment.role_template_id == UUID(role_id), CandidateAssignment.status.in_([AssignmentStatus.ASSESSED, AssignmentStatus.SHORTLISTED, AssignmentStatus.PENDING])).all()
    sorted_assignments = sorted(assignments, key=lambda a: (a.status.value == 'shortlisted', a.weighted_score or 0.0, a.fit_score or 0.0, a.overall_score or 0.0), reverse=True)
    results = []
    for i, a in enumerate(sorted_assignments[:limit]):
        candidate = db.query(User).filter(User.id == a.candidate_id).first()
        results.append(CandidateRankingResponse(assignment_id=str(a.id), candidate_name=candidate.full_name if candidate else 'Unknown', candidate_email=candidate.email if candidate else '', status=a.status.value if a.status else 'pending', overall_score=a.overall_score or 0.0, weighted_score=a.weighted_score or 0.0, fit_score=a.fit_score or 0.0, dimension_scores=a.dimension_scores or {}, rank=i + 1))
    return results

@app.post('/batch/shortlist')
async def batch_shortlist(data: BatchShortlistRequest, background_tasks: BackgroundTasks, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    assignments = db.query(CandidateAssignment).filter(CandidateAssignment.id.in_([UUID(id) for id in data.assignment_ids]), CandidateAssignment.status == AssignmentStatus.ASSESSED).all()
    shortlisted_count = 0
    company_payloads = {}
    for a in assignments:
        a.status = AssignmentStatus.SHORTLISTED
        a.decision_at = datetime.now(timezone.utc)
        shortlisted_count += 1
        role = db.query(RoleTemplate).filter(RoleTemplate.id == a.role_template_id).first()
        if role and role.company_id:
            if role.company_id not in company_payloads:
                company_payloads[role.company_id] = []
            company_payloads[role.company_id].append({'assignment_id': str(a.id), 'candidate_id': str(a.candidate_id), 'role_id': str(role.id), 'status': 'shortlisted', 'batch': True})
    db.commit()
    for company_id, payloads in company_payloads.items():
        for payload in payloads:
            background_tasks.add_task(_trigger_ats_webhook, db, company_id, 'candidate_shortlisted', payload)
    return {'status': 'success', 'count': shortlisted_count}

@app.get('/health')
async def health(db: Session=Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text('SELECT 1'))
        return {'status': 'healthy', 'service': settings.service_name}
    except Exception as e:
        return {'status': 'unhealthy', 'service': settings.service_name, 'error': str(e)}
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)
