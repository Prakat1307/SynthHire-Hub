
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float,
    ForeignKey, Text, Enum, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from .base import Base

class UserRole(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"

class SessionType(str, enum.Enum):
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    MIXED = "mixed"

class SessionStatus(str, enum.Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    REPORT_READY = "report_ready"
    ERROR = "error"
    CANCELLED = "cancelled"

class PersonaType(str, enum.Enum):
    KIND_MENTOR = "kind_mentor"
    TOUGH_LEAD = "tough_lead"
    TRICKY_HR = "tricky_hr"
    SILENT_OBSERVER = "silent_observer"
    COLLABORATIVE_PEER = "collaborative_peer"

class CoachingMode(str, enum.Enum):
    TRAINING = "training"
    SIMULATION = "simulation"

class UserAccountType(str, enum.Enum):
    CANDIDATE = "candidate"
    COMPANY = "company"
    ADMIN = "admin"

class EvidenceType(str, enum.Enum):
    TRANSCRIPT = "transcript"
    CODE_OUTPUT = "code_output"
    SYSTEM_EVENT = "system_event"
    MANUAL = "manual"
    SEMANTIC = "semantic"

class TrustLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FLAGGED = "flagged"

class AssessmentMode(str, enum.Enum):
    PRACTICE = "practice"
    TIMED_MOCK = "timed_mock"
    CERTIFIED = "certified"

class CertificateStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ConsentAction(str, enum.Enum):
    AUDIO_RECORDING = "audio_recording"
    VIDEO_RECORDING = "video_recording"
    TRANSCRIPT_STORAGE = "transcript_storage"
    REPORT_SHARING = "report_sharing"
    COMPANY_VISIBILITY = "company_visibility"
    DATA_PROCESSING = "data_processing"

class LearningStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    auth_provider_id = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.FREE)
    account_type = Column(Enum(UserAccountType), default=UserAccountType.CANDIDATE)
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)

    resume_text = Column(Text, nullable=True)
    resume_parsed_json = Column(JSON, nullable=True)  
    resume_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    is_discoverable = Column(Boolean, default=False)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skill_profile = relationship("SkillProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")
    portfolio = relationship("CandidatePortfolio", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    personal_stories = relationship("PersonalStory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resume_versions = relationship("ResumeVersion", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    target_company = Column(String(100), nullable=True)
    target_role = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    preferred_language = Column(String(50), default="python")
    interview_timeline = Column(String(50), nullable=True)
    timezone = Column(String(100), nullable=True)
    self_assessed_weaknesses = Column(JSON, default=list)
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)  
    coaching_mode = Column(Enum(CoachingMode), default=CoachingMode.TRAINING)
    webcam_enabled = Column(Boolean, default=False)

    industry = Column(String(100), nullable=True)  
    target_companies = Column(JSON, default=list)  
    work_preference = Column(String(50), nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="profile")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan = Column(Enum(UserRole), default=UserRole.FREE)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    sessions_used_this_month = Column(Integer, default=0)
    sessions_limit = Column(Integer, default=3)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="subscription")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(JSON, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserGamification(Base):
    __tablename__ = "user_gamification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    level = Column(Integer, default=1)
    current_xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_practice_date = Column(DateTime(timezone=True), nullable=True)
    
    badges = Column(JSON, default=list)  
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", backref="gamification")

class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_date = Column(DateTime(timezone=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("interview_templates.id"), nullable=False)
    xp_reward = Column(Integer, default=100)
    description = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    logo_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    interview_style = Column(JSON, nullable=True)
    engineering_blog_url = Column(Text, nullable=True)
    glassdoor_rating = Column(Float, nullable=True)
    typical_rounds = Column(JSON, nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class InterviewTemplate(Base):
    __tablename__ = "interview_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    role = Column(String(100), nullable=False)
    round_type = Column(Enum(SessionType), nullable=False)
    experience_level = Column(String(50), nullable=True)
    persona_type = Column(Enum(PersonaType), nullable=True)
    system_prompt = Column(Text, nullable=False)
    persona_vector = Column(JSON, nullable=False)
    difficulty_range = Column(JSON, default={"min": 1, "max": 10})
    duration_minutes = Column(Integer, default=45)
    elevenlabs_voice_id = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("interview_templates.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    session_type = Column(Enum(SessionType), nullable=False)
    persona_type = Column(Enum(PersonaType), nullable=False, default=PersonaType.KIND_MENTOR)
    coaching_mode = Column(Enum(CoachingMode), default=CoachingMode.TRAINING)
    difficulty_level = Column(Integer, default=5)
    company_slug = Column(String(255), nullable=True)
    target_role = Column(String(100), nullable=True)
    webcam_enabled = Column(Boolean, default=False)

    assessment_mode = Column(Enum(AssessmentMode), default=AssessmentMode.PRACTICE)

    is_certified = Column(Boolean, default=False)

    consent_record_id = Column(UUID(as_uuid=True), ForeignKey("consent_records.id"), nullable=True)

    time_limit_minutes = Column(Integer, nullable=True)  

    status = Column(Enum(SessionStatus), default=SessionStatus.CREATED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    overall_score = Column(Float, nullable=True)
    dimension_scores = Column(JSON, nullable=True)
    emotional_summary = Column(JSON, nullable=True)

    audio_recording_url = Column(Text, nullable=True)
    transcript_mongo_id = Column(String(255), nullable=True)

    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    exchanges = relationship("SessionExchange", back_populates="session", cascade="all, delete-orphan")
    code_submissions = relationship("CodeSubmission", back_populates="session", cascade="all, delete-orphan")
    report = relationship("AssessmentReport", back_populates="session", uselist=False, cascade="all, delete-orphan")

class SessionExchange(Base):
    __tablename__ = "session_exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_number = Column(Integer, nullable=False)

    interviewer_text = Column(Text, nullable=True)
    interviewer_audio_url = Column(Text, nullable=True)
    question_type = Column(String(50), nullable=True)
    difficulty_at_time = Column(Integer, nullable=True)

    candidate_text = Column(Text, nullable=True)
    candidate_audio_url = Column(Text, nullable=True)
    response_duration_seconds = Column(Integer, nullable=True)

    dimension_scores = Column(JSON, nullable=True)
    emotional_snapshot = Column(JSON, nullable=True)
    coaching_hints_sent = Column(JSON, nullable=True)
    
    deberta_scores = Column(JSON, nullable=True)  
    gpt4o_scores = Column(JSON, nullable=True)  
    embedding_similarity = Column(Float, nullable=True)  
    behavioral_scores = Column(JSON, nullable=True)  
    ensemble_scores = Column(JSON, nullable=True)  
    
    timestamp_start = Column(DateTime(timezone=True), nullable=True)
    timestamp_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="exchanges")

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey("session_exchanges.id"), nullable=True)

    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)

    execution_status = Column(String(50), nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    memory_used_mb = Column(Float, nullable=True)

    test_cases_total = Column(Integer, nullable=True)
    test_cases_passed = Column(Integer, nullable=True)
    test_results = Column(JSON, nullable=True)

    complexity_analysis = Column(JSON, nullable=True)
    style_issues = Column(JSON, nullable=True)
    version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="code_submissions")

class AssessmentReport(Base):
    __tablename__ = "assessment_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    dimension_details = Column(JSON, nullable=True)
    coaching_narrative = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    improvement_areas = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)

    vs_previous_session = Column(JSON, nullable=True)
    vs_target_benchmark = Column(JSON, nullable=True)
    readiness_score = Column(Float, nullable=True)

    report_html = Column(Text, nullable=True)
    report_pdf_url = Column(Text, nullable=True)

    generation_status = Column(String(50), default="pending")
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="report")

