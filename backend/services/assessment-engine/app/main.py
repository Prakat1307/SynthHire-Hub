
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import openai
import json
import numpy as np
import uvicorn
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from shared.config.base import BaseServiceSettings
from shared.constants import DIMENSION_NAMES

class AssessmentSettings(BaseServiceSettings):
    service_name: str = "assessment-engine"
    service_port: int = 8006
    deberta_model_path: str = ""
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_gpu: bool = False
    openai_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""

settings = AssessmentSettings()
openai.api_key = settings.openai_api_key

GEMINI_API_KEYS = [k for k in [
    settings.gemini_api_key,
    settings.gemini_api_key_2,
    settings.gemini_api_key_3,
    settings.gemini_api_key_4,
] if k and "placeholder" not in k]

_current_gemini_key_idx = 0

def rotate_gemini_key():

    global _current_gemini_key_idx
    import google.generativeai as genai
    if not GEMINI_API_KEYS:
        return None
    _current_gemini_key_idx = (_current_gemini_key_idx + 1) % len(GEMINI_API_KEYS)
    key = GEMINI_API_KEYS[_current_gemini_key_idx]
    genai.configure(api_key=key)
    print(f"Assessment: Rotated to Gemini key index {_current_gemini_key_idx}")
    return key

if GEMINI_API_KEYS:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEYS[0])

ml_pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_pipeline
    print(f"Initializing {settings.service_name}...")

    try:
        from ml.serving.inference import MLInferencePipeline
        ml_pipeline = MLInferencePipeline(
            deberta_model_path=settings.deberta_model_path if settings.deberta_model_path else None,
            embedding_model_name=settings.embedding_model_name,
            use_gpu=settings.use_gpu,
        )
        print("✅ ML Pipeline loaded")
    except Exception as e:
        print(f"⚠️ ML Pipeline partially loaded: {e}")

    print(f"{settings.service_name} started on port {settings.service_port}")
    yield

app = FastAPI(
    title="SynthHire Assessment Engine",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AssessRequest(BaseModel):
    session_id: str
    exchange_number: int
    response_text: str
    question_text: Optional[str] = None
    ideal_responses: Optional[List[str]] = None
    session_type: str = "coding"
    behavioral_scores: Optional[Dict[str, float]] = None

class AssessResponse(BaseModel):
    scores: Dict[str, float]
    deberta_scores: Optional[Dict[str, float]] = None
    gpt4o_scores: Optional[Dict[str, float]] = None
    embedding_similarity: Optional[float] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)

class SessionAggregateRequest(BaseModel):
    exchange_scores: List[Dict[str, float]]
    session_type: str = "coding"

class SessionAggregateResponse(BaseModel):
    dimension_scores: Dict[str, float]
    overall_score: float

GPT4O_ASSESSMENT_PROMPT = """You are an expert interview assessor. Evaluate this candidate response across 10 dimensions.

Interview Type: {session_type}
{question_context}

Candidate Response:
"{response_text}"

Rate each dimension from 0.0 to 1.0:
1. technical_correctness — Is the answer technically accurate?
2. problem_decomposition — Did they break down the problem?
3. communication_clarity — Was explanation clear and structured?
4. handling_ambiguity — Did they clarify or handle vagueness?
5. edge_case_awareness — Did they consider edge cases?
6. time_management — Good pacing for exchange #{exchange_number}?
7. collaborative_signals — Collaborative engagement?
8. growth_mindset — Openness to feedback/learning?
9. semantic_quality — Does the semantic meaning match the ideal model answer?
10. problem_structure — Clear rubric-based structure (plan -> implementation -> test)?

Respond ONLY with JSON: {{"technical_correctness": 0.75, "problem_decomposition": 0.80, ...}}"""

