
import sys
import os
import base64
import io
import asyncio
import aiohttp
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import openai
import google.generativeai as genai
import edge_tts
from groq import Groq

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from .config import settings
from shared.constants import EDGE_TTS_VOICES

GEMINI_API_KEYS = [k for k in [
    settings.gemini_api_key,
    settings.gemini_api_key_2,
    settings.gemini_api_key_3,
    settings.gemini_api_key_4,
] if k and "placeholder" not in k]

_current_gemini_key_index = 0

def get_next_gemini_key():

    global _current_gemini_key_index
    if not GEMINI_API_KEYS:
        return None
    _current_gemini_key_index = (_current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
    key = GEMINI_API_KEYS[_current_gemini_key_index]
    genai.configure(api_key=key)
    print(f"Rotated to Gemini API key index {_current_gemini_key_index}")
    return key

if GEMINI_API_KEYS:
    genai.configure(api_key=GEMINI_API_KEYS[0])

if settings.openai_api_key:
    openai.api_key = settings.openai_api_key

groq_client = None
if settings.groq_api_key and "placeholder" not in settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key)
    print(f"Groq Whisper STT initialized")

print("GROQ KEY LOADED:", bool(os.getenv("GROQ_API_KEY")))

app = FastAPI(title="SynthHire Speech & AI Pipeline", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    system_prompt: str
    user_message: str
    conversation_history: List[Dict[str, str]] = []
    persona_type: str = "kind_mentor"
    generate_audio: bool = False
    difficulty_action: str = "continue"

class GenerateResponse(BaseModel):
    response_text: str
    audio_url: Optional[str] = None
    question_type: str = "follow_up"
    phase_suggestion: str = "continue"

class TranscribeRequest(BaseModel):
    audio: str  

class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float = 1.0
    error: Optional[str] = None  

class WhiteboardRequest(BaseModel):
    content: str
    mode: str = "explain"  
    session_id: Optional[str] = None

class WhiteboardResponse(BaseModel):
    response: str
    format: str = "text"  
    timestamp: str

async def generate_text_ollama(prompt: str, model: str) -> str:

    url = f"{settings.ollama_base_url}/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 256
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Ollama API Error: {error}")
            result = await resp.json()
            return result.get("response", "").strip()

async def generate_text_gemini(prompt: str) -> str:

    last_error = None
    
    for attempt in range(len(GEMINI_API_KEYS)):
        try:
            model = genai.GenerativeModel(settings.gemini_model)
            completion = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            return completion.text
        except Exception as e:
            error_str = str(e)
            last_error = e
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                print(f"Gemini key {_current_gemini_key_index} hit rate limit, rotating...")
                get_next_gemini_key()
                continue
            else:
                print(f"Gemini Error: {e}")
                raise e
    
    raise last_error or Exception("All Gemini API keys exhausted")

async def generate_text_openai(system_prompt: str, user_message: str, history: List[Dict]) -> str:

    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Generation Error: {e}")
        return ""

@app.post("/ai/generate", response_model=GenerateResponse)
async def generate_response(req: GenerateRequest):

    try:
        response_text = ""
        
        if settings.use_local_ai:
            try:
                ollama_prompt = f"System: {req.system_prompt}\n"
                for msg in req.conversation_history:
                    ollama_prompt += f"{msg['role']}: {msg['content']}\n"
                ollama_prompt += f"user: {req.user_message}\n\nPlease respond as the interviewer."
                
                response_text = await generate_text_ollama(ollama_prompt, settings.ollama_model)
                print(f"Generated response using Local AI ({settings.ollama_model})")
            except Exception as e:
                print(f"Local AI (Ollama) Generation Error: {e}. Falling back...")

        if not response_text and GEMINI_API_KEYS:
            try:
                full_prompt = f"System: {req.system_prompt}\n"
                for msg in req.conversation_history:
                    full_prompt += f"{msg['role']}: {msg['content']}\n"
                full_prompt += f"user: {req.user_message}\n"
                
                response_text = await generate_text_gemini(full_prompt)
                print(f"Generated response using Gemini ({settings.gemini_model})")
            except Exception as e:
                print(f"Gemini Generation Error: {e}")
                response_text = ""

        if not response_text and settings.openai_api_key and "placeholder" not in settings.openai_api_key.lower():
            print("Falling back to OpenAI (gpt-4o)...")
            response_text = await generate_text_openai(req.system_prompt, req.user_message, req.conversation_history)
            if response_text:
                print("Generated response using OpenAI (gpt-4o)")

        if not response_text:
            print("CRITICAL: All AI providers failed. Using mandatory safety response.")
            response_text = "I apologize, but I'm having a brief connection issue. To ensure we stay on track, could you tell me a bit more about your recent project experience?"

        audio_url = None
        if req.generate_audio and response_text:
            try:
                
                edge_voice = EDGE_TTS_VOICES.get(req.persona_type, settings.tts_voice)
                print(f"Generating audio using Edge TTS ({edge_voice})...")
                
                audio_content = await generate_speech_edge_tts(response_text, edge_voice)
                audio_b64 = base64.b64encode(audio_content).decode('utf-8')
                audio_url = f"data:audio/mpeg;base64,{audio_b64}"
                print(f"Generated audio successfully (base64 size: {len(audio_b64)})")
            except Exception as e:
                print(f"Edge TTS Error: {e}")
        
        return GenerateResponse(
            response_text=response_text,
            audio_url=audio_url,
            question_type="follow_up",
            phase_suggestion="continue"
        )
        
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return GenerateResponse(
            response_text="I apologize, but I'm having trouble retrieving my thoughts right now. Could you repeat that?",
            question_type="error"
        )

@app.post("/speech/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):

    try:
        
        audio_data = base64.b64decode(req.audio)

        if not groq_client:
            return TranscribeResponse(
                transcript="",
                error="Groq API key not configured. Set GROQ_API_KEY in .env"
            )

        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.webm"

        try:
            
            result = await asyncio.to_thread(
                groq_client.audio.transcriptions.create,
                model="whisper-large-v3",
                file=audio_file,
                language="en"
            )
            transcript = result.text.strip() if result.text else ""
            print(f"Groq Whisper transcribed: '{transcript[:80]}'")
            return TranscribeResponse(transcript=transcript)

        except Exception as direct_err:
            print(f"STT direct attempt failed: {direct_err} — trying pydub wav conversion")
            
            try:
                from pydub import AudioSegment
                audio_file.seek(0)
                segment = AudioSegment.from_file(audio_file, format="webm")
                wav_buf = io.BytesIO()
                segment.export(wav_buf, format="wav")
                wav_buf.seek(0)
                wav_buf.name = "audio.wav"

                result = await asyncio.to_thread(
                    groq_client.audio.transcriptions.create,
                    model="whisper-large-v3",
                    file=wav_buf,
                    language="en"
                )
                transcript = result.text.strip() if result.text else ""
                print(f"Groq Whisper (wav fallback) transcribed: '{transcript[:80]}'")
                return TranscribeResponse(transcript=transcript)

            except Exception as wav_err:
                print(f"STT wav conversion also failed: {wav_err}")
                return TranscribeResponse(
                    transcript="",
                    error=f"Transcription failed: {str(wav_err)}"
                )

    except Exception as e:
        print(f"STT outer error: {e}")
        
        return TranscribeResponse(transcript="", error=str(e))

async def generate_speech_edge_tts(text: str, voice: str) -> bytes:

    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "speech-pipeline",
        "stt_provider": "groq-whisper",
        "tts_provider": "edge-tts",
        "groq_configured": groq_client is not None,
        "gemini_keys": len(GEMINI_API_KEYS),
    }

_WHITEBOARD_MODE_PROMPTS = {
    "explain": "Explain the following in a clear, concise way suitable for a technical interview. Use plain language and avoid unnecessary jargon. If relevant, give a brief example.",
    "code": "Provide a clean, working code solution for the following. Add brief inline comments. Return ONLY the code block with no extra prose.",
    "hints": "Give 3-5 progressive hints (from small nudge to bigger hint) to help solve the following problem without giving away the direct answer.",
    "solution": "Provide a complete, step-by-step solution for the following problem. Include: 1) approach/algorithm, 2) code implementation, 3) time/space complexity analysis."
}

@app.post("/whiteboard/ask", response_model=WhiteboardResponse)
async def whiteboard_ask(req: WhiteboardRequest):

    try:
        mode_prefix = _WHITEBOARD_MODE_PROMPTS.get(req.mode, _WHITEBOARD_MODE_PROMPTS["explain"])
        full_prompt = f"{mode_prefix}\n\n---\n\n{req.content}"

        ai_text = ""

        if GEMINI_API_KEYS:
            try:
                ai_text = await generate_text_gemini(full_prompt)
            except Exception as e:
                print(f"Whiteboard Gemini error: {e}")

        if not ai_text and settings.openai_api_key and "placeholder" not in settings.openai_api_key.lower():
            try:
                ai_text = await generate_text_openai(
                    "You are a technical interview coach helping a candidate.",
                    full_prompt,
                    []
                )
            except Exception as e:
                print(f"Whiteboard OpenAI error: {e}")

        if not ai_text:
            ai_text = "AI is temporarily unavailable. Please try again shortly."

        fmt = "code" if req.mode == "code" or ai_text.strip().startswith("```") else "text"
        
        if fmt == "code":
            ai_text = ai_text.replace("```python", "").replace("```javascript", "").replace("```", "").strip()

        return WhiteboardResponse(
            response=ai_text,
            format=fmt,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        print(f"Whiteboard endpoint error: {e}")
        return WhiteboardResponse(
            response="AI is temporarily unavailable. Please try again.",
            format="text",
            timestamp=datetime.utcnow().isoformat()
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)