class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())

    total_sessions = Column(Integer, default=0)
    total_practice_hours = Column(Float, default=0.0)
    dimension_averages = Column(JSON, nullable=True)
    company_readiness = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(SessionType), nullable=False)
    difficulty = Column(Integer, nullable=False)
    topics = Column(JSON, nullable=True)

    starter_code = Column(JSON, nullable=True)
    test_cases = Column(JSON, nullable=True)
    optimal_solutions = Column(JSON, nullable=True)
    expected_complexity = Column(JSON, nullable=True)

    design_requirements = Column(JSON, nullable=True)
    reference_architecture = Column(JSON, nullable=True)
    key_discussion_points = Column(JSON, nullable=True)

    star_expectations = Column(JSON, nullable=True)
    follow_up_probes = Column(JSON, nullable=True)
    
    ideal_response_texts = Column(JSON, nullable=True)  
    
    source = Column(String(100), nullable=True)
    frequency_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class TrainingData(Base):

    __tablename__ = "training_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_text = Column(Text, nullable=False)
    question_text = Column(Text, nullable=True)
    question_type = Column(Enum(SessionType), nullable=True)
    
    labels = Column(JSON, nullable=False)  
    
    annotator_id = Column(String(255), nullable=True)
    annotation_confidence = Column(Float, nullable=True)
    source = Column(String(50), nullable=True)  
    is_validated = Column(Boolean, default=False)
    split = Column(String(20), default="train")  
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_training_split', 'split'),
    )

