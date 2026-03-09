
import secrets
from datetime import datetime, timedelta, timezone
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
    Certificate, CertificateStatus, InterviewSession,
    SkillProfile, User, AssessmentMode
)
from shared.auth.dependencies import init_jwt_handler, get_current_user_id

engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)

init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)

app = FastAPI(title="SynthHire Certification Service", version="1.0.0")

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

class CertificateCreate(BaseModel):
    session_id: str  

class CertificateResponse(BaseModel):
    id: str
    certificate_code: str
    title: str
    role_type: str
    difficulty_level: str
    overall_score: float
    dimension_scores: dict
    status: str
    issued_at: str
    expires_at: str
    share_url: Optional[str] = None
    is_public: bool = False
    view_count: int = 0
    summary_text: Optional[str] = None

    class Config:
        from_attributes = True

class CertificateListResponse(BaseModel):
    certificates: List[CertificateResponse]
    total: int

class CertificatePublicView(BaseModel):

    certificate_code: str
    title: str
    role_type: str
    difficulty_level: str
    overall_score: float
    dimension_scores: dict
    status: str
    issued_at: str
    expires_at: str
    summary_text: Optional[str] = None
    candidate_name: Optional[str] = None  

def generate_certificate_code() -> str:

    suffix = secrets.token_hex(3).upper()
    return f"SH-CERT-{suffix}"

def generate_share_token() -> str:

    return secrets.token_urlsafe(32)

def session_to_certificate_title(session: InterviewSession) -> str:

    role = session.target_role or "General"
    round_type = session.session_type.value.replace("_", " ").title() if session.session_type else "Interview"
    difficulty = f"Level {session.difficulty_level}" if session.difficulty_level else ""
    return f"{role} {round_type} Assessment {difficulty}".strip()

