import re
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
import uvicorn
from .config import settings
from shared.models.base import get_engine, get_session_factory
from shared.models.tables import CompanyAccount, CompanyUser, CompanyRole, RoleTemplate, ScoringProfile, CandidateAssignment, ReviewAction, ReviewDecision, AssignmentStatus, ATSIntegration, User, UserAccountType, InterviewSession, SessionType
from shared.auth.dependencies import init_jwt_handler, get_current_user_id
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)
init_jwt_handler(settings.jwt_public_key_path, algorithm=settings.jwt_algorithm)
app = FastAPI(title='SynthHire Company Service', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://localhost:8888'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub('[^\\w\\s-]', '', text)
    return re.sub('[-\\s]+', '-', text)

class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None

class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    plan: str
    member_count: int = 0
    active_roles: int = 0
    created_at: str

class TeamMemberInvite(BaseModel):
    email: str
    role: str = 'recruiter'

class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    role: str
    is_active: bool
    joined_at: Optional[str] = None

class RoleTemplateCreate(BaseModel):
    title: str
    department: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    interview_type: str = 'technical'
    duration_minutes: int = 45
    scoring_profile_id: Optional[str] = None
    auto_shortlist_enabled: bool = False
    auto_shortlist_threshold: Optional[float] = None

class RoleTemplateResponse(BaseModel):
    id: str
    title: str
    department: Optional[str] = None
    experience_level: Optional[str] = None
    interview_type: str
    duration_minutes: int
    is_active: bool
    candidates_assessed: int = 0
    candidates_shortlisted: int = 0
    auto_shortlist_enabled: bool = False
    created_at: str

class ScoringProfileCreate(BaseModel):
    name: str
    weights: dict
    thresholds: Optional[dict] = None
    pass_threshold: float = 60.0

class ScoringProfileResponse(BaseModel):
    id: str
    name: str
    weights: dict
    thresholds: Optional[dict] = None
    pass_threshold: float
    is_default: bool

class CandidateAssignmentResponse(BaseModel):
    id: str
    candidate_name: str
    candidate_email: str
    status: str
    overall_score: Optional[float] = None
    weighted_score: Optional[float] = None
    fit_score: Optional[float] = None
    dimension_scores: Optional[dict] = None
    invited_at: str
    assessed_at: Optional[str] = None
    tags: list = []
    reviews: list = []

class ReviewActionCreate(BaseModel):
    decision: str
    notes: Optional[str] = None
    dimension_feedback: Optional[dict] = None
    confidence_level: Optional[str] = None

class DashboardStats(BaseModel):
    total_roles: int = 0
    active_roles: int = 0
    total_candidates: int = 0
    assessed: int = 0
    shortlisted: int = 0
    rejected: int = 0
    pending: int = 0

def _require_company_member(db: Session, user_id: str, company_id: str, min_role: str='reviewer') -> CompanyUser:
    membership = db.query(CompanyUser).filter(CompanyUser.company_id == UUID(company_id), CompanyUser.user_id == UUID(user_id), CompanyUser.is_active == True).first()
    if not membership:
        raise HTTPException(status_code=403, detail='Not a member of this company')
    role_hierarchy = {'reviewer': 0, 'recruiter': 1, 'admin': 2}
    if role_hierarchy.get(membership.role.value, 0) < role_hierarchy.get(min_role, 0):
        raise HTTPException(status_code=403, detail=f'Requires {min_role} role or higher')
    return membership

@app.post('/companies', response_model=CompanyResponse)
async def create_company(data: CompanyCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    slug = slugify(data.name)
    existing = db.query(CompanyAccount).filter(CompanyAccount.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail='Company name already taken')
    company = CompanyAccount(name=data.name, slug=slug, website=data.website, industry=data.industry, company_size=data.company_size, description=data.description)
    db.add(company)
    db.flush()
    membership = CompanyUser(company_id=company.id, user_id=UUID(user_id), role=CompanyRole.ADMIN, accepted_at=datetime.now(timezone.utc))
    db.add(membership)
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user:
        user.account_type = UserAccountType.COMPANY
    db.commit()
    db.refresh(company)
    return _company_to_response(company, db)

@app.get('/companies/mine', response_model=List[CompanyResponse])
async def list_my_companies(user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    memberships = db.query(CompanyUser).filter(CompanyUser.user_id == UUID(user_id), CompanyUser.is_active == True).all()
    companies = []
    for m in memberships:
        company = db.query(CompanyAccount).filter(CompanyAccount.id == m.company_id).first()
        if company:
            companies.append(_company_to_response(company, db))
    return companies

@app.get('/companies/{company_id}', response_model=CompanyResponse)
async def get_company(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    company = db.query(CompanyAccount).filter(CompanyAccount.id == UUID(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    return _company_to_response(company, db)

@app.get('/companies/{company_id}/dashboard', response_model=DashboardStats)
async def company_dashboard(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    roles = db.query(RoleTemplate).filter(RoleTemplate.company_id == UUID(company_id)).all()
    role_ids = [r.id for r in roles]
    assignments = []
    if role_ids:
        assignments = db.query(CandidateAssignment).filter(CandidateAssignment.role_template_id.in_(role_ids)).all()
    return DashboardStats(total_roles=len(roles), active_roles=len([r for r in roles if r.is_active]), total_candidates=len(assignments), assessed=len([a for a in assignments if a.status and a.status.value == 'assessed']), shortlisted=len([a for a in assignments if a.status and a.status.value == 'shortlisted']), rejected=len([a for a in assignments if a.status and a.status.value == 'rejected']), pending=len([a for a in assignments if a.status and a.status.value == 'pending']))

@app.get('/companies/{company_id}/team', response_model=List[TeamMemberResponse])
async def list_team_members(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    members = db.query(CompanyUser).filter(CompanyUser.company_id == UUID(company_id), CompanyUser.is_active == True).all()
    results = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            results.append(TeamMemberResponse(id=str(m.id), user_id=str(m.user_id), user_name=user.full_name, user_email=user.email, role=m.role.value, is_active=m.is_active, joined_at=m.accepted_at.isoformat() if m.accepted_at else None))
    return results

@app.post('/companies/{company_id}/team/invite', response_model=TeamMemberResponse)
async def invite_team_member(company_id: str, data: TeamMemberInvite, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='admin')
    target_user = db.query(User).filter(User.email == data.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail='User not found with this email')
    existing = db.query(CompanyUser).filter(CompanyUser.company_id == UUID(company_id), CompanyUser.user_id == target_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail='User is already a member')
    membership = CompanyUser(company_id=UUID(company_id), user_id=target_user.id, role=CompanyRole(data.role), invited_by=UUID(user_id), accepted_at=datetime.now(timezone.utc))
    db.add(membership)
    db.commit()
    return TeamMemberResponse(id=str(membership.id), user_id=str(target_user.id), user_name=target_user.full_name, user_email=target_user.email, role=membership.role.value, is_active=True, joined_at=membership.accepted_at.isoformat() if membership.accepted_at else None)

@app.delete('/companies/{company_id}/team/{member_id}')
async def remove_team_member(company_id: str, member_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='admin')
    member = db.query(CompanyUser).filter(CompanyUser.id == UUID(member_id), CompanyUser.company_id == UUID(company_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail='Member not found')
    member.is_active = False
    db.commit()
    return {'status': 'removed'}

@app.post('/companies/{company_id}/roles', response_model=RoleTemplateResponse)
async def create_role_template(company_id: str, data: RoleTemplateCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='recruiter')
    role = RoleTemplate(company_id=UUID(company_id), created_by=UUID(user_id), title=data.title, department=data.department, experience_level=data.experience_level, description=data.description, interview_type=SessionType(data.interview_type) if data.interview_type else SessionType.TECHNICAL, duration_minutes=data.duration_minutes, scoring_profile_id=UUID(data.scoring_profile_id) if data.scoring_profile_id else None, auto_shortlist_enabled=data.auto_shortlist_enabled, auto_shortlist_threshold=data.auto_shortlist_threshold)
    db.add(role)
    db.commit()
    db.refresh(role)
    return _role_to_response(role)

@app.get('/companies/{company_id}/roles', response_model=List[RoleTemplateResponse])
async def list_role_templates(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    roles = db.query(RoleTemplate).filter(RoleTemplate.company_id == UUID(company_id)).order_by(RoleTemplate.created_at.desc()).all()
    return [_role_to_response(r) for r in roles]

@app.get('/companies/{company_id}/roles/{role_id}', response_model=RoleTemplateResponse)
async def get_role_template(company_id: str, role_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    role = db.query(RoleTemplate).filter(RoleTemplate.id == UUID(role_id), RoleTemplate.company_id == UUID(company_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    return _role_to_response(role)

@app.put('/companies/{company_id}/roles/{role_id}', response_model=RoleTemplateResponse)
async def update_role_template(company_id: str, role_id: str, data: RoleTemplateCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='recruiter')
    role = db.query(RoleTemplate).filter(RoleTemplate.id == UUID(role_id), RoleTemplate.company_id == UUID(company_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    for field in ['title', 'department', 'experience_level', 'description', 'duration_minutes', 'auto_shortlist_enabled', 'auto_shortlist_threshold']:
        val = getattr(data, field, None)
        if val is not None:
            setattr(role, field, val)
    db.commit()
    db.refresh(role)
    return _role_to_response(role)

@app.post('/companies/{company_id}/scoring-profiles', response_model=ScoringProfileResponse)
async def create_scoring_profile(company_id: str, data: ScoringProfileCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='admin')
    profile = ScoringProfile(company_id=UUID(company_id), name=data.name, weights=data.weights, thresholds=data.thresholds, pass_threshold=data.pass_threshold)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ScoringProfileResponse(id=str(profile.id), name=profile.name, weights=profile.weights, thresholds=profile.thresholds, pass_threshold=profile.pass_threshold, is_default=profile.is_default or False)

@app.get('/companies/{company_id}/scoring-profiles', response_model=List[ScoringProfileResponse])
async def list_scoring_profiles(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    profiles = db.query(ScoringProfile).filter(ScoringProfile.company_id == UUID(company_id)).all()
    return [ScoringProfileResponse(id=str(p.id), name=p.name, weights=p.weights, thresholds=p.thresholds, pass_threshold=p.pass_threshold, is_default=p.is_default or False) for p in profiles]

@app.get('/companies/{company_id}/roles/{role_id}/candidates', response_model=List[CandidateAssignmentResponse])
async def list_candidates(company_id: str, role_id: str, status: Optional[str]=None, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    query = db.query(CandidateAssignment).filter(CandidateAssignment.role_template_id == UUID(role_id))
    if status:
        query = query.filter(CandidateAssignment.status == status)
    assignments = query.order_by(CandidateAssignment.created_at.desc()).all()
    results = []
    for a in assignments:
        candidate = db.query(User).filter(User.id == a.candidate_id).first()
        reviews = db.query(ReviewAction).filter(ReviewAction.assignment_id == a.id).all()
        results.append(_assignment_to_response(a, candidate, reviews))
    return results

@app.get('/companies/{company_id}/candidates/{assignment_id}', response_model=CandidateAssignmentResponse)
async def get_candidate_detail(company_id: str, assignment_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    assignment = db.query(CandidateAssignment).filter(CandidateAssignment.id == UUID(assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail='Assignment not found')
    candidate = db.query(User).filter(User.id == assignment.candidate_id).first()
    reviews = db.query(ReviewAction).filter(ReviewAction.assignment_id == assignment.id).all()
    return _assignment_to_response(assignment, candidate, reviews)

@app.post('/companies/{company_id}/candidates/{assignment_id}/review')
async def submit_review(company_id: str, assignment_id: str, data: ReviewActionCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    assignment = db.query(CandidateAssignment).filter(CandidateAssignment.id == UUID(assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail='Assignment not found')
    review = ReviewAction(assignment_id=UUID(assignment_id), reviewer_id=UUID(user_id), decision=ReviewDecision(data.decision), notes=data.notes, dimension_feedback=data.dimension_feedback, confidence_level=data.confidence_level)
    db.add(review)
    if data.decision == 'pass':
        assignment.status = AssignmentStatus.SHORTLISTED
        assignment.decision_at = datetime.now(timezone.utc)
    elif data.decision == 'reject':
        assignment.status = AssignmentStatus.REJECTED
        assignment.decision_at = datetime.now(timezone.utc)
    db.commit()
    return {'status': 'review_submitted', 'assignment_status': assignment.status.value}

@app.put('/companies/{company_id}/candidates/{assignment_id}/status')
async def update_candidate_status(company_id: str, assignment_id: str, status: str=Query(...), user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='recruiter')
    assignment = db.query(CandidateAssignment).filter(CandidateAssignment.id == UUID(assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail='Assignment not found')
    assignment.status = AssignmentStatus(status)
    assignment.decision_at = datetime.now(timezone.utc)
    db.commit()
    return {'status': 'updated', 'new_status': assignment.status.value}

class ATSCreate(BaseModel):
    provider: str
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    events_enabled: list = []

@app.post('/companies/{company_id}/ats')
async def add_ats_integration(company_id: str, data: ATSCreate, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id, min_role='admin')
    ats = ATSIntegration(company_id=UUID(company_id), provider=data.provider, webhook_url=data.webhook_url, api_key_encrypted=data.api_key, events_enabled=data.events_enabled)
    db.add(ats)
    db.commit()
    db.refresh(ats)
    return {'id': str(ats.id), 'provider': ats.provider, 'is_active': ats.is_active}

@app.get('/companies/{company_id}/ats')
async def list_ats_integrations(company_id: str, user_id: str=Depends(get_current_user_id), db: Session=Depends(get_db)):
    _require_company_member(db, user_id, company_id)
    integrations = db.query(ATSIntegration).filter(ATSIntegration.company_id == UUID(company_id)).all()
    return [{'id': str(i.id), 'provider': i.provider, 'webhook_url': i.webhook_url, 'events_enabled': i.events_enabled or [], 'is_active': i.is_active, 'last_sync_at': i.last_sync_at.isoformat() if i.last_sync_at else None} for i in integrations]

class CompanySearchResult(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    industry: Optional[str] = None
    interview_style: Optional[dict] = None
    typical_rounds: Optional[list] = None
    difficulty_level: Optional[str] = None
    glassdoor_rating: Optional[float] = None
    confidence_score: float = 0.0
    source: str = 'cache'

class BlueprintRequest(BaseModel):
    role: str
    experience_level: str = 'mid'

class BlueprintRound(BaseModel):
    round_number: int
    round_type: str
    title: str
    duration_minutes: int
    focus_areas: list = []
    sample_questions: list = []
    persona_suggestion: str = 'kind_mentor'
    difficulty: int = 5

class BlueprintResponse(BaseModel):
    company_name: str
    role: str
    experience_level: str
    total_duration_minutes: int
    rounds: List[BlueprintRound]
    tips: list = []
    generated_by: str = 'gemini'

async def _llm_fetch_company_data(company_name: str) -> dict:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = f'''You are a career intelligence AI. Provide structured interview process data for "{company_name}" in JSON format.\n\nReturn ONLY valid JSON with this structure:\n{'name': \"{company_name}\",\n    \"description\": \"Brief company description\",\n    \"industry\": \"Technology/Finance/etc\",\n    \"interview_style\": {'culture': \"collaborative/competitive/analytical\",\n        \"emphasis\": [\"coding\", \"system_design\", \"behavioral\"],\n        \"unique_traits\": [\"pair programming emphasis\", \"whiteboard heavy\"]\n    } ,\n    \"typical_rounds\": [\n        {'round': 1, \"type\": \"phone_screen\", \"focus\": \"basics\", \"duration_min\": 30} ,\n        {'round': 2, \"type\": \"coding\", \"focus\": \"algorithms\", \"duration_min\": 45} ,\n        {'round': 3, \"type\": \"system_design\", \"focus\": \"architecture\", \"duration_min\": 60} ,\n        {'round': 4, \"type\": \"behavioral\", \"focus\": \"culture_fit\", \"duration_min\": 30} \n    ],\n    \"difficulty_level\": \"hard\",\n    \"glassdoor_rating\": 4.2,\n    \"tips\": [\"Focus on X\", \"Expect Y\"]\n} '''
        response = model.generate_content(prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        import json
        return json.loads(text)
    except Exception as e:
        print(f'LLM fetch error: {e}')
        return {'name': company_name, 'description': f'Interview data for {company_name}', 'difficulty_level': 'medium'}

async def _llm_generate_blueprint(company_name: str, role: str, experience_level: str, company_data: dict=None) -> dict:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        context = ''
        if company_data:
            context = f"\nKnown company data: {company_data.get('interview_style', {})}\nTypical rounds: {company_data.get('typical_rounds', [])}"
        prompt = f'''Generate a detailed interview blueprint for the role "{role}" ({experience_level} level) at "{company_name}".\n{context}\n\nReturn ONLY valid JSON:\n{'rounds': [\n        {'round_number': 1,\n            \"round_type\": \"coding\",\n            \"title\": \"DSA & Problem Solving\",\n            \"duration_minutes\": 45,\n            \"focus_areas\": [\"arrays\", \"trees\", \"dynamic_programming\"],\n            \"sample_questions\": [\n                \"Implement LRU Cache\",\n                \"Find the longest palindromic substring\"\n            ],\n            \"persona_suggestion\": \"tough_lead\",\n            \"difficulty\": 7\n        } \n    ],\n    \"tips\": [\"Tip 1\", \"Tip 2\"],\n    \"total_duration_minutes\": 180\n} \n\nGenerate 3-5 rounds appropriate for {experience_level} level. Include coding, system design, and behavioral rounds as appropriate.'''
        response = model.generate_content(prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        import json
        return json.loads(text)
    except Exception as e:
        print(f'Blueprint generation error: {e}')
        return {'rounds': [{'round_number': 1, 'round_type': 'coding', 'title': 'Technical Screen', 'duration_minutes': 45, 'focus_areas': ['algorithms', 'data_structures'], 'sample_questions': ['Implement a data structure', 'Solve an optimization problem'], 'persona_suggestion': 'kind_mentor', 'difficulty': 5}, {'round_number': 2, 'round_type': 'system_design', 'title': 'System Design', 'duration_minutes': 60, 'focus_areas': ['scalability', 'architecture'], 'sample_questions': ['Design a URL shortener', 'Design a chat system'], 'persona_suggestion': 'tough_lead', 'difficulty': 6}, {'round_number': 3, 'round_type': 'behavioral', 'title': 'Culture Fit', 'duration_minutes': 30, 'focus_areas': ['teamwork', 'leadership'], 'sample_questions': ['Tell me about a time you disagreed', 'Describe a difficult project'], 'persona_suggestion': 'tricky_hr', 'difficulty': 4}], 'tips': [f"Research {company_name}'s engineering blog", 'Practice system design fundamentals'], 'total_duration_minutes': 135}
from shared.models.tables import Company

@app.get('/company/search', response_model=List[CompanySearchResult])
async def search_companies(q: str=Query(..., min_length=2, description='Search query for company name'), db: Session=Depends(get_db)):
    results = db.query(Company).filter(Company.name.ilike(f'%{q}%')).limit(5).all()
    if results:
        return [CompanySearchResult(name=c.name, slug=c.slug, description=c.description, industry=None, interview_style=c.interview_style, typical_rounds=c.typical_rounds, difficulty_level=c.difficulty_level, glassdoor_rating=c.glassdoor_rating, confidence_score=0.9, source='cache') for c in results]
    llm_data = await _llm_fetch_company_data(q)
    slug = slugify(llm_data.get('name', q))
    new_company = Company(name=llm_data.get('name', q), slug=slug, description=llm_data.get('description'), interview_style=llm_data.get('interview_style'), typical_rounds=llm_data.get('typical_rounds'), difficulty_level=llm_data.get('difficulty_level', 'medium'), glassdoor_rating=llm_data.get('glassdoor_rating'))
    try:
        db.add(new_company)
        db.commit()
    except Exception:
        db.rollback()
    return [CompanySearchResult(name=llm_data.get('name', q), slug=slug, description=llm_data.get('description'), industry=llm_data.get('industry'), interview_style=llm_data.get('interview_style'), typical_rounds=llm_data.get('typical_rounds'), difficulty_level=llm_data.get('difficulty_level', 'medium'), glassdoor_rating=llm_data.get('glassdoor_rating'), confidence_score=0.7, source='llm')]

@app.post('/company/{slug}/blueprint', response_model=BlueprintResponse)
async def generate_blueprint(slug: str, data: BlueprintRequest, db: Session=Depends(get_db)):
    company = db.query(Company).filter(Company.slug == slug).first()
    company_data = None
    company_name = slug.replace('-', ' ').title()
    if company:
        company_name = company.name
        company_data = {'interview_style': company.interview_style, 'typical_rounds': company.typical_rounds}
    blueprint = await _llm_generate_blueprint(company_name, data.role, data.experience_level, company_data)
    rounds = [BlueprintRound(**r) for r in blueprint.get('rounds', [])]
    total_duration = blueprint.get('total_duration_minutes', sum((r.duration_minutes for r in rounds)))
    return BlueprintResponse(company_name=company_name, role=data.role, experience_level=data.experience_level, total_duration_minutes=total_duration, rounds=rounds, tips=blueprint.get('tips', []), generated_by='gemini')

@app.get('/health')
async def health(db: Session=Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text('SELECT 1'))
        return {'status': 'healthy', 'service': settings.service_name}
    except Exception as e:
        return {'status': 'unhealthy', 'service': settings.service_name, 'error': str(e)}

def _company_to_response(company: CompanyAccount, db: Session) -> CompanyResponse:
    member_count = db.query(CompanyUser).filter(CompanyUser.company_id == company.id, CompanyUser.is_active == True).count()
    active_roles = db.query(RoleTemplate).filter(RoleTemplate.company_id == company.id, RoleTemplate.is_active == True).count()
    return CompanyResponse(id=str(company.id), name=company.name, slug=company.slug, logo_url=company.logo_url, website=company.website, industry=company.industry, company_size=company.company_size, plan=company.plan, member_count=member_count, active_roles=active_roles, created_at=company.created_at.isoformat() if company.created_at else '')

def _role_to_response(role: RoleTemplate) -> RoleTemplateResponse:
    return RoleTemplateResponse(id=str(role.id), title=role.title, department=role.department, experience_level=role.experience_level, interview_type=role.interview_type.value if role.interview_type else 'technical', duration_minutes=role.duration_minutes or 45, is_active=role.is_active or True, candidates_assessed=role.candidates_assessed or 0, candidates_shortlisted=role.candidates_shortlisted or 0, auto_shortlist_enabled=role.auto_shortlist_enabled or False, created_at=role.created_at.isoformat() if role.created_at else '')

def _assignment_to_response(a: CandidateAssignment, candidate, reviews) -> CandidateAssignmentResponse:
    return CandidateAssignmentResponse(id=str(a.id), candidate_name=candidate.full_name if candidate else 'Unknown', candidate_email=candidate.email if candidate else '', status=a.status.value if a.status else 'pending', overall_score=a.overall_score, weighted_score=a.weighted_score, fit_score=a.fit_score, dimension_scores=a.dimension_scores, invited_at=a.invited_at.isoformat() if a.invited_at else '', assessed_at=a.assessed_at.isoformat() if a.assessed_at else None, tags=a.tags or [], reviews=[{'id': str(r.id), 'decision': r.decision.value, 'notes': r.notes, 'reviewer_id': str(r.reviewer_id), 'created_at': r.created_at.isoformat() if r.created_at else ''} for r in reviews or []])
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)