class MLModelRegistry(Base):

    __tablename__ = "ml_model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  
    artifact_path = Column(Text, nullable=False)
    
    metrics = Column(JSON, nullable=True)  
    is_active = Column(Boolean, default=False)
    config = Column(JSON, nullable=True)
    
    trained_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_model_active', 'model_name', 'is_active'),
    )

class SkillProfile(Base):

    __tablename__ = "skill_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    technical_knowledge = Column(Float, default=0.0)
    problem_solving = Column(Float, default=0.0)
    communication = Column(Float, default=0.0)
    coding_correctness = Column(Float, default=0.0)
    system_design = Column(Float, default=0.0)
    behavioral_fit = Column(Float, default=0.0)
    leadership = Column(Float, default=0.0)
    culture_fit = Column(Float, default=0.0)
    overall = Column(Float, default=0.0)

    industry_percentile = Column(Float, nullable=True)  
    role_percentile = Column(JSON, nullable=True)  

    score_history = Column(JSON, default=list)  
    total_assessments = Column(Integer, default=0)
    certified_assessments = Column(Integer, default=0)

    verified_skills = Column(JSON, default=list)  
    skill_confidence = Column(JSON, default=dict)  

    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skill_profile")

class Certificate(Base):

    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)

    certificate_code = Column(String(50), unique=True, nullable=False, index=True)  
    title = Column(String(255), nullable=False)  
    role_type = Column(String(100), nullable=False)
    difficulty_level = Column(String(50), nullable=False)
    overall_score = Column(Float, nullable=False)
    dimension_scores = Column(JSON, nullable=False)  

    status = Column(Enum(CertificateStatus), default=CertificateStatus.ACTIVE)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  

    share_token = Column(String(100), unique=True, nullable=False)  
    share_url = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  
    view_count = Column(Integer, default=0)

    summary_text = Column(Text, nullable=True)  
    rubric_snapshot = Column(JSON, nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="certificates")
    session = relationship("InterviewSession")

class CandidatePortfolio(Base):

    __tablename__ = "candidate_portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    slug = Column(String(100), unique=True, nullable=True, index=True)  
    headline = Column(String(255), nullable=True)  
    bio = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)

    featured_certificate_ids = Column(JSON, default=list)
    featured_skills = Column(JSON, default=list)

    open_to_opportunities = Column(Boolean, default=False)
    preferred_roles = Column(JSON, default=list)  
    preferred_locations = Column(JSON, default=list)  

    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="portfolio")

class LearningPath(Base):

    __tablename__ = "learning_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)  

    title = Column(String(255), nullable=False)  
    description = Column(Text, nullable=True)
    target_dimension = Column(String(100), nullable=False)  
    current_score = Column(Float, nullable=True)  
    target_score = Column(Float, nullable=True)  

    status = Column(Enum(LearningStatus), default=LearningStatus.NOT_STARTED)
    progress_pct = Column(Float, default=0.0)
    total_lessons = Column(Integer, default=0)
    completed_lessons = Column(Integer, default=0)

    curriculum_json = Column(JSON, nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="learning_paths")
    lessons = relationship("MicroLesson", back_populates="learning_path", cascade="all, delete-orphan")