@app.post("/certificates", response_model=CertificateResponse)
async def create_certificate(
    data: CertificateCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    session = db.query(InterviewSession).filter(
        InterviewSession.id == UUID(data.session_id),
        InterviewSession.user_id == UUID(user_id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status.value != "completed" and session.status.value != "report_ready":
        raise HTTPException(status_code=400, detail="Session must be completed to generate a certificate")

    if session.overall_score is None:
        raise HTTPException(status_code=400, detail="Session must have scores to generate a certificate")

    existing = db.query(Certificate).filter(Certificate.session_id == session.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Certificate already exists for this session")

    now = datetime.now(timezone.utc)
    certificate = Certificate(
        user_id=UUID(user_id),
        session_id=session.id,
        certificate_code=generate_certificate_code(),
        title=session_to_certificate_title(session),
        role_type=session.target_role or "General",
        difficulty_level=str(session.difficulty_level or 5),
        overall_score=session.overall_score,
        dimension_scores=session.dimension_scores or {},
        status=CertificateStatus.ACTIVE,
        issued_at=now,
        expires_at=now + timedelta(days=settings.certificate_ttl_days),
        share_token=generate_share_token(),
        is_public=False,
        summary_text=f"Completed {session_to_certificate_title(session)} with an overall score of {session.overall_score:.1f}%",
        rubric_snapshot=session.dimension_scores,
    )
    certificate.share_url = f"{settings.base_url}/verify/{certificate.share_token}"

    db.add(certificate)

    _update_skill_profile(db, user_id, session)

    db.commit()
    db.refresh(certificate)

    return _cert_to_response(certificate)

@app.get("/certificates", response_model=CertificateListResponse)
async def list_certificates(
    user_id: str = Depends(get_current_user_id),
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):

    query = db.query(Certificate).filter(Certificate.user_id == UUID(user_id))

    if status:
        query = query.filter(Certificate.status == status)

    _check_expirations(db, user_id)

    total = query.count()
    certs = query.order_by(Certificate.issued_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return CertificateListResponse(
        certificates=[_cert_to_response(c) for c in certs],
        total=total
    )

@app.get("/certificates/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(
    certificate_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    cert = db.query(Certificate).filter(
        Certificate.id == UUID(certificate_id),
        Certificate.user_id == UUID(user_id)
    ).first()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return _cert_to_response(cert)

@app.put("/certificates/{certificate_id}/visibility")
async def toggle_visibility(
    certificate_id: str,
    is_public: bool = True,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    cert = db.query(Certificate).filter(
        Certificate.id == UUID(certificate_id),
        Certificate.user_id == UUID(user_id)
    ).first()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    cert.is_public = is_public
    db.commit()

    return {"id": str(cert.id), "is_public": cert.is_public}

@app.get("/verify/{share_token}", response_model=CertificatePublicView)
async def verify_certificate(
    share_token: str,
    db: Session = Depends(get_db)
):

    cert = db.query(Certificate).filter(Certificate.share_token == share_token).first()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.expires_at and cert.expires_at < datetime.now(timezone.utc):
        cert.status = CertificateStatus.EXPIRED
        db.commit()

    cert.view_count = (cert.view_count or 0) + 1
    db.commit()

    candidate_name = None
    if cert.is_public:
        user = db.query(User).filter(User.id == cert.user_id).first()
        if user:
            candidate_name = user.full_name

    return CertificatePublicView(
        certificate_code=cert.certificate_code,
        title=cert.title,
        role_type=cert.role_type,
        difficulty_level=cert.difficulty_level,
        overall_score=cert.overall_score,
        dimension_scores=cert.dimension_scores or {},
        status=cert.status.value,
        issued_at=cert.issued_at.isoformat() if cert.issued_at else "",
        expires_at=cert.expires_at.isoformat() if cert.expires_at else "",
        summary_text=cert.summary_text,
        candidate_name=candidate_name,
    )

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": settings.service_name}
    except Exception as e:
        return {"status": "unhealthy", "service": settings.service_name, "error": str(e)}

def _cert_to_response(cert: Certificate) -> CertificateResponse:
    return CertificateResponse(
        id=str(cert.id),
        certificate_code=cert.certificate_code,
        title=cert.title,
        role_type=cert.role_type,
        difficulty_level=cert.difficulty_level,
        overall_score=cert.overall_score,
        dimension_scores=cert.dimension_scores or {},
        status=cert.status.value if cert.status else "active",
        issued_at=cert.issued_at.isoformat() if cert.issued_at else "",
        expires_at=cert.expires_at.isoformat() if cert.expires_at else "",
        share_url=cert.share_url,
        is_public=cert.is_public or False,
        view_count=cert.view_count or 0,
        summary_text=cert.summary_text,
    )

def _check_expirations(db: Session, user_id: str):

    now = datetime.now(timezone.utc)
    expired = db.query(Certificate).filter(
        Certificate.user_id == UUID(user_id),
        Certificate.status == CertificateStatus.ACTIVE,
        Certificate.expires_at < now
    ).all()

    for cert in expired:
        cert.status = CertificateStatus.EXPIRED

    if expired:
        db.commit()

def _update_skill_profile(db: Session, user_id: str, session: InterviewSession):

    profile = db.query(SkillProfile).filter(SkillProfile.user_id == UUID(user_id)).first()

    if not profile:
        profile = SkillProfile(user_id=UUID(user_id))
        db.add(profile)

    profile.total_assessments = (profile.total_assessments or 0) + 1
    if session.assessment_mode and session.assessment_mode.value == "certified":
        profile.certified_assessments = (profile.certified_assessments or 0) + 1

    dim_scores = session.dimension_scores or {}
    n = profile.total_assessments

    for dim_name, field_name in [
        ("technical_correctness", "technical_knowledge"),
        ("problem_solving", "problem_solving"),
        ("communication", "communication"),
        ("code_quality", "coding_correctness"),
        ("system_design", "system_design"),
        ("behavioral", "behavioral_fit"),
        ("leadership", "leadership"),
        ("culture_fit", "culture_fit"),
    ]:
        if dim_name in dim_scores:
            old_val = getattr(profile, field_name, 0.0) or 0.0
            new_val = dim_scores[dim_name]
            
            setattr(profile, field_name, (old_val * (n - 1) + new_val * 100) / n)

    profile.overall = session.overall_score or profile.overall

    history = profile.score_history or []
    history.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "overall": session.overall_score,
        "dimensions": dim_scores,
        "session_id": str(session.id),
    })
    profile.score_history = history[-20:]  

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)