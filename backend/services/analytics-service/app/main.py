
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta

from shared.models import User, InterviewSession, ProgressSnapshot, UserGamification
from shared.models.base import get_engine, get_session_factory
from shared.auth import get_current_user_id, init_jwt_handler
from .config import settings

app = FastAPI(title="Analytics Service", version="1.0.0")

engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)

init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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

@app.get("/analytics/dashboard/{user_id}")
async def get_dashboard_stats(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these stats")
        
    total_sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed"
    ).count()
    
    total_seconds = db.query(func.sum(InterviewSession.duration_seconds)).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed"
    ).scalar() or 0
    
    latest_snapshot = db.query(ProgressSnapshot).filter(
        ProgressSnapshot.user_id == user_id
    ).order_by(ProgressSnapshot.snapshot_date.desc()).first()
    
    dimension_scores = {}
    if latest_snapshot and latest_snapshot.dimension_averages:
        dimension_scores = latest_snapshot.dimension_averages
        
    return {
        "total_sessions": total_sessions,
        "total_hours": round(total_seconds / 3600, 1),
        "streak_days": 0, 
        "dimension_scores": dimension_scores,
        "recent_activity": [] 
    }

@app.post("/analytics/snapshot")
async def create_snapshot(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == "completed"
    ).all()
    
    if not sessions:
        return {"status": "no_data"}
        
    dim_sums = {}
    dim_counts = {}
    
    for s in sessions:
        if s.dimension_scores:
            for dim, score in s.dimension_scores.items():
                dim_sums[dim] = dim_sums.get(dim, 0) + score
                dim_counts[dim] = dim_counts.get(dim, 0) + 1
                
    averages = {dim: round(dim_sums[dim] / dim_counts[dim], 2) for dim in dim_sums}
    
    snapshot = ProgressSnapshot(
        user_id=user_id,
        snapshot_date=datetime.utcnow(),
        total_sessions=len(sessions),
        total_practice_hours=sum(s.duration_seconds or 0 for s in sessions) / 3600,
        dimension_averages=averages
    )
    
    db.add(snapshot)
    db.commit()
    
    return {"status": "created", "snapshot_id": str(snapshot.id)}

@app.post("/gamification/award")
async def award_xp(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    session_record = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user_id,
        InterviewSession.status == "completed"
    ).first()
    
    if not session_record:
        raise HTTPException(status_code=404, detail="Completed session not found.")
        
    gamification = db.query(UserGamification).filter(UserGamification.user_id == current_user_id).first()
    if not gamification:
        gamification = UserGamification(user_id=current_user_id)
        db.add(gamification)
        
    base_xp = 50 
    score_multiplier = (session_record.overall_score or 0) / 100.0
    performance_xp = int(100 * score_multiplier)
    
    xp_earned = base_xp + performance_xp
    
    gamification.current_xp += xp_earned
    gamification.total_xp += xp_earned
    
    while gamification.current_xp >= 1000:
        gamification.level += 1
        gamification.current_xp -= 1000
        
    gamification.last_practice_date = datetime.utcnow()
    
    gamification.current_streak_days += 1
    if gamification.current_streak_days > gamification.longest_streak_days:
        gamification.longest_streak_days = gamification.current_streak_days
        
    db.commit()
    db.refresh(gamification)
    
    return {
        "xp_earned": xp_earned,
        "new_total": gamification.total_xp,
        "level": gamification.level,
        "current_streak": gamification.current_streak_days
    }

@app.get("/leaderboard")
async def get_leaderboard(
    limit: int = 50,
    db: Session = Depends(get_db)
):

    top_users = db.query(UserGamification, User.full_name, User.avatar_url).join(
        User, UserGamification.user_id == User.id
    ).order_by(UserGamification.total_xp.desc()).limit(limit).all()
    
    leaderboard = []
    for rank, (gamification, name, avatar) in enumerate(top_users, start=1):
        leaderboard.append({
            "rank": rank,
            "user_id": str(gamification.user_id),
            "name": name,
            "avatar_url": avatar,
            "level": gamification.level,
            "total_xp": gamification.total_xp,
            "streak": gamification.current_streak_days
        })
        
    return {"leaderboard": leaderboard}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)