async def get_gpt4o_assessment(
    response_text: str,
    session_type: str,
    exchange_number: int,
    question_text: str = None,
) -> Dict[str, float]:

    question_context = f"Question: {question_text}" if question_text else ""

    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert interview assessor. Respond ONLY with valid JSON."},
                {"role": "user", "content": GPT4O_ASSESSMENT_PROMPT.format(
                    session_type=session_type,
                    question_context=question_context,
                    response_text=response_text,
                    exchange_number=exchange_number,
                )},
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        scores = json.loads(response.choices[0].message.content)

        validated = {}
        for dim in DIMENSION_NAMES:
            val = scores.get(dim, 0.5)
            validated[dim] = max(0.0, min(1.0, float(val)))

        return validated

    except Exception as e:
        print(f"GPT-4o assessment error: {e}")
        return {dim: 0.5 for dim in DIMENSION_NAMES}

async def get_local_assessment(
    response_text: str,
    session_type: str,
    exchange_number: int,
    question_text: str = None,
) -> Dict[str, float]:

    question_context = f"Question: {question_text}" if question_text else ""
    url = f"{settings.ollama_base_url}/api/generate"
    
    prompt = f"""You are an expert interview assessor. Evaluate this candidate response across 10 dimensions.

Interview Type: {session_type}
{question_context}

Candidate Response:
"{response_text}"

Rate each dimension from 0.0 to 1.0:
1. technical_correctness
2. problem_decomposition
3. communication_clarity
4. handling_ambiguity
5. edge_case_awareness
6. time_management
7. collaborative_signals
8. growth_mindset
9. semantic_quality
10. problem_structure

Respond ONLY with valid JSON: {{ "technical_correctness": 0.75, ...}} """

    try:
        data = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3.0)) as session:
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama API Error: {resp.status}")
                result = await resp.json()
                scores = json.loads(result.get("response", "{}"))
                
                validated = {}
                for dim in DIMENSION_NAMES:
                    val = scores.get(dim, 0.5)
                    validated[dim] = max(0.0, min(1.0, float(val)))
                return validated
    except Exception as e:
        print(f"Local assessment error: {e}")
        return {dim: 0.5 for dim in DIMENSION_NAMES}

async def get_gemini_assessment(
    response_text: str,
    session_type: str,
    exchange_number: int,
    question_text: str = None,
) -> Dict[str, float]:

    question_context = f"Question: {question_text}" if question_text else ""
    
    prompt = f"""You are an expert interview assessor. Evaluate this candidate response across 10 dimensions.

Interview Type: {session_type}
{question_context}

Candidate Response:
"{response_text}"

Rate each dimension from 0.0 to 1.0:
1. technical_correctness
2. problem_decomposition
3. communication_clarity
4. handling_ambiguity
5. edge_case_awareness
6. time_management
7. collaborative_signals
8. growth_mindset
9. semantic_quality
10. problem_structure

Respond ONLY with valid JSON: {{ "technical_correctness": 0.75, ...}} """
    
    last_error = None
    for attempt in range(len(GEMINI_API_KEYS)):
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(settings.gemini_model)
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            scores = json.loads(text)

            validated = {}
            for dim in DIMENSION_NAMES:
                val = scores.get(dim, 0.5)
                validated[dim] = max(0.0, min(1.0, float(val)))

            return validated

        except Exception as e:
            last_error = e
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                print(f"Assessment Gemini key {_current_gemini_key_idx} hit rate limit, rotating...")
                rotate_gemini_key()
                continue
            else:
                print(f"Gemini assessment error: {e}")
                return {dim: 0.5 for dim in DIMENSION_NAMES}
    
    print(f"All Gemini keys exhausted in assessment: {last_error}")
    return {dim: 0.5 for dim in DIMENSION_NAMES}

