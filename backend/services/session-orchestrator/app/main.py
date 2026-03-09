
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import io
import PyPDF2
from contextlib import asynccontextmanager
from typing import Optional, Dict
from uuid import UUID
import json
import uvicorn
import asyncio

from .config import settings
from .database import get_db, create_tables
from .service import SessionOrchestrator
from shared.auth.dependencies import init_jwt_handler, get_current_user_id, verify_ws_token
from shared.utils.redis_client import RedisClient
from shared.utils.mongodb_client import MongoDBClient
from shared.utils.http_client import ServiceClient
from shared.schemas.session import SessionCreate, SessionResponse, SessionListResponse, TemplateCreate, TemplateResponse
from shared.models.tables import InterviewSession, Company, InterviewTemplate

redis_client = RedisClient(settings.redis_url)
mongodb_client = MongoDBClient(settings.mongodb_url)
user_client = ServiceClient(settings.user_service_url)
speech_client = ServiceClient(settings.speech_pipeline_url)
assessment_client = ServiceClient(settings.assessment_engine_url)
coaching_client = ServiceClient(settings.coaching_engine_url)
report_client = ServiceClient(settings.report_generator_url)
code_executor_client = ServiceClient(settings.code_executor_url)
emotion_client = ServiceClient(settings.emotion_analysis_url)

analytics_client = ServiceClient(settings.analytics_service_url)

from pydantic import BaseModel
from uuid import UUID
class CompanyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    difficulty_level: str = "moderate"
    class Config:
        from_attributes = True

active_ws_sessions: Dict[str, SessionOrchestrator] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    create_tables()
    await redis_client.connect()
    
    if os.path.exists(settings.jwt_public_key_path):
        init_jwt_handler(settings.jwt_public_key_path, None, settings.jwt_algorithm)
    else:
        print(f"WARNING: JWT public key not found at {settings.jwt_public_key_path}. WebSocket auth will fail.")
        
    print(f"Session Orchestrator started on port {settings.service_port}")
    yield
    
    await redis_client.close()
    await mongodb_client.close()

