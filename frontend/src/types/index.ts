export enum UserRole {
    FREE = 'free',
    PRO = 'pro',
    ENTERPRISE = 'enterprise',
    ADMIN = 'admin',
}
export enum SessionType {
    CODING = 'coding',
    SYSTEM_DESIGN = 'system_design',
    BEHAVIORAL = 'behavioral',
    MIXED = 'mixed',
}
export type InterviewPhase = 'talk' | 'code' | 'whiteboard';
export interface Message {
    id?: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    audio_url?: string;
}
export enum SessionStatus {
    CREATED = 'created',
    INITIALIZING = 'initializing',
    ACTIVE = 'active',
    PAUSED = 'paused',
    COMPLETING = 'completing',
    COMPLETED = 'completed',
    REPORT_READY = 'report_ready',
    ERROR = 'error',
    CANCELLED = 'cancelled',
}
export enum PersonaType {
    KIND_MENTOR = 'kind_mentor',
    TOUGH_LEAD = 'tough_lead',
    TRICKY_HR = 'tricky_hr',
    SILENT_OBSERVER = 'silent_observer',
    COLLABORATIVE_PEER = 'collaborative_peer',
}
export enum CoachingMode {
    TRAINING = 'training',
    SIMULATION = 'simulation',
}
export interface User {
    id: string;
    email: string;
    full_name: string;
    role: UserRole;
    account_type?: string;
    company_id?: string;
    avatar_url?: string;
    is_email_verified: boolean;
    created_at: string;
}
export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}
export interface Session {
    id: string;
    user_id: string;
    session_type: SessionType;
    persona_type: PersonaType;
    coaching_mode: CoachingMode;
    difficulty_level: number;
    company_slug?: string;
    target_role?: string;
    status: SessionStatus;
    overall_score?: number;
    dimension_scores?: Record<string, number>;
    started_at?: string;
    completed_at?: string;
    duration_seconds?: number;
    created_at: string;
}
export interface DimensionScores {
    technical_correctness: number;
    problem_decomposition: number;
    communication_clarity: number;
    handling_ambiguity: number;
    edge_case_awareness: number;
    time_management: number;
    collaborative_signals: number;
    growth_mindset: number;
}
export interface Exchange {
    exchange_number: number;
    question_text?: string;
    response_text: string;
    audio_url?: string;
    question_type: string;
    phase_suggestion: string;
    dimension_scores?: DimensionScores;
    coaching_hints?: CoachingHint[];
}
export interface CoachingHint {
    hint: string;
    dimension: string;
    priority: 'high' | 'medium' | 'low';
    timestamp?: string;
}
export interface CodeExecutionResult {
    status: string;
    stdout?: string;
    stderr?: string;
    test_results?: any[];
    passed: number;
    total: number;
    execution_time_ms: number;
}
