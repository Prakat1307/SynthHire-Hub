from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import uuid
from shared.models import User, UserProfile, Subscription, ProgressSnapshot
from shared.models.base import get_engine, get_session_factory
from shared.auth import get_current_user_id, init_jwt_handler
from .config import settings
app = FastAPI(title='User Service', version='1.0.0')
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)
init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProfileUpdateRequest(BaseModel):
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_language: Optional[str] = None
    interview_timeline: Optional[str] = None
    timezone: Optional[str] = None
    coaching_mode: Optional[str] = None
    webcam_enabled: Optional[bool] = None
    self_assessed_weaknesses: Optional[list[str]] = None
    onboarding_completed: Optional[bool] = None

@app.get('/profile')
async def get_profile(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(id=uuid.uuid4(), user_id=uuid.UUID(user_id))
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@app.put('/profile')
async def update_profile(data: ProfileUpdateRequest, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(id=uuid.uuid4(), user_id=uuid.UUID(user_id))
        db.add(profile)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile

@app.get('/subscription')
async def get_subscription(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        sub = Subscription(id=uuid.uuid4(), user_id=uuid.UUID(user_id), plan='free', sessions_limit=settings.free_sessions_per_month)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

@app.post('/subscription/increment-usage')
async def increment_session_usage(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail='Subscription not found')
    if sub.sessions_limit != -1 and sub.sessions_used_this_month >= sub.sessions_limit:
        raise HTTPException(status_code=403, detail='Monthly session limit reached')
    sub.sessions_used_this_month += 1
    db.commit()
    return {'sessions_used': sub.sessions_used_this_month, 'sessions_limit': sub.sessions_limit}

@app.get('/progress')
async def get_progress_snapshots(limit: int=10, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    snapshots = db.query(ProgressSnapshot).filter(ProgressSnapshot.user_id == uuid.UUID(user_id)).order_by(ProgressSnapshot.snapshot_date.desc()).limit(limit).all()
    return snapshots

@app.get('/profile/activity')
async def get_recent_activity(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    from shared.models.tables import InterviewSession, JobApplication, PrepAnswerHistory, ResumeVersion
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid user ID format')
    activities = []
    try:
        sessions = db.query(InterviewSession).filter(InterviewSession.user_id == uid).order_by(InterviewSession.created_at.desc()).limit(10).all()
        for s in sessions:
            status_val = s.status.value if hasattr(s.status, 'value') else str(s.status)
            type_val = s.session_type.value if hasattr(s.session_type, 'value') else str(s.session_type)
            display_status = 'Report' if status_val == 'active' else status_val
            activities.append({'id': str(s.id), 'type': 'interview', 'title': f"{type_val.replace('_', ' ').title()} Interview", 'status': display_status, 'timestamp': s.created_at.isoformat() if s.created_at else None, 'score': s.overall_score, 'link': f'/interview/report/{s.id}'})
    except Exception as e:
        print(f'Error fetching sessions for activity: {e}')
    try:
        jobs = db.query(JobApplication).filter(JobApplication.user_id == uid).order_by(JobApplication.applied_at.desc()).limit(10).all()
        for g in jobs:
            status_val = g.status.value if hasattr(g.status, 'value') else str(g.status)
            activities.append({'id': str(g.application_id), 'type': 'job', 'title': g.job.title if hasattr(g, 'job') and g.job else 'Job Application', 'status': status_val, 'timestamp': g.applied_at.isoformat() if g.applied_at else None, 'company': g.job.company if hasattr(g, 'job') and g.job else 'External', 'link': '/jobs'})
    except Exception as e:
        print(f'Error fetching jobs for activity: {e}')
    try:
        preps = db.query(PrepAnswerHistory).filter(PrepAnswerHistory.user_id == uid).order_by(PrepAnswerHistory.created_at.desc()).limit(10).all()
        for p in preps:
            activities.append({'id': str(p.id), 'type': 'prep', 'title': f'Prep Question Answered', 'status': 'completed', 'timestamp': p.created_at.isoformat() if p.created_at else None, 'score': p.overall_score, 'link': '/prep'})
    except Exception as e:
        print(f'Error fetching prep history for activity: {e}')
    try:
        resumes = db.query(ResumeVersion).filter(ResumeVersion.user_id == uid).order_by(ResumeVersion.created_at.desc()).limit(10).all()
        for r in resumes:
            activities.append({'id': str(r.id), 'type': 'resume', 'title': r.label or 'Resume Update', 'status': 'active' if r.is_active else 'archived', 'timestamp': r.created_at.isoformat() if r.created_at else None, 'link': '/resume'})
    except Exception as e:
        print(f'Error fetching resume history for activity: {e}')
    activities = [a for a in activities if a['timestamp']]
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return {'activities': activities[:10]}

@app.get('/profile/stats')
async def get_profile_stats(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    from shared.models.tables import InterviewSession
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid user ID format')
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == uid, InterviewSession.duration_seconds.isnot(None)).all()
    total_sessions = len(sessions)
    total_hours = sum([s.duration_seconds for s in sessions if s.duration_seconds]) / 3600.0
    dimension_totals = {}
    dimension_counts = {}
    sessions_completed = db.query(InterviewSession).filter(InterviewSession.user_id == uid, InterviewSession.status == 'completed').all()
    for s in sessions_completed:
        if s.dimension_scores and isinstance(s.dimension_scores, dict):
            for dim, score in s.dimension_scores.items():
                dimension_totals[dim] = dimension_totals.get(dim, 0) + score
                dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
    dimension_scores = {dim: dimension_totals[dim] / dimension_counts[dim] for dim in dimension_totals}
    return {'total_sessions': total_sessions, 'total_hours': round(total_hours, 1), 'streak_days': 1 if total_sessions > 0 else 0, 'dimension_scores': dimension_scores}

@app.get('/health')
async def health(db: Session=Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text('SELECT 1'))
        return {'status': 'healthy', 'service': 'user-service', 'db': 'connected'}
    except Exception as e:
        return {'status': 'unhealthy', 'service': 'user-service', 'db': str(e)}
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)