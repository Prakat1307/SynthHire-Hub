
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import base64
import io
import numpy as np
import uvicorn
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
from PIL import Image

from shared.config.base import BaseServiceSettings
from ml.models.emotion_analyzer import EmotionAnalysisPipeline, FacialEmotionAnalyzer, AudioProsodyAnalyzer

class EmotionSettings(BaseServiceSettings):
    service_name: str = "emotion-analysis"
    service_port: int = 8007

settings = EmotionSettings()

session_pipelines: Dict[str, EmotionAnalysisPipeline] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.service_name} started on port {settings.service_port}")
    yield
    session_pipelines.clear()

app = FastAPI(
    title="SynthHire Emotion Analysis",
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

class VideoFrameRequest(BaseModel):
    session_id: str
    frame_base64: str
    timestamp: float

class AudioChunkRequest(BaseModel):
    session_id: str
    audio_base64: str
    timestamp_start: float
    timestamp_end: float

class TranscriptRequest(BaseModel):
    session_id: str
    transcript: str
    duration_seconds: float = Field(..., gt=0)

class SessionSummaryRequest(BaseModel):
    session_id: str

def get_or_create_pipeline(session_id: str) -> EmotionAnalysisPipeline:

    if session_id not in session_pipelines:
        session_pipelines[session_id] = EmotionAnalysisPipeline()
    return session_pipelines[session_id]

def decode_frame(frame_base64: str) -> np.ndarray:

    try:
        
        frame_bytes = base64.b64decode(frame_base64)
        
        image = Image.open(io.BytesIO(frame_bytes))
        frame_array = np.array(image)
        
        if len(frame_array.shape) == 2:
            
            frame_array = np.stack([frame_array] * 3, axis=-1)
        elif frame_array.shape[2] == 4:
            
            frame_array = frame_array[:, :, :3]
        elif frame_array.shape[2] == 1:
            
            frame_array = np.concatenate([frame_array] * 3, axis=2)
            
        return frame_array
    except Exception as e:
        raise ValueError(f"Failed to decode frame: {e}")

@app.post("/emotion/video-frame")
async def process_video_frame(request: VideoFrameRequest):

    pipeline = get_or_create_pipeline(request.session_id)

    try:
        
        frame_rgb = decode_frame(request.frame_base64)

        pipeline.process_video_frame(frame_rgb, request.timestamp)

        latest = pipeline.emotion_frames[-1] if pipeline.emotion_frames else None
        if latest:
            return {
                "status": "processed",
                "confidence": latest.confidence_composite,
                "dominant_emotion": latest.dominant_emotion,
                "gaze_score": latest.gaze_score,
            }
        return {"status": "processed"}

    except ValueError as e:
        return {"status": "error", "detail": str(e)}
    except Exception as e:
        return {"status": "error", "detail": f"Processing failed: {str(e)}"}

@app.post("/emotion/audio-chunk")
async def process_audio_chunk(request: AudioChunkRequest):

    pipeline = get_or_create_pipeline(request.session_id)

    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        pipeline.process_audio_chunk(audio_bytes, request.timestamp_start, request.timestamp_end)

        latest = pipeline.prosody_chunks[-1] if pipeline.prosody_chunks else None
        if latest:
            return {
                "status": "processed",
                "confidence": latest.confidence_score,
                "speech_rate_wpm": latest.speech_rate_wpm,
                "pause_ratio": latest.pause_ratio,
            }
        return {"status": "processed"}

    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/emotion/transcript")
async def process_transcript(request: TranscriptRequest):

    pipeline = get_or_create_pipeline(request.session_id)
    result = pipeline.process_transcript(request.transcript, request.duration_seconds)
    return result

@app.post("/emotion/behavioral-scores")
async def get_behavioral_scores(request: SessionSummaryRequest):

    pipeline = session_pipelines.get(request.session_id)
    if not pipeline:
        return {"scores": {dim: 0.5 for dim in [
            "technical_correctness", "problem_decomposition",
            "communication_clarity", "handling_ambiguity",
            "edge_case_awareness", "time_management",
            "collaborative_signals", "growth_mindset",
        ]}}

    return {"scores": pipeline.get_behavioral_scores()}

@app.post("/emotion/summary")
async def get_emotion_summary(request: SessionSummaryRequest):

    pipeline = session_pipelines.get(request.session_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="No emotion data for this session")

    summary = pipeline.get_summary()
    return {
        "avg_confidence": summary.avg_confidence,
        "confidence_trend": summary.confidence_trend,
        "stress_peaks": summary.stress_peaks,
        "total_filler_words": summary.total_filler_words,
        "avg_eye_contact": summary.avg_eye_contact,
        "avg_speech_rate_wpm": summary.avg_speech_rate_wpm,
        "emotion_distribution": summary.emotion_distribution,
    }

@app.post("/emotion/cleanup")
async def cleanup_session(request: SessionSummaryRequest):

    if request.session_id in session_pipelines:
        del session_pipelines[request.session_id]
    return {"status": "cleaned"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "port": settings.service_port,
        "active_sessions": len(session_pipelines),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)