class MicroLesson(Base):

    __tablename__ = "micro_lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True)

    order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    lesson_type = Column(String(50), nullable=False)  
    content_markdown = Column(Text, nullable=True)  
    practice_prompt = Column(Text, nullable=True)  
    example_answer = Column(Text, nullable=True)  
    estimated_minutes = Column(Integer, default=10)

    status = Column(Enum(LearningStatus), default=LearningStatus.NOT_STARTED)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    user_response = Column(Text, nullable=True)  
    score = Column(Float, nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    learning_path = relationship("LearningPath", back_populates="lessons")

class ConsentRecord(Base):

    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(Enum(ConsentAction), nullable=False)
    granted = Column(Boolean, nullable=False)
    context = Column(String(255), nullable=True)  
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="consent_records")

class CompanyRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    REVIEWER = "reviewer"

class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    ASSESSED = "assessed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"

class ReviewDecision(str, enum.Enum):
    PASS = "pass"
    REJECT = "reject"
    FLAG = "flag"
    HOLD = "hold"

class CompanyAccount(Base):

    __tablename__ = "company_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    logo_url = Column(Text, nullable=True)
    website = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  
    description = Column(Text, nullable=True)

    plan = Column(String(50), default="free")  
    stripe_customer_id = Column(String(255), nullable=True)
    max_active_roles = Column(Integer, default=3)
    max_assessments_per_month = Column(Integer, default=50)
    assessments_used_this_month = Column(Integer, default=0)

    default_scoring_profile_id = Column(UUID(as_uuid=True), nullable=True)
    require_consent_for_sharing = Column(Boolean, default=True)
    allow_anonymous_review = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    members = relationship("CompanyUser", back_populates="company", cascade="all, delete-orphan")
    role_templates = relationship("RoleTemplate", back_populates="company", cascade="all, delete-orphan")
    ats_integrations = relationship("ATSIntegration", back_populates="company", cascade="all, delete-orphan")

class CompanyUser(Base):

    __tablename__ = "company_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(CompanyRole), default=CompanyRole.RECRUITER)

    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("CompanyAccount", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_company_user_unique', 'company_id', 'user_id', unique=True),
    )

class RoleTemplate(Base):

    __tablename__ = "role_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    title = Column(String(255), nullable=False)  
    department = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=True)  
    description = Column(Text, nullable=True)

    interview_type = Column(Enum(SessionType), default=SessionType.CODING)
    duration_minutes = Column(Integer, default=45)
    difficulty_range = Column(JSON, default={"min": 3, "max": 8})
    question_bank_ids = Column(JSON, default=list)  

    scoring_profile_id = Column(UUID(as_uuid=True), ForeignKey("scoring_profiles.id"), nullable=True)

    auto_shortlist_enabled = Column(Boolean, default=False)
    auto_shortlist_threshold = Column(Float, nullable=True)  
    auto_shortlist_rules = Column(JSON, nullable=True)  

    is_active = Column(Boolean, default=True)
    candidates_assessed = Column(Integer, default=0)
    candidates_shortlisted = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    company = relationship("CompanyAccount", back_populates="role_templates")
    scoring_profile = relationship("ScoringProfile", foreign_keys=[scoring_profile_id])
    assignments = relationship("CandidateAssignment", back_populates="role_template", cascade="all, delete-orphan")

