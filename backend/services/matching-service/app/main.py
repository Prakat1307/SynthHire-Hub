import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import uvicorn
from .config import settings
from shared.models.base import get_engine, get_session_factory
from shared.models.tables import User, SkillProfile, CandidateRoleFit, RoleTemplate, InitialProfile, TrustSignal, TrustLevel, BiasAuditLog, CandidateAssignment, InterviewSession
from shared.auth.dependencies import init_jwt_handler, get_current_user_id
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('matching-service')
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)
init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)
app = FastAPI(title='SynthHire Matching & Intelligence Service', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://synthhire.me", "https://www.synthhire.me"], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MatchCandidateRequest(BaseModel):
    candidate_id: str
    role_id: str

class MatchCandidateResponse(BaseModel):
    match_score: float
    skill_gaps: List[str]
    strength_highlights: List[str]

class GenerateTrustSignalRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    signal_type: str

class BiasAuditStatsResponse(BaseModel):
    cohort: str
    average_score: float
    pass_rate: float
    total_samples: int

async def _mock_parse_resume(file_bytes: bytes) -> dict:
    return {'years_experience': 4, 'skills': {'React': 'expert', 'TypeScript': 'expert', 'Python': 'intermediate', 'Docker': 'beginner', 'System Design': 'intermediate'}, 'extracted_text_preview': 'Senior Software Engineer with 4 years...', 'education': 'B.S. Computer Science'}

def _calculate_fit(candidate_skills: dict, role_reqs: dict) -> tuple[float, list, list]:
    if not role_reqs:
        return (1.0, [], ['Candidate meets all baseline requirements'])
    score = 0.0
    total = 0.0
    gaps = []
    strengths = []
    level_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
    for skill, req_level in role_reqs.items():
        total += 1
        cand_level_str = candidate_skills.get(skill)
        if cand_level_str:
            c_val = level_map.get(cand_level_str, 1)
            r_val = level_map.get(req_level.lower(), 1) if isinstance(req_level, str) else req_level
            if c_val >= r_val:
                score += 1.0
                if c_val > r_val:
                    strengths.append(f'Exceeds requirement in {skill}')
                else:
                    strengths.append(f'Meets requirement in {skill}')
            else:
                score += c_val / r_val
                gaps.append(f'Needs improvement in {skill} (Has {cand_level_str}, needs {req_level})')
        else:
            gaps.append(f'Missing required skill: {skill}')
    final_score = score / total if total > 0 else 1.0
    return (round(final_score, 2), gaps, strengths)

@app.post('/profiles/{user_id}/parse-resume')
async def parse_and_enrich_resume(user_id: str, file: UploadFile=File(...), db: Session=Depends(get_db)):
    content = await file.read()
    parsed_data = await _mock_parse_resume(content)
    profile = db.query(InitialProfile).filter(InitialProfile.user_id == UUID(user_id)).first()
    if profile:
        profile.resume_text = parsed_data['extracted_text_preview']
        profile.years_experience = parsed_data['years_experience']
        profile.skills = list(parsed_data['skills'].keys())
    else:
        profile = InitialProfile(user_id=UUID(user_id), resume_text=parsed_data['extracted_text_preview'], years_experience=parsed_data['years_experience'], skills=list(parsed_data['skills'].keys()), preferred_roles=['Software Engineer'])
        db.add(profile)
    skill_profile = db.query(SkillProfile).filter(SkillProfile.user_id == UUID(user_id)).first()
    if not skill_profile:
        skill_profile = SkillProfile(user_id=UUID(user_id), skills=parsed_data['skills'], proficiency_levels=parsed_data['skills'])
        db.add(skill_profile)
    db.commit()
    return {'status': 'success', 'parsed_skills': parsed_data['skills']}

@app.post('/match', response_model=MatchCandidateResponse)
async def match_candidate_to_role(data: MatchCandidateRequest, db: Session=Depends(get_db)):
    user_id_uuid = UUID(data.candidate_id)
    role_id_uuid = UUID(data.role_id)
    skill_profile = db.query(SkillProfile).filter(SkillProfile.user_id == user_id_uuid).first()
    role = db.query(RoleTemplate).filter(RoleTemplate.id == role_id_uuid).first()
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    cand_skills = skill_profile.proficiency_levels if skill_profile and skill_profile.proficiency_levels else {}
    mock_role_reqs = {'Python': 'expert', 'React': 'intermediate', 'System Design': 'intermediate'}
    score, gaps, strengths = _calculate_fit(cand_skills, mock_role_reqs)
    fit = db.query(CandidateRoleFit).filter(CandidateRoleFit.candidate_id == user_id_uuid, CandidateRoleFit.role_template_id == role_id_uuid).first()
    if not fit:
        fit = CandidateRoleFit(candidate_id=user_id_uuid, role_template_id=role_id_uuid)
        db.add(fit)
    fit.match_score = score
    fit.skill_gaps = gaps
    fit.strength_highlights = strengths
    fit.is_active = True
    db.commit()
    return MatchCandidateResponse(match_score=score, skill_gaps=gaps, strength_highlights=strengths)

@app.post('/trust-signals', response_model=dict)
async def generate_trust_signal(data: GenerateTrustSignalRequest, db: Session=Depends(get_db)):
    user_id_uuid = UUID(data.user_id)
    session_id_uuid = UUID(data.session_id) if data.session_id else None
    trust_val = TrustLevel.MEDIUM
    conf = 0.5
    details = 'Insufficient data to verify'
    if data.signal_type == 'resume_vs_performance':
        profile = db.query(InitialProfile).filter(InitialProfile.user_id == user_id_uuid).first()
        assignments = db.query(CandidateAssignment).filter(CandidateAssignment.candidate_id == user_id_uuid).all()
        if profile and profile.years_experience and assignments:
            avg_score = sum([a.overall_score for a in assignments if a.overall_score]) / len(assignments)
            if profile.years_experience > 5 and avg_score < 0.4:
                trust_val = TrustLevel.FLAGGED
                conf = 0.8
                details = 'High claimed experience but consistently low performance'
            elif profile.years_experience > 2 and avg_score > 0.7:
                trust_val = TrustLevel.HIGH
                conf = 0.9
                details = 'Performance strongly aligns with claimed experience'
    signal = TrustSignal(user_id=user_id_uuid, session_id=session_id_uuid, signal_type=data.signal_type, trust_level=trust_val, confidence_score=conf, details=details)
    db.add(signal)
    db.commit()
    return {'id': str(signal.id), 'level': trust_val.value, 'details': details}

@app.post('/audit/log')
async def log_bias_audit(company_id: str, role_id: str, cohort_hash: str, score: float, outcome: str, db: Session=Depends(get_db)):
    log = BiasAuditLog(company_id=UUID(company_id), role_template_id=UUID(role_id), demographic_cohort=cohort_hash, overall_score=score, outcome=outcome)
    db.add(log)
    db.commit()
    return {'status': 'logged', 'id': str(log.id)}

@app.get('/audit/stats/{company_id}', response_model=List[BiasAuditStatsResponse])
async def get_audit_stats(company_id: str, role_id: Optional[str]=None, db: Session=Depends(get_db)):
    query = db.query(BiasAuditLog).filter(BiasAuditLog.company_id == UUID(company_id))
    if role_id:
        query = query.filter(BiasAuditLog.role_template_id == UUID(role_id))
    logs = query.all()
    cohort_stats = {}
    for log in logs:
        c = log.demographic_cohort
        if c not in cohort_stats:
            cohort_stats[c] = {'total': 0, 'score_sum': 0, 'passed': 0}
        cohort_stats[c]['total'] += 1
        cohort_stats[c]['score_sum'] += log.overall_score
        if log.outcome == 'shortlisted' or log.outcome == 'pass':
            cohort_stats[c]['passed'] += 1
    results = []
    for c, stats in cohort_stats.items():
        results.append(BiasAuditStatsResponse(cohort=c, average_score=round(stats['score_sum'] / stats['total'], 2), pass_rate=round(stats['passed'] / stats['total'], 2), total_samples=stats['total']))
    return results

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