@app.post("/assess", response_model=AssessResponse)
async def assess_response(request: AssessRequest):

    ai_scores = None
    
    if settings.use_local_ai:
        ai_scores = await get_local_assessment(
            response_text=request.response_text,
            session_type=request.session_type,
            exchange_number=request.exchange_number,
            question_text=request.question_text,
        )
        if ai_scores and any(v != 0.5 for v in ai_scores.values()):
            print(f"Used Local AI assessment scores ({settings.ollama_model})")
        else:
            ai_scores = None 

    if not ai_scores and GEMINI_API_KEYS:
        ai_scores = await get_gemini_assessment(
            response_text=request.response_text,
            session_type=request.session_type,
            exchange_number=request.exchange_number,
            question_text=request.question_text,
        )
    
    if not ai_scores and settings.openai_api_key and "placeholder" not in settings.openai_api_key:
        ai_scores = await get_gpt4o_assessment(
            response_text=request.response_text,
            session_type=request.session_type,
            exchange_number=request.exchange_number,
            question_text=request.question_text,
        )
        
    if not ai_scores:
        
        ai_scores = {dim: 0.5 for dim in DIMENSION_NAMES}

    if ml_pipeline:
        result = ml_pipeline.score_response(
            candidate_response=request.response_text,
            gpt4o_scores=ai_scores, 
            ideal_responses=request.ideal_responses,
            behavioral_scores=request.behavioral_scores,
        )
        final_scores = result["ensemble_scores"]
        deberta_scores = result.get("deberta_scores")
        embedding_sim = result.get("embedding_similarity", 0.5)
        confidence = 0.85
    else:
        
        final_scores = ai_scores
        deberta_scores = None
        embedding_sim = None
        confidence = 0.6

    return AssessResponse(
        scores=final_scores,
        deberta_scores=deberta_scores,
        gpt4o_scores=ai_scores, 
        embedding_similarity=embedding_sim,
        confidence=confidence,
    )

@app.post("/assess/aggregate", response_model=SessionAggregateResponse)
async def aggregate_session_scores(request: SessionAggregateRequest):

    if ml_pipeline:
        result = ml_pipeline.aggregate_session(request.exchange_scores, request.session_type)
    else:
        
        session_scores = {}
        if not request.exchange_scores:
            session_scores = {dim: 0.5 for dim in DIMENSION_NAMES}
            overall = 0.5
        else:
            for dim in DIMENSION_NAMES:
                scores_for_dim = [ex.get(dim, 0.5) for ex in request.exchange_scores if dim in ex]
                session_scores[dim] = sum(scores_for_dim) / len(scores_for_dim) if scores_for_dim else 0.5
            
            from shared.constants import DIMENSION_WEIGHTS
            weights = DIMENSION_WEIGHTS.get(request.session_type, DIMENSION_WEIGHTS["coding"])
            overall = 0.0
            total_w = 0.0
            for dim, w in weights.items():
                overall += session_scores.get(dim, 0.5) * w
                total_w += w
            if total_w > 0:
                overall /= total_w
                
        result = {"dimension_scores": session_scores, "overall_score": round(overall, 2)}

    return SessionAggregateResponse(**result)

@app.post("/coaching/hints")
async def generate_coaching_hints(request: Dict[str, Any]):

    scores = request.get("scores", {})
    session_type = request.get("session_type", "coding")
    exchange_number = request.get("exchange_number", 0)
    coaching_mode = request.get("coaching_mode", "training")

    if coaching_mode != "training":
        return {"hints": []}

    hints = []
    thresholds = {
        "communication_clarity": (0.65, "Structure your answer: approach first, then details"),
        "edge_case_awareness": (0.55, "Consider edge cases: empty input, maximum values"),
        "problem_decomposition": (0.60, "Break the problem into smaller sub-problems"),
        "handling_ambiguity": (0.55, "Ask clarifying questions before solving"),
        "collaborative_signals": (0.60, "Think out loud — share your reasoning"),
        "time_management": (0.50, "Start with a working solution, then optimize"),
    }

    for dim, (threshold, hint_text) in thresholds.items():
        if scores.get(dim, 1.0) < threshold:
            hints.append({
                "hint": hint_text,
                "dimension": dim,
                "priority": "high" if scores.get(dim, 1.0) < 0.4 else "medium",
            })

    return {"hints": hints[:3]}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "port": settings.service_port,
        "deberta_loaded": ml_pipeline is not None and hasattr(ml_pipeline, 'deberta') and ml_pipeline.deberta is not None,
        "embedding_loaded": ml_pipeline is not None and hasattr(ml_pipeline, 'embedding_scorer'),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)