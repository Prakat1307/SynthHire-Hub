from openai import AsyncOpenAI
from shared.constants import PERSONA_VECTORS
from typing import Dict, Any, Optional, List
import json

class GPT4Client:

    def __init__(self, api_key: str, model: str='gpt-4-turbo-preview'):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_chat_session(self, session_id: str, persona_type: str, session_type: str, company_slug: Optional[str]=None):
        persona_vector = PERSONA_VECTORS.get(persona_type, PERSONA_VECTORS['kind_mentor'])
        system_prompt = self._build_system_prompt(persona_type, session_type, company_slug, persona_vector)
        self.chat_sessions[session_id] = {'system_prompt': system_prompt, 'persona_type': persona_type, 'session_type': session_type, 'messages': []}

    def _build_system_prompt(self, persona_type: str, session_type: str, company_slug: Optional[str], persona_vector: Dict) -> str:
        base = f"You are an interviewer conducting a {session_type} interview.\n\nPersona: {persona_type.replace('_', ' ').title()}\nWarmth level: {persona_vector['warmth']}/1.0\nHint frequency: {persona_vector['hint_frequency']}/1.0  \nProbe depth: {persona_vector['probe_depth']}/1.0\nAmbiguity tolerance: {persona_vector['ambiguity_level']}/1.0\nPace pressure: {persona_vector['pace_pressure']}/1.0\n\n"
        if company_slug:
            base += f"\nYou are simulating an interview for {company_slug}. Ask questions and interact in a way typical of this company's interview process.\n"
        if session_type == 'coding':
            base += "\nFocus on:\n- Algorithmic thinking and problem-solving\n- Code correctness and optimization\n- Edge case handling\n- Communication of approach\n- Ability to handle clarifying questions\n\nAsk follow-up questions based on their performance. Probe deeper if they're doing well, provide hints if they're stuck (based on your hint frequency).\n"
        elif session_type == 'behavioral':
            base += '\nFocus on:\n- STAR format responses (Situation, Task, Action, Result)\n- Leadership and collaboration\n- Conflict resolution\n- Growth mindset\n- Cultural fit\n\nAsk probing follow-up questions. Look for concrete examples and results.\n'
        elif session_type == 'system_design':
            base += '\nFocus on:\n- Requirements gathering\n- High-level architecture\n- Scalability considerations\n- Trade-off discussions\n- Database/caching strategies\n\nGuide them through the design process. Ask clarifying questions about scale, constraints, and user requirements.\n'
        base += '\nKeep your responses conversational and natural.  You are voice-enabled, so speak naturally like a human interviewer.'
        return base

    async def send_message(self, session_id: str, user_message: str, context: Optional[Dict[str, Any]]=None) -> str:
        if session_id not in self.chat_sessions:
            raise ValueError(f'Chat session {session_id} not found')
        session = self.chat_sessions[session_id]
        messages = [{'role': 'system', 'content': session['system_prompt']}]
        messages.extend(session['messages'])
        if context:
            context_msg = f'\n\n[Context: {json.dumps(context)}]'
            user_message += context_msg
        messages.append({'role': 'user', 'content': user_message})
        response = await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.7, max_tokens=500)
        assistant_message = response.choices[0].message.content
        session['messages'].append({'role': 'user', 'content': user_message})
        session['messages'].append({'role': 'assistant', 'content': assistant_message})
        if len(session['messages']) > 20:
            session['messages'] = session['messages'][-20:]
        return assistant_message

    async def get_initial_question(self, session_id: str, difficulty: int=5) -> str:
        if session_id not in self.chat_sessions:
            raise ValueError(f'Chat session {session_id} not found')
        session = self.chat_sessions[session_id]
        session_type = session['session_type']
        prompt = f'Start the interview by asking a {session_type} question at difficulty level {difficulty}/10. Be concise and clear.'
        return await self.send_message(session_id, prompt)

    def close_session(self, session_id: str):
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]