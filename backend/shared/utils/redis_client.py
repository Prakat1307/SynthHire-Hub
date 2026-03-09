
import redis.asyncio as aioredis
import json
from typing import Optional, Dict, Any

class RedisClient:
    def __init__(self, url: str):
        self.url = url
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        if self._client is None:
            self._client = await aioredis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    @property
    async def client(self) -> aioredis.Redis:
        return await self.connect()

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        c = await self.connect()
        state = await c.hgetall(f"session:state:{session_id}")
        if not state:
            return None
        
        for key in ["dimension_scores", "conversation_history", "speech_metrics"]:
            if key in state and isinstance(state[key], str):
                try:
                    state[key] = json.loads(state[key])
                except json.JSONDecodeError:
                    pass
        return state

    async def set_session_state(self, session_id: str, state: Dict[str, Any], ttl: int = 10800):
        c = await self.connect()
        
        serialized = {}
        for key, value in state.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = str(value)
        
        await c.hset(f"session:state:{session_id}", mapping=serialized)
        await c.expire(f"session:state:{session_id}", ttl)

    async def update_session_field(self, session_id: str, field: str, value: Any):
        c = await self.connect()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await c.hset(f"session:state:{session_id}", field, str(value))

    async def get_conversation_history(self, session_id: str) -> list:
        c = await self.connect()
        history = await c.lrange(f"session:history:{session_id}", 0, -1)
        return [json.loads(h) for h in history]

    async def append_conversation(self, session_id: str, message: Dict[str, Any]):
        c = await self.connect()
        await c.rpush(f"session:history:{session_id}", json.dumps(message))
        await c.ltrim(f"session:history:{session_id}", -20, -1)
        await c.expire(f"session:history:{session_id}", 10800)

    async def push_coaching_hint(self, session_id: str, hint: Dict[str, Any]):
        c = await self.connect()
        await c.lpush(f"session:hints:{session_id}", json.dumps(hint))
        await c.expire(f"session:hints:{session_id}", 10800)

    async def pop_coaching_hints(self, session_id: str, count: int = 5) -> list:
        c = await self.connect()
        hints = []
        for _ in range(count):
            hint = await c.rpop(f"session:hints:{session_id}")
            if hint:
                hints.append(json.loads(hint))
            else:
                break
        return hints

    async def set_user_active_session(self, user_id: str, session_id: str):
        c = await self.connect()
        await c.setex(f"user:active_session:{user_id}", 10800, session_id)

    async def get_user_active_session(self, user_id: str) -> Optional[str]:
        c = await self.connect()
        return await c.get(f"user:active_session:{user_id}")

    async def remove_user_active_session(self, user_id: str):
        c = await self.connect()
        await c.delete(f"user:active_session:{user_id}")

    async def is_token_blacklisted(self, token_hash: str) -> bool:
        c = await self.connect()
        return await c.sismember("blacklisted_tokens", token_hash) == 1

    async def blacklist_token(self, token_hash: str, ttl: int = 604800):
        c = await self.connect()
        await c.sadd("blacklisted_tokens", token_hash)
        await c.expire("blacklisted_tokens", ttl)