app = FastAPI(
    title="SynthHire Session Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_orchestrator(db: Session = Depends(get_db)) -> SessionOrchestrator:
    return SessionOrchestrator(
        db=db,
        redis=redis_client,
        mongodb=mongodb_client,
        user_client=user_client,
        speech_client=speech_client,
        assessment_client=assessment_client,
        coaching_client=coaching_client,
        report_client=report_client,
        code_executor_client=code_executor_client,
        emotion_client=emotion_client,
        analytics_client=analytics_client
    )

@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    orchestrator: SessionOrchestrator = Depends(get_orchestrator)
):
    try:
        session = await orchestrator.create_session(user_id, data)
        return SessionResponse.from_orm(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sessions/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        text = ""
        for page in pdf_reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
                
        return {"filename": file.filename, "resume_text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    query = db.query(InterviewSession).filter(
        InterviewSession.user_id == UUID(user_id)
    ).order_by(InterviewSession.created_at.desc())
    
    total = query.count()
    sessions = query.offset(offset).limit(page_size).all()
    
    return SessionListResponse(
        sessions=[SessionResponse.from_orm(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size
    )

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == UUID(user_id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return SessionResponse.from_orm(session)

@app.get("/companies", response_model=list[CompanyResponse])
async def list_companies(db: Session = Depends(get_db)):

    companies = db.query(Company).all()
    return [CompanyResponse.from_orm(c) for c in companies]

@app.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    template = InterviewTemplate(
        role=data.role,
        round_type=data.round_type,
        experience_level=data.experience_level,
        persona_type=data.persona_type,
        system_prompt=data.system_prompt,
        persona_vector={},  
        difficulty_range=data.difficulty_range,
        duration_minutes=data.duration_minutes,
        is_public=data.is_public,
        creator_id=UUID(user_id)
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.from_orm(template)

@app.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):

    try:
        uuid_obj = UUID(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Template ID format")
        
    template = db.query(InterviewTemplate).filter(InterviewTemplate.id == uuid_obj).first()
    if not template:
        raise HTTPException(status_code=404, detail="Interview Template not found")
        
    return TemplateResponse.from_orm(template)

from pydantic import BaseModel
class AntiCheatSignal(BaseModel):
    signal_type: str
    description: Optional[str] = None
    level: str = "medium" 

@app.post("/sessions/{session_id}/anti-cheat")
async def report_anti_cheat_signal(
    session_id: UUID,
    signal: AntiCheatSignal,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    from shared.models.tables import TrustSignal, TrustLevel
    
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == UUID(user_id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    trust_level = TrustLevel.MEDIUM
    try:
        trust_level = TrustLevel(signal.level.lower())
    except ValueError:
        pass
        
    ts = TrustSignal(
        user_id=session.user_id,
        session_id=session.id,
        signal_type=signal.signal_type,
        description=signal.description,
        is_positive=False,
        trust_level=trust_level
    )
    db.add(ts)
    db.commit()
    
    return {"status": "logged", "signal_id": str(ts.id)}

@app.websocket("/sessions/ws/{session_id}")
async def websocket_interview(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
):

    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return
        
    await websocket.accept()
    
    from .database import SessionLocal
    db = SessionLocal()
    
    orchestrator = SessionOrchestrator(
        db=db,
        redis=redis_client,
        mongodb=mongodb_client,
        user_client=user_client,
        speech_client=speech_client,
        assessment_client=assessment_client,
        coaching_client=coaching_client,
        report_client=report_client,
        code_executor_client=code_executor_client,
        emotion_client=emotion_client,
        analytics_client=analytics_client
    )
    
    try:
        try:
            
            await orchestrator.load_session(session_id, user_id)
            active_ws_sessions[session_id] = orchestrator
            
            opening = await orchestrator.start_session()
            await websocket.send_json({
                "type": "session_started",
                "data": opening
            })
        except Exception as startup_err:
            print(f"WS STARTUP ERROR: {startup_err}")
            import traceback
            traceback.print_exc()
            await websocket.close(code=1011)
            return
        
        while True:
            raw = await websocket.receive_text()
            print(f"WS RAW RECEIVED: {raw[:100]}...") 
            message = json.loads(raw)
            msg_type = message.get("type")
            msg_data = message.get("data", {})
            
            if msg_type == "user_message":
                try:
                    response = await orchestrator.process_user_message(msg_data.get("text", ""))
                    
                    await websocket.send_json({
                        "type": "ai_response",
                        "data": {
                            "response_text": response["response_text"],
                            "audio_url": response.get("audio_url"),
                            "exchange_number": response["exchange_number"],
                            "question_type": response["question_type"],
                            "phase_suggestion": response["phase_suggestion"]
                        }
                    })
                    
                    await websocket.send_json({
                        "type": "score_update",
                        "data": {"scores": response["dimension_scores"]}
                    })
                    
                    if response.get("coaching_hints"):
                        await websocket.send_json({
                            "type": "coaching_hints",
                            "data": {"hints": response["coaching_hints"]}
                        })
                except Exception as e:
                    import traceback
                    with open("/app/crash.log", "w") as f:
                        f.write(traceback.format_exc())
                    raise e
            
            elif msg_type == "audio_chunk":
                print(f"WS [audio_chunk] received size={len(msg_data.get('audio', ''))} bytes")
                transcript = ""

                asyncio.create_task(emotion_client.post("/emotion/audio-chunk", {
                    "session_id": session_id,
                    "audio_base64": msg_data.get("audio", ""),
                    "timestamp_start": 0.0,
                    "timestamp_end": 5.0
                }))

                try:
                    transcript = await orchestrator.process_audio(msg_data.get("audio", ""))
                    print(f"WS [audio_chunk] transcript='{transcript[:120] if transcript else '(empty)'}' len={len(transcript)}")
                except Exception as e:
                    print(f"WS [audio_chunk] STT Error: {e}")
                    transcript = ""

                await websocket.send_json({
                    "type": "transcript",
                    "data": {"text": transcript}
                })

                if transcript:
                    asyncio.create_task(emotion_client.post("/emotion/transcript", {
                        "session_id": session_id,
                        "transcript": transcript,
                        "duration_seconds": 5.0
                    }))

                    try:
                        response = await orchestrator.process_user_message(transcript)
                        await websocket.send_json({
                            "type": "ai_response",
                            "data": {
                                "response_text": response["response_text"],
                                "audio_url": response.get("audio_url"),
                                "exchange_number": response["exchange_number"],
                                "question_type": response["question_type"],
                                "phase_suggestion": response["phase_suggestion"]
                            }
                        })
                        await websocket.send_json({
                            "type": "score_update",
                            "data": {"scores": response["dimension_scores"]}
                        })
                    except Exception as e:
                        print(f"WS [audio_chunk] AI response error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "AI failed to respond to transcript", "code": "AI_ERROR"}
                        })
                else:
                    print(f"WS [audio_chunk] Empty transcript — sending error response")

            elif msg_type == "code_submit":
                code_text = msg_data.get("code", "")
                language = msg_data.get("language", "python")
                result = await orchestrator.execute_code(code_text, language)
                
                await websocket.send_json({
                    "type": "code_result",
                    "data": result
                })
                
                try:
                    ai_prompt = f"I have run the following {language} code:\n\n```\n{code_text}\n```\n\nThe output was:\n{result.get('stdout')}\n{result.get('stderr')}\n\nPlease review my code."
                    ai_response = await orchestrator.process_user_message(ai_prompt)
                    
                    await websocket.send_json({
                        "type": "ai_response",
                        "data": {
                            "response_text": ai_response["response_text"],
                            "audio_url": ai_response.get("audio_url"),
                            "exchange_number": ai_response["exchange_number"],
                            "question_type": ai_response.get("question_type"),
                            "phase_suggestion": ai_response.get("phase_suggestion")
                        }
                    })
                    
                    await websocket.send_json({
                        "type": "score_update",
                        "data": {"scores": ai_response["dimension_scores"]}
                    })
                    
                    if ai_response.get("coaching_hints"):
                        await websocket.send_json({
                            "type": "coaching_hints",
                            "data": {"hints": ai_response["coaching_hints"]}
                        })
                except Exception as e:
                    print(f"Error processing code for AI response: {e}")
            
            elif msg_type == "video_frame":
                
                asyncio.create_task(emotion_client.post("/emotion/video-frame", {
                    "session_id": session_id,
                    "image": msg_data.get("image", "")
                }))
            
            elif msg_type == "end_session":
                result = await orchestrator.end_session()
                await websocket.send_json({
                    "type": "session_ended",
                    "data": result
                })
                break
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        except Exception:
            pass
            
    finally:
        if session_id in active_ws_sessions:
            del active_ws_sessions[session_id]
        db.close()

class AnalyseRequest(BaseModel):
    transcript: Optional[str] = None
    messages: Optional[list] = None
    session_type: Optional[str] = "mixed"
    target_role: Optional[str] = "Software Engineer"

@app.post("/sessions/{session_id}/analyse")
async def analyse_session(
    session_id: str,
    data: AnalyseRequest = AnalyseRequest(),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    import google.generativeai as genai_local
    import os as _os

    transcript_text = data.transcript or ""
    if not transcript_text and data.messages:
        for msg in data.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            transcript_text += f"{role}: {content}\n"

    print(f"[analyse] session={session_id} transcript_len={len(transcript_text)}")

    fallback_scores = {
        "communication_clarity": 6,
        "technical_accuracy": 6,
        "problem_solving": 6,
        "confidence": 6,
        "relevance": 6,
        "grammar": 7,
        "question_handling": 6,
        "overall_score": 60,
        "strengths": ["Participated in the interview session"],
        "improvement_areas": ["More interview data needed for detailed analysis"],
        "narrative": "Analysis could not be completed due to insufficient data."
    }

    if not transcript_text.strip():
        return {
            "status": "fallback",
            "scores": fallback_scores,
            "message": "Empty transcript — returning default scores"
        }

    raw = ""
    try:
        gemini_key = _os.getenv("GEMINI_API_KEY_1") or _os.getenv("GEMINI_API_KEY") or ""
        if gemini_key and "placeholder" not in gemini_key:
            genai_local.configure(api_key=gemini_key)

        prompt = f"""You are an expert interview evaluator. Analyse the following interview transcript and return ONLY a JSON object.

Transcript:
\"\"\"
{transcript_text[:6000]}
\"\"\"

Role: {data.target_role}
Interview Type: {data.session_type}

Return exactly this JSON structure (scores 0-10, overall 0-100):
{ 
  "communication_clarity": <int 0-10>,
  "technical_accuracy": <int 0-10>,
  "problem_solving": <int 0-10>,
  "confidence": <int 0-10>,
  "relevance": <int 0-10>,
  "grammar": <int 0-10>,
  "question_handling": <int 0-10>,
  "overall_score": <int 0-100>,
  "strengths": ["...", "..."],
  "improvement_areas": ["...", "..."],
  "narrative": "3-sentence coaching summary"
} """

        model = genai_local.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        scores = json.loads(raw)
        return {"status": "success", "scores": scores}

    except json.JSONDecodeError:
        return {"status": "partial", "scores": fallback_scores, "raw": raw}
    except Exception as e:
        print(f"[analyse] Gemini error: {e}")
        return {"status": "fallback", "scores": fallback_scores, "error": str(e)}

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": settings.service_name, 
        "port": settings.service_port,
        "active_sessions": len(active_ws_sessions)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)