class ScoringProfile(Base):

    __tablename__ = "scoring_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  

    weights = Column(JSON, nullable=False, default={
        "technical_correctness": 0.20,
        "problem_solving": 0.20,
        "communication": 0.15,
        "code_quality": 0.15,
        "system_design": 0.10,
        "behavioral": 0.10,
        "leadership": 0.05,
        "culture_fit": 0.05,
    })

    thresholds = Column(JSON, nullable=True, default={
        "technical_correctness": 50,
        "communication": 40,
    })

    pass_threshold = Column(Float, default=60.0)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class CandidateAssignment(Base):

    __tablename__ = "candidate_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_template_id = Column(UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)

    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING)
    overall_score = Column(Float, nullable=True)
    weighted_score = Column(Float, nullable=True)  
    dimension_scores = Column(JSON, nullable=True)
    fit_score = Column(Float, nullable=True)  

    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    decision_at = Column(DateTime(timezone=True), nullable=True)

    internal_notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    role_template = relationship("RoleTemplate", back_populates="assignments")
    candidate = relationship("User")
    session = relationship("InterviewSession")
    reviews = relationship("ReviewAction", back_populates="assignment", cascade="all, delete-orphan")

class ReviewAction(Base):

    __tablename__ = "review_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("candidate_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    decision = Column(Enum(ReviewDecision), nullable=False)
    notes = Column(Text, nullable=True)
    dimension_feedback = Column(JSON, nullable=True)  
    confidence_level = Column(String(20), nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignment = relationship("CandidateAssignment", back_populates="reviews")
    reviewer = relationship("User")

class ATSIntegration(Base):

    __tablename__ = "ats_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String(50), nullable=False)  
    webhook_url = Column(Text, nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    sync_direction = Column(String(20), default="push")  

    events_enabled = Column(JSON, default=list)  
    field_mapping = Column(JSON, nullable=True)  

    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    company = relationship("CompanyAccount", back_populates="ats_integrations")

class ScoringDimension(Base):

    __tablename__ = "scoring_dimensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    role_template_id = Column(UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String(100), nullable=False)  
    description = Column(Text, nullable=True)
    evidence_type = Column(Enum(EvidenceType), default=EvidenceType.SEMANTIC)
    weight = Column(Float, default=1.0)
    strictness = Column(Float, default=0.5)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("CompanyAccount")
    role_template = relationship("RoleTemplate")

class DimensionScore(Base):

    __tablename__ = "dimension_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("candidate_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("scoring_dimensions.id", ondelete="CASCADE"), nullable=False)

    score_value = Column(Float, nullable=False)  
    evidence_snippets = Column(JSON, nullable=True)  
    plain_english_explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignment = relationship("CandidateAssignment")
    dimension = relationship("ScoringDimension")

class BiasAuditLog(Base):

    __tablename__ = "bias_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    role_template_id = Column(UUID(as_uuid=True), ForeignKey("role_templates.id"), nullable=True)

    demographic_cohort = Column(String(50), nullable=False)  
    overall_score = Column(Float, nullable=False)
    dimension_scores = Column(JSON, nullable=True)
    outcome = Column(String(50), nullable=False)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrustSignal(Base):

    __tablename__ = "trust_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="SET NULL"), nullable=True)

    signal_type = Column(String(50), nullable=False)  
    trust_level = Column(Enum(TrustLevel), default=TrustLevel.MEDIUM)
    confidence_score = Column(Float, nullable=False)  
    details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    session = relationship("InterviewSession")

class CandidateRoleFit(Base):

    __tablename__ = "candidate_role_fits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_template_id = Column(UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="CASCADE"), nullable=False, index=True)

    match_score = Column(Float, nullable=False)  
    skill_gaps = Column(JSON, nullable=True)  
    strength_highlights = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    candidate = relationship("User")
    role_template = relationship("RoleTemplate")

class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"

class ApplicationStatus(str, enum.Enum):
    NEW = "new"
    APPLIED = "applied"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    OFFERED = "offered"
    HIRED = "hired"

class JobListing(Base):

    __tablename__ = "job_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    role_template_id = Column(UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="SET NULL"), nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=list)  
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=False)
    salary_range = Column(String(100), nullable=True)
    
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT)
    external_url = Column(Text, nullable=True)  
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    company = relationship("CompanyAccount", foreign_keys=[company_id])
    role_template = relationship("RoleTemplate", foreign_keys=[role_template_id])
    source = relationship("JobSource", foreign_keys=[source_id])
    
