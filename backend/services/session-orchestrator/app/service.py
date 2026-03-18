import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from sqlalchemy.orm import Session as DBSession
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import json
import asyncio
from shared.models.tables import InterviewSession, SessionExchange, SessionStatus, SessionType, PersonaType, CoachingMode, Company
from shared.schemas.session import SessionCreate, SessionResponse
from shared.utils.redis_client import RedisClient
from shared.utils.mongodb_client import MongoDBClient
from shared.utils.http_client import ServiceClient
from .config import settings
from .persona_prompts import build_system_prompt
from .adaptive_difficulty import AdaptiveDifficultyController

class SessionOrchestrator:

    def __init__(self, db: DBSession, redis: RedisClient, mongodb: MongoDBClient, user_client: ServiceClient, speech_client: ServiceClient, assessment_client: ServiceClient, coaching_client: ServiceClient, report_client: ServiceClient, code_executor_client: ServiceClient, emotion_client: ServiceClient, analytics_client: ServiceClient):
        self.db = db
        self.redis = redis
        self.mongodb = mongodb
        self.user_client = user_client
        self.speech_client = speech_client
        self.assessment_client = assessment_client
        self.coaching_client = coaching_client
        self.report_client = report_client
        self.code_executor_client = code_executor_client
        self.emotion_client = emotion_client
        self.analytics_client = analytics_client
        self.session: Optional[InterviewSession] = None
        self.difficulty_controller: Optional[AdaptiveDifficultyController] = None

    async def create_session(self, user_id: str, data: SessionCreate) -> InterviewSession:
        active = await self.redis.get_user_active_session(user_id)
        if active:
            existing_session = self.db.query(InterviewSession).filter(InterviewSession.id == active).first()
            if existing_session:
                return existing_session
            await self.redis.clear_user_active_session(user_id)
        try:
            await self.user_client.post('/subscription/increment-usage', headers={'X-User-Id': user_id})
        except Exception as e:
            print(f'[WARNING] Subscription increment failed (non-fatal): {str(e)}')
        final_company_slug = data.custom_company_name
        final_company_id = None
        if not final_company_slug and data.company_id:
            try:
                UUID(data.company_id)
                company = self.db.query(Company).filter(Company.id == data.company_id).first()
            except ValueError:
                company = self.db.query(Company).filter(Company.slug == data.company_id).first()
            if company:
                final_company_id = company.id
                final_company_slug = company.slug
            else:
                final_company_slug = data.company_id
        from shared.models.tables import AssessmentMode
        session = InterviewSession(user_id=UUID(user_id), session_type=SessionType(data.session_type), persona_type=PersonaType(data.persona_type), coaching_mode=CoachingMode(data.coaching_mode), assessment_mode=AssessmentMode(data.assessment_mode) if hasattr(data, 'assessment_mode') else AssessmentMode.PRACTICE, difficulty_level=data.difficulty_level, company_slug=final_company_slug, company_id=final_company_id, target_role=data.target_role, webcam_enabled=data.webcam_enabled, time_limit_minutes=data.time_limit_minutes, status=SessionStatus.CREATED)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        await self.redis.set_session_state(str(session.id), {'status': 'created', 'user_id': user_id, 'session_type': data.session_type, 'persona_type': data.persona_type, 'coaching_mode': data.coaching_mode, 'assessment_mode': session.assessment_mode.value, 'time_limit_minutes': session.time_limit_minutes, 'difficulty_level': data.difficulty_level, 'resume_text': data.resume_text or '', 'exchange_count': 0, 'current_phase': 'INITIALIZING', 'dimension_scores': {'technical_correctness': 0.0, 'problem_decomposition': 0.0, 'communication_clarity': 0.0, 'handling_ambiguity': 0.0, 'edge_case_awareness': 0.0, 'time_management': 0.0, 'collaborative_signals': 0.0, 'growth_mindset': 0.0}, 'started_at': datetime.utcnow().isoformat()})
        await self.redis.set_user_active_session(user_id, str(session.id))
        return session

    async def load_session(self, session_id: str, user_id: str):
        session = self.db.query(InterviewSession).filter(InterviewSession.id == UUID(session_id), InterviewSession.user_id == UUID(user_id)).first()
        if not session:
            raise ValueError('Session not found')
        self.session = session
        self.difficulty_controller = AdaptiveDifficultyController(initial_difficulty=session.difficulty_level, persona_type=session.persona_type.value)

    async def start_session(self) -> Dict[str, Any]:
        if not self.session:
            raise ValueError('No session loaded')
        print(f'start_session: starting for session {self.session.id}')
        self.session.status = SessionStatus.ACTIVE
        self.session.started_at = datetime.utcnow()
        self.db.commit()
        print('start_session: db committed')
        await self.redis.update_session_field(str(self.session.id), 'status', 'active')
        await self.redis.update_session_field(str(self.session.id), 'current_phase', 'AI_SPEAKING')
        print('start_session: redis updated')
        system_prompt = build_system_prompt(persona_type=self.session.persona_type.value, session_type=self.session.session_type.value, difficulty=self.session.difficulty_level, company_slug=self.session.company_slug, target_role=self.session.target_role, resume_text=await self._get_cached_resume_text())
        print(f'start_session: calling speech client to /ai/generate at {self.speech_client.base_url}')
        opening_response = await self.speech_client.post('/ai/generate', {'system_prompt': system_prompt, 'conversation_history': [], 'user_message': '[SESSION_START]', 'persona_type': self.session.persona_type.value, 'generate_audio': True})
        print('start_session: speech client returned successfully')
        await self.redis.append_conversation(str(self.session.id), {'role': 'assistant', 'content': opening_response['response_text'], 'timestamp': datetime.utcnow().isoformat()})
        print('start_session: returning response')
        return {'response_text': opening_response['response_text'], 'audio_url': opening_response.get('audio_url'), 'exchange_number': 0, 'phase': 'AI_SPEAKING'}

    async def process_user_message(self, text: str) -> Dict[str, Any]:
        session_id = str(self.session.id)
        state = await self.redis.get_session_state(session_id)
        try:
            exchange_count = int(state.get('exchange_count', 0)) + 1
        except (ValueError, TypeError):
            exchange_count = 1
        await self.redis.append_conversation(session_id, {'role': 'user', 'content': text, 'timestamp': datetime.utcnow().isoformat()})
        elapsed_minutes = 0
        if self.session.started_at:
            started_at_naive = self.session.started_at.replace(tzinfo=None) if self.session.started_at.tzinfo else self.session.started_at
            elapsed_minutes = (datetime.utcnow() - started_at_naive).total_seconds() / 60
        if self.session.time_limit_minutes and elapsed_minutes > self.session.time_limit_minutes:
            return {'exchange_number': exchange_count, 'response_text': 'The time limit for this assessment has been reached. Ending session.', 'phase_suggestion': 'end', 'dimension_scores': state.get('dimension_scores', {}), 'coaching_hints': [], 'time_up': True}
        behavioral_scores = {}
        try:
            beh_resp = await self.emotion_client.post('/emotion/behavioral-scores', {'session_id': session_id})
            behavioral_scores = beh_resp.get('scores', {})
        except Exception as e:
            print(f'Failed to get behavioral scores: {e}')
        assessment_response = await self.assessment_client.post('/assess', {'session_id': session_id, 'exchange_number': exchange_count, 'response_text': text, 'session_type': self.session.session_type.value, 'behavioral_scores': behavioral_scores})
        scores = assessment_response.get('scores', {})
        difficulty_update = self.difficulty_controller.update(scores)
        history = await self.redis.get_conversation_history(session_id)
        elapsed_minutes = 0
        if self.session.started_at:
            elapsed_minutes = int((datetime.utcnow() - started_at_naive).total_seconds() / 60)
        system_prompt = build_system_prompt(persona_type=self.session.persona_type.value, session_type=self.session.session_type.value, difficulty=difficulty_update['new_difficulty'], company_slug=self.session.company_slug, target_role=self.session.target_role, time_elapsed_minutes=elapsed_minutes, current_scores=scores, resume_text=state.get('resume_text', ''))
        ai_response = await self.speech_client.post('/ai/generate', {'system_prompt': system_prompt, 'conversation_history': history[-10:], 'user_message': text, 'persona_type': self.session.persona_type.value, 'generate_audio': True, 'difficulty_action': difficulty_update['action']})
        await self.redis.append_conversation(session_id, {'role': 'assistant', 'content': ai_response['response_text'], 'timestamp': datetime.utcnow().isoformat()})
        await self.redis.update_session_field(session_id, 'exchange_count', exchange_count)
        await self.redis.update_session_field(session_id, 'difficulty_level', difficulty_update['new_difficulty'])
        await self.redis.update_session_field(session_id, 'dimension_scores', scores)
        await self.mongodb.save_exchange({'session_id': session_id, 'exchange_number': exchange_count, 'user_message': text, 'ai_response': ai_response['response_text'], 'dimension_scores': scores, 'difficulty_at_time': difficulty_update['new_difficulty'], 'timestamp': datetime.utcnow().isoformat()})
        exchange = SessionExchange(session_id=self.session.id, exchange_number=exchange_count, interviewer_text=ai_response['response_text'], candidate_text=text, dimension_scores=scores, difficulty_at_time=difficulty_update['new_difficulty'], timestamp_start=datetime.utcnow())
        self.db.add(exchange)
        self.db.commit()
        coaching_hints = []
        if self.session.coaching_mode == CoachingMode.TRAINING:
            try:
                hints_response = await self.coaching_client.post('/coaching/hints', {'scores': scores, 'session_type': self.session.session_type.value, 'exchange_number': exchange_count, 'coaching_mode': 'training'})
                coaching_hints = hints_response.get('hints', [])
            except Exception:
                pass
        return {'exchange_number': exchange_count, 'response_text': ai_response['response_text'], 'audio_url': ai_response.get('audio_url'), 'question_type': ai_response.get('question_type', 'follow_up'), 'phase_suggestion': ai_response.get('phase_suggestion', 'continue'), 'dimension_scores': scores, 'coaching_hints': coaching_hints, 'difficulty_level': difficulty_update['new_difficulty']}

    async def process_audio(self, audio_base64: str) -> str:
        result = await self.speech_client.post('/speech/transcribe', {'audio': audio_base64})
        return result.get('transcript', '')

    async def _get_cached_resume_text(self) -> str:
        state = await self.redis.get_session_state(str(self.session.id))
        return state.get('resume_text', '') if state else ''

    async def execute_code(self, code: str, language: str) -> Dict[str, Any]:
        result = await self.code_executor_client.post('/execute', {'code': code, 'language': language, 'session_id': str(self.session.id)})
        return result

    async def end_session(self) -> Dict[str, Any]:
        session_id = str(self.session.id)
        self.session.status = SessionStatus.COMPLETING
        self.session.completed_at = datetime.utcnow()
        if self.session.started_at:
            started_naive = self.session.started_at.replace(tzinfo=None) if self.session.started_at.tzinfo else self.session.started_at
            completed_naive = self.session.completed_at.replace(tzinfo=None) if self.session.completed_at.tzinfo else self.session.completed_at
            self.session.duration_seconds = int((completed_naive - started_naive).total_seconds())
        state = await self.redis.get_session_state(session_id)
        if state:
            scores = state.get('dimension_scores', {})
            if isinstance(scores, str):
                scores = json.loads(scores)
            from shared.constants import DIMENSION_WEIGHTS
            weights = DIMENSION_WEIGHTS.get(self.session.session_type.value, DIMENSION_WEIGHTS['mixed'])
            if not scores:
                scores = {dim: 0.0 for dim in weights.keys()}
            self.session.dimension_scores = scores
            overall = sum((scores.get(dim, 0) * weight for dim, weight in weights.items()))
            self.session.overall_score = round(overall * 100, 2)
        self.session.status = SessionStatus.COMPLETED
        try:
            emo_summary = await self.emotion_client.post('/emotion/summary', {'session_id': session_id})
            self.session.emotional_summary = emo_summary
        except Exception as e:
            print(f'Failed to get emotional summary: {e}')
        self.db.commit()
        try:
            await self.report_client.post('/generate', {'session_id': session_id}, headers={'X-User-Id': str(self.session.user_id)})
            self.session.status = SessionStatus.REPORT_READY
            self.db.commit()
        except Exception as e:
            print(f'Failed to trigger report generation: {e}')
        try:
            await self.analytics_client.post(f'/gamification/award?session_id={session_id}', {}, headers={'X-User-Id': str(self.session.user_id)})
        except Exception as e:
            print(f'Failed to award Gamification XP: {e}')
        await self.redis.remove_user_active_session(str(self.session.user_id))
        return {'session_id': session_id, 'status': 'completed', 'overall_score': self.session.overall_score, 'dimension_scores': self.session.dimension_scores, 'duration_seconds': self.session.duration_seconds}