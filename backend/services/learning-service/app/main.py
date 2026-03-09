
import json
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uvicorn

from .config import settings
from shared.models.base import get_engine, get_session_factory
from shared.models.tables import (
    LearningPath, MicroLesson, LearningStatus,
    InterviewSession, SkillProfile, User, AssessmentReport
)
from shared.auth.dependencies import init_jwt_handler, get_current_user_id

engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)

init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)

app = FastAPI(title="SynthHire Learning Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8888"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GapAnalysisRequest(BaseModel):
    session_id: Optional[str] = None  

class GapAnalysisResponse(BaseModel):
    gaps: list  
    recommended_paths: list  

class LearningPathResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    target_dimension: str
    current_score: Optional[float] = None
    target_score: Optional[float] = None
    status: str
    progress_pct: float
    total_lessons: int
    completed_lessons: int
    created_at: str

class LearningPathListResponse(BaseModel):
    paths: List[LearningPathResponse]
    total: int

class LessonResponse(BaseModel):
    id: str
    order: int
    title: str
    lesson_type: str
    content_markdown: Optional[str] = None
    practice_prompt: Optional[str] = None
    example_answer: Optional[str] = None
    estimated_minutes: int
    status: str
    score: Optional[float] = None

class LessonSubmitRequest(BaseModel):
    response_text: str

class CreatePathRequest(BaseModel):
    session_id: Optional[str] = None
    target_dimension: str
    title: Optional[str] = None

SCORE_DIMENSIONS = [
    ("technical_knowledge", "Technical Knowledge", 70.0),
    ("problem_solving", "Problem Solving", 70.0),
    ("communication", "Communication", 65.0),
    ("coding_correctness", "Coding Correctness", 70.0),
    ("system_design", "System Design", 65.0),
    ("behavioral_fit", "Behavioral Fit", 60.0),
    ("leadership", "Leadership", 55.0),
    ("culture_fit", "Culture Fit", 60.0),
]

LESSON_TEMPLATES = {
    "technical_knowledge": [
        {"title": "Core Concepts Review", "type": "explanation", "minutes": 15},
        {"title": "Knowledge Check Quiz", "type": "quiz", "minutes": 10},
        {"title": "Applied Problem Set", "type": "practice", "minutes": 20},
        {"title": "Deep Dive: Edge Cases", "type": "explanation", "minutes": 15},
        {"title": "Mock Q&A Practice", "type": "practice", "minutes": 20},
    ],
    "problem_solving": [
        {"title": "Structured Approach Framework", "type": "explanation", "minutes": 10},
        {"title": "Breaking Down Complex Problems", "type": "practice", "minutes": 20},
        {"title": "Time-Boxed Problem Sprint", "type": "practice", "minutes": 25},
        {"title": "Solution Evaluation Criteria", "type": "explanation", "minutes": 10},
        {"title": "Mock Problem Solving Session", "type": "practice", "minutes": 30},
    ],
    "communication": [
        {"title": "STAR Method Mastery", "type": "explanation", "minutes": 10},
        {"title": "Articulating Technical Decisions", "type": "practice", "minutes": 15},
        {"title": "Handling Ambiguity", "type": "practice", "minutes": 15},
        {"title": "Clarity and Conciseness", "type": "explanation", "minutes": 10},
        {"title": "Full Communication Drill", "type": "practice", "minutes": 20},
    ],
    "coding_correctness": [
        {"title": "Common Bug Patterns", "type": "explanation", "minutes": 15},
        {"title": "Test-Driven Development Basics", "type": "coding_task", "minutes": 25},
        {"title": "Edge Case Thinking", "type": "practice", "minutes": 20},
        {"title": "Code Review Exercise", "type": "coding_task", "minutes": 20},
        {"title": "Timed Coding Challenge", "type": "coding_task", "minutes": 30},
    ],
    "system_design": [
        {"title": "Design Fundamentals", "type": "explanation", "minutes": 20},
        {"title": "Scalability Patterns", "type": "explanation", "minutes": 15},
        {"title": "Design a URL Shortener", "type": "practice", "minutes": 30},
        {"title": "Trade-off Analysis", "type": "practice", "minutes": 20},
        {"title": "Full System Design Mock", "type": "practice", "minutes": 45},
    ],
}

DEFAULT_LESSONS = [
    {"title": "Fundamentals Review", "type": "explanation", "minutes": 15},
    {"title": "Self-Assessment Exercise", "type": "practice", "minutes": 15},
    {"title": "Guided Practice", "type": "practice", "minutes": 20},
    {"title": "Application Challenge", "type": "practice", "minutes": 25},
    {"title": "Comprehensive Review", "type": "quiz", "minutes": 15},
]

@app.post("/gaps/analyze", response_model=GapAnalysisResponse)
async def analyze_gaps(
    data: GapAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    gaps = []
    recommended = []

    if data.session_id:
        
        session = db.query(InterviewSession).filter(
            InterviewSession.id == UUID(data.session_id),
            InterviewSession.user_id == UUID(user_id)
        ).first()
        if not session or not session.dimension_scores:
            raise HTTPException(status_code=404, detail="Session not found or has no scores")

        for dim_key, dim_name, target in SCORE_DIMENSIONS:
            score = session.dimension_scores.get(dim_key, 0) * 100  
            if score < target:
                severity = "high" if score < target - 20 else "medium" if score < target - 10 else "low"
                gaps.append({
                    "dimension": dim_key,
                    "dimension_name": dim_name,
                    "current_score": round(score, 1),
                    "target_score": target,
                    "severity": severity
                })
    else:
        
        profile = db.query(SkillProfile).filter(SkillProfile.user_id == UUID(user_id)).first()
        if not profile:
            return GapAnalysisResponse(gaps=[], recommended_paths=[])

        for dim_key, dim_name, target in SCORE_DIMENSIONS:
            score = getattr(profile, dim_key, 0.0) or 0.0
            if score < target:
                severity = "high" if score < target - 20 else "medium" if score < target - 10 else "low"
                gaps.append({
                    "dimension": dim_key,
                    "dimension_name": dim_name,
                    "current_score": round(score, 1),
                    "target_score": target,
                    "severity": severity
                })

    severity_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: severity_order.get(g["severity"], 3))

    for gap in gaps[:3]:  
        recommended.append({
            "title": f"Improve {gap['dimension_name']}",
            "dimension": gap["dimension"],
            "description": f"Build your {gap['dimension_name'].lower()} skills from {gap['current_score']:.0f}% to {gap['target_score']:.0f}%",
        })

    return GapAnalysisResponse(gaps=gaps, recommended_paths=recommended)

@app.post("/paths", response_model=LearningPathResponse)
async def create_learning_path(
    data: CreatePathRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    current_score = 0.0
    profile = db.query(SkillProfile).filter(SkillProfile.user_id == UUID(user_id)).first()
    if profile:
        current_score = getattr(profile, data.target_dimension, 0.0) or 0.0

    target_score = 70.0
    for dim_key, _, target in SCORE_DIMENSIONS:
        if dim_key == data.target_dimension:
            target_score = target
            break

    dim_name = data.target_dimension.replace("_", " ").title()
    title = data.title or f"Improve {dim_name}"

    path = LearningPath(
        user_id=UUID(user_id),
        session_id=UUID(data.session_id) if data.session_id else None,
        title=title,
        description=f"A focused learning path to improve your {dim_name.lower()} skills",
        target_dimension=data.target_dimension,
        current_score=current_score,
        target_score=target_score,
        status=LearningStatus.NOT_STARTED,
    )

    db.add(path)
    db.flush()  

    templates = LESSON_TEMPLATES.get(data.target_dimension, DEFAULT_LESSONS)
    for i, tmpl in enumerate(templates):
        lesson = MicroLesson(
            learning_path_id=path.id,
            order=i + 1,
            title=tmpl["title"],
            lesson_type=tmpl["type"],
            estimated_minutes=tmpl["minutes"],
            content_markdown=_generate_lesson_content(data.target_dimension, tmpl["title"], tmpl["type"]),
            practice_prompt=_generate_practice_prompt(data.target_dimension, tmpl["title"]) if tmpl["type"] in ("practice", "quiz", "coding_task") else None,
            example_answer=_generate_example_answer(data.target_dimension, tmpl["title"]) if tmpl["type"] in ("practice", "quiz", "coding_task") else None,
            status=LearningStatus.NOT_STARTED,
        )
        db.add(lesson)

    path.total_lessons = len(templates)
    db.commit()
    db.refresh(path)

    return _path_to_response(path)

@app.get("/paths", response_model=LearningPathListResponse)
async def list_learning_paths(
    user_id: str = Depends(get_current_user_id),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = db.query(LearningPath).filter(LearningPath.user_id == UUID(user_id))
    if status:
        query = query.filter(LearningPath.status == status)

    paths = query.order_by(LearningPath.created_at.desc()).all()

    return LearningPathListResponse(
        paths=[_path_to_response(p) for p in paths],
        total=len(paths)
    )

@app.get("/paths/{path_id}", response_model=LearningPathResponse)
async def get_learning_path(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    path = db.query(LearningPath).filter(
        LearningPath.id == UUID(path_id),
        LearningPath.user_id == UUID(user_id)
    ).first()
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return _path_to_response(path)

@app.get("/paths/{path_id}/lessons", response_model=List[LessonResponse])
async def list_lessons(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    path = db.query(LearningPath).filter(
        LearningPath.id == UUID(path_id),
        LearningPath.user_id == UUID(user_id)
    ).first()
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    lessons = db.query(MicroLesson).filter(
        MicroLesson.learning_path_id == UUID(path_id)
    ).order_by(MicroLesson.order).all()

    return [_lesson_to_response(l) for l in lessons]

@app.get("/paths/{path_id}/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    path_id: str,
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    lesson = db.query(MicroLesson).filter(
        MicroLesson.id == UUID(lesson_id),
        MicroLesson.learning_path_id == UUID(path_id)
    ).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return _lesson_to_response(lesson)

@app.post("/paths/{path_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    path_id: str,
    lesson_id: str,
    data: Optional[LessonSubmitRequest] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    path = db.query(LearningPath).filter(
        LearningPath.id == UUID(path_id),
        LearningPath.user_id == UUID(user_id)
    ).first()
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    lesson = db.query(MicroLesson).filter(
        MicroLesson.id == UUID(lesson_id),
        MicroLesson.learning_path_id == UUID(path_id)
    ).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson.status = LearningStatus.COMPLETED
    lesson.completed_at = datetime.now(timezone.utc)
    if data:
        lesson.user_response = data.response_text
        
        lesson.score = 0.75  

    if path.status == LearningStatus.NOT_STARTED:
        path.status = LearningStatus.IN_PROGRESS

    path.completed_lessons = (path.completed_lessons or 0) + 1
    if path.total_lessons and path.total_lessons > 0:
        path.progress_pct = (path.completed_lessons / path.total_lessons) * 100

    if path.completed_lessons >= path.total_lessons:
        path.status = LearningStatus.COMPLETED
        path.progress_pct = 100.0

    db.commit()

    return {
        "lesson_id": str(lesson.id),
        "status": "completed",
        "score": lesson.score,
        "path_progress": path.progress_pct,
        "path_status": path.status.value
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": settings.service_name}
    except Exception as e:
        return {"status": "unhealthy", "service": settings.service_name, "error": str(e)}

def _path_to_response(path: LearningPath) -> LearningPathResponse:
    return LearningPathResponse(
        id=str(path.id),
        title=path.title,
        description=path.description,
        target_dimension=path.target_dimension,
        current_score=path.current_score,
        target_score=path.target_score,
        status=path.status.value if path.status else "not_started",
        progress_pct=path.progress_pct or 0.0,
        total_lessons=path.total_lessons or 0,
        completed_lessons=path.completed_lessons or 0,
        created_at=path.created_at.isoformat() if path.created_at else "",
    )

def _lesson_to_response(lesson: MicroLesson) -> LessonResponse:
    return LessonResponse(
        id=str(lesson.id),
        order=lesson.order,
        title=lesson.title,
        lesson_type=lesson.lesson_type,
        content_markdown=lesson.content_markdown,
        practice_prompt=lesson.practice_prompt,
        example_answer=lesson.example_answer,
        estimated_minutes=lesson.estimated_minutes or 10,
        status=lesson.status.value if lesson.status else "not_started",
        score=lesson.score,
    )

def _generate_lesson_content(dimension: str, title: str, lesson_type: str) -> str:

    dim_name = dimension.replace("_", " ").title()
    if lesson_type == "explanation":
        return f"""# {title}

## Overview
This lesson covers key concepts for improving your **{dim_name}** skills.

## Key Takeaways
1. Understand the fundamentals and common patterns
2. Practice identifying gaps in your approach
3. Build confidence through structured preparation

## Tips
- Focus on clarity and structure in your responses
- Practice explaining concepts to others
- Review and iterate on your approach after each practice session
"""
    return f"# {title}\n\nComplete this practice exercise to strengthen your {dim_name.lower()} skills."

def _generate_practice_prompt(dimension: str, title: str) -> str:

    dim_name = dimension.replace("_", " ").title()
    return f"Practice exercise for {dim_name}: {title}. Describe your approach step by step."

def _generate_example_answer(dimension: str, title: str) -> str:

    return f"A strong answer would demonstrate structured thinking, clear communication, and relevant examples."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)