class JobSource(Base):

    __tablename__ = "job_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  
    provider_type = Column(String(50), nullable=False)  
    
    api_url = Column(Text, nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    config = Column(JSON, default=dict)  
    
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    listings = relationship("JobListing", back_populates="source")

class TrustLevel(str, enum.Enum):

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FLAGGED = "flagged"

class InitialProfile(Base):

    __tablename__ = "initial_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    resume_text = Column(Text, nullable=True)
    years_experience = Column(Integer, nullable=True)
    skills = Column(JSON, default=list)          
    preferred_roles = Column(JSON, default=list) 
    education = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", backref="initial_profile")

class AnswerTone(str, enum.Enum):
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    ASSERTIVE = "assertive"
    WARM = "warm"

class AnswerLength(str, enum.Enum):
    SHORT = "short"            
    MEDIUM = "medium"          
    DETAILED = "detailed"      

class AnswerFormat(str, enum.Enum):
    STAR = "star"              
    BULLET_POINTS = "bullet_points"
    FLOWING = "flowing"        

class PersonalStory(Base):

    __tablename__ = "personal_stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)  
    situation = Column(Text, nullable=False)
    task = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    result = Column(Text, nullable=False)

    tags = Column(JSON, default=list)  
    company_name = Column(String(255), nullable=True)  
    role_at_time = Column(String(255), nullable=True)   

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="personal_stories")

class UserPreferences(Base):

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    tone = Column(Enum(AnswerTone), default=AnswerTone.CONVERSATIONAL)
    answer_length = Column(Enum(AnswerLength), default=AnswerLength.MEDIUM)
    answer_format = Column(Enum(AnswerFormat), default=AnswerFormat.STAR)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="preferences")

class ResumeVersion(Base):

    __tablename__ = "resume_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    label = Column(String(255), nullable=False, default="Master Resume")  
    is_master = Column(Boolean, default=False)  
    raw_text = Column(Text, nullable=True)       
    parsed_json = Column(JSON, nullable=True)    
    file_url = Column(Text, nullable=True)       
    file_name = Column(String(255), nullable=True)
    tailored_for_jd = Column(Text, nullable=True)  
    match_score = Column(Float, nullable=True)     

    version_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="resume_versions")

class PrepAnswerHistory(Base):

    __tablename__ = "prep_answer_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(255), nullable=False)
    answer_text = Column(Text, nullable=False)
    scores_json = Column(JSON, nullable=False)  
    overall_score = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class JobPosting(Base):

    __tablename__ = "job_postings"

    job_id = Column(String(255), primary_key=True)  
    source = Column(String(50), nullable=False)     
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    company_logo_url = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=False)
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), nullable=True)
    
    description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=list)
    experience_level = Column(String(50), nullable=True)  
    
    apply_url = Column(Text, nullable=True)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    match_score = Column(Integer, nullable=True)
    match_details = Column(JSON, nullable=True)

class JobApplication(Base):

    __tablename__ = "job_applications"

    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(255), ForeignKey("job_postings.job_id", ondelete="CASCADE"), nullable=False)
    
    applied_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    status = Column(String(50), default="applied")  
    apply_method = Column(String(50), default="manual")  
    
    resume_used = Column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True)
    cover_letter_text = Column(Text, nullable=True)
    confirmation_screenshot = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    reminder_date = Column(DateTime(timezone=True), nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User")
    job = relationship("JobPosting")
    resume = relationship("ResumeVersion")

class UserJobPreference(Base):

    __tablename__ = "user_job_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    target_roles = Column(JSON, default=list)
    preferred_locations = Column(JSON, default=list)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    remote_preference = Column(String(50), default="any")  
    company_sizes = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    
    daily_apply_limit = Column(Integer, default=10)
    require_review = Column(Boolean, default=True)
    alert_frequency = Column(String(50), default="off")  
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User")

class SavedSearch(Base):

    __tablename__ = "saved_searches"

    search_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    query = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    filters = Column(JSON, default=dict)
    
    email_alert_enabled = Column(Boolean, default=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")