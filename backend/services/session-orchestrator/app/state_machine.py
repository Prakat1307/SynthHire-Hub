from shared.utils import RedisClient
from shared.constants import DIMENSION_NAMES
from typing import Dict, Any, Optional
import json
from datetime import datetime
import enum

class SessionPhase(str, enum.Enum):
    CREATED = 'created'
    WAITING_FOR_QUESTION = 'waiting_for_question'
    CANDIDATE_TURN = 'candidate_turn'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    ERROR = 'error'

class SessionStateMachine:

    def __init__(self, redis_client: RedisClient, session_id: str):
        self.redis = redis_client
        self.session_id = session_id
        self.state_key = f'session:state:{session_id}'
        self.scores_key = f'session:scores:{session_id}'
        self.history_key = f'session:history:{session_id}'
        self.metrics_key = f'session:metrics:{session_id}'

    async def initialize(self, initial_state: Dict[str, Any]):
        await self.redis.set_session_state(self.session_id, {'current_phase': SessionPhase.CREATED.value, 'exchange_count': 0, 'started_at': datetime.utcnow().isoformat(), **initial_state})
        c = await self.redis.connect()
        initial_scores = {dim: '0.5' for dim in DIMENSION_NAMES}
        await c.hset(self.scores_key, mapping=initial_scores)
        await c.expire(self.scores_key, 10800)

    async def get_state(self) -> Optional[Dict[str, Any]]:
        return await self.redis.get_session_state(self.session_id)

    async def update_state(self, updates: Dict[str, Any]):
        state = await self.get_state()
        if state:
            state.update(updates)
            await self.redis.set_session_state(self.session_id, state)

    async def transition_to(self, phase: SessionPhase):
        await self.update_state({'current_phase': phase.value})

    async def increment_exchange(self):
        state = await self.get_state()
        new_count = int(state.get('exchange_count', 0)) + 1
        await self.update_state({'exchange_count': new_count})
        return new_count

    async def update_scores(self, scores: Dict[str, float]):
        c = await self.redis.connect()
        score_strings = {k: str(v) for k, v in scores.items()}
        await c.hset(self.scores_key, mapping=score_strings)

    async def get_scores(self) -> Dict[str, float]:
        c = await self.redis.connect()
        scores = await c.hgetall(self.scores_key)
        if not scores:
            return {dim: 0.5 for dim in DIMENSION_NAMES}
        return {k: float(v) for k, v in scores.items() if k in DIMENSION_NAMES}

    async def add_to_history(self, role: str, content: str):
        await self.redis.append_conversation(self.session_id, {'role': role, 'content': content, 'timestamp': datetime.utcnow().isoformat()})

    async def get_history(self) -> list:
        return await self.redis.get_conversation_history(self.session_id)

    async def cleanup(self):
        c = await self.redis.connect()
        await c.delete(self.state_key, self.scores_key, self.history_key, self.metrics_key)