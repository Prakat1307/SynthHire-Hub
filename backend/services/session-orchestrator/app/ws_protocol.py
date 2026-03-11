import asyncio
import json
import uuid
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from fastapi import WebSocket

class WSChannel(str, Enum):
    CONTROL = 'control'
    INTERVIEW = 'interview'
    COACHING = 'coaching'
    CODE = 'code'

@dataclass
class WSMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    seq: int = 0
    type: str = ''
    channel: str = WSChannel.INTERVIEW
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    ack_required: bool = False

    def to_dict(self) -> dict:
        return {'id': self.id, 'seq': self.seq, 'type': self.type, 'channel': self.channel, 'timestamp': self.timestamp, 'data': self.data, 'ack_required': self.ack_required}

    @classmethod
    def from_dict(cls, data: dict) -> 'WSMessage':
        return cls(id=data.get('id', str(uuid.uuid4())), seq=data.get('seq', 0), type=data.get('type', ''), channel=data.get('channel', WSChannel.INTERVIEW), timestamp=data.get('timestamp', time.time()), data=data.get('data', {}), ack_required=data.get('ack_required', False))

class WSConnectionManager:

    def __init__(self, websocket: WebSocket, session_id: str):
        self.ws = websocket
        self.session_id = session_id
        self.send_seq = 0
        self.recv_seq = 0
        self.pending_acks: Dict[str, WSMessage] = {}
        self.message_buffer: deque[WSMessage] = deque(maxlen=100)
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.ack_timeout_task: Optional[asyncio.Task] = None
        self.connected = True
        self.last_activity = time.time()

    async def start(self):
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.ack_timeout_task = asyncio.create_task(self._ack_timeout_loop())

    async def stop(self):
        self.connected = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.ack_timeout_task:
            self.ack_timeout_task.cancel()

    async def send(self, msg_type: str, data: Dict[str, Any], channel: str=WSChannel.INTERVIEW, ack_required: bool=False) -> WSMessage:
        self.send_seq += 1
        msg = WSMessage(seq=self.send_seq, type=msg_type, channel=channel, data=data, ack_required=ack_required)
        if ack_required:
            self.pending_acks[msg.id] = msg
        self.message_buffer.append(msg)
        try:
            await self.ws.send_json(msg.to_dict())
            self.last_activity = time.time()
        except Exception as e:
            print(f'WS send error: {e}')
            self.connected = False
        return msg

    async def receive(self) -> Optional[WSMessage]:
        try:
            raw = await self.ws.receive_text()
            data = json.loads(raw)
            msg = WSMessage.from_dict(data)
            self.last_activity = time.time()
            if msg.type == 'ack':
                ack_id = msg.data.get('ack_id') or data.get('ack_id')
                if ack_id and ack_id in self.pending_acks:
                    del self.pending_acks[ack_id]
                return None
            if msg.type == 'pong':
                return None
            self.recv_seq = msg.seq
            if msg.ack_required:
                await self.ws.send_json({'type': 'ack', 'ack_id': msg.id, 'seq': self.send_seq + 1})
            return msg
        except Exception as e:
            print(f'WS receive error: {e}')
            self.connected = False
            return None

    async def send_score_update(self, scores: Dict[str, float]):
        await self.send('score_update', {'scores': scores}, WSChannel.COACHING)

    async def send_coaching_hint(self, hints: List[Dict]):
        await self.send('coaching_hints', {'hints': hints}, WSChannel.COACHING)

    async def send_ai_response(self, response_text: str, audio_url: str=None, **kwargs):
        await self.send('ai_response', {'response_text': response_text, 'audio_url': audio_url, **kwargs}, WSChannel.INTERVIEW, ack_required=True)

    async def send_phase_change(self, phase: str):
        await self.send('phase_change', {'phase': phase}, WSChannel.CONTROL)

    async def send_error(self, message: str, code: str='UNKNOWN'):
        await self.send('error', {'message': message, 'code': code}, WSChannel.CONTROL)

    async def _heartbeat_loop(self):
        while self.connected:
            try:
                await asyncio.sleep(30)
                if self.connected:
                    await self.ws.send_json({'type': 'ping', 'timestamp': time.time()})
            except Exception:
                self.connected = False
                break

    async def _ack_timeout_loop(self):
        while self.connected:
            try:
                await asyncio.sleep(10)
                now = time.time()
                timed_out = []
                for msg_id, msg in self.pending_acks.items():
                    if now - msg.timestamp > 30:
                        timed_out.append(msg_id)
                for msg_id in timed_out:
                    msg = self.pending_acks.pop(msg_id)
                    try:
                        msg.timestamp = time.time()
                        msg.id = str(uuid.uuid4())
                        self.pending_acks[msg.id] = msg
                        await self.ws.send_json(msg.to_dict())
                    except Exception:
                        pass
            except Exception:
                break