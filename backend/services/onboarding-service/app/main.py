import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional, List
import uvicorn
import io
from pypdf import PdfReader
from .config import settings
from .database import get_db, create_tables
from .service import OnboardingService
from .schemas import ResumeParseResponse, ResumeVersionResponse, JobTargetingRequest, PersonalStoryCreate, PersonalStoryUpdate, PersonalStoryResponse, PreferencesRequest, PreferencesResponse, OnboardingStatusResponse
from shared.auth.jwt_handler import JWTHandler
jwt_handler: Optional[JWTHandler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwt_handler
    print(f'Initializing {settings.service_name}...')
    create_tables()
    jwt_handler = JWTHandler(public_key_path=settings.jwt_public_key_path, private_key_path=settings.jwt_private_key_path, algorithm=settings.jwt_algorithm)
    print(f'{settings.service_name} started on port {settings.service_port}')
    yield
app = FastAPI(title='SynthHire Onboarding Service', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://localhost:8888'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

async def get_current_user_id(authorization: Optional[str]=Header(None)) -> str:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
    token = authorization.replace('Bearer ', '')
    payload = jwt_handler.validate_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    return payload.get('sub') or payload.get('user_id')

def get_service(db: Session=Depends(get_db)) -> OnboardingService:
    return OnboardingService(db=db, gemini_api_key=settings.gemini_api_key, gemini_model=settings.gemini_model)

@app.post('/onboarding/resume/upload', response_model=ResumeParseResponse)
async def upload_resume(resume_file: Optional[UploadFile]=File(None), resume_text: Optional[str]=Form(None), file_name: Optional[str]=Form(None), user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    try:
        final_text = ''
        if resume_file:
            content = await resume_file.read()
            if resume_file.filename.lower().endswith('.pdf'):
                reader = PdfReader(io.BytesIO(content))
                final_text = ' '.join((page.extract_text() for page in reader.pages if page.extract_text()))
            else:
                final_text = content.decode('utf-8', errors='ignore')
            if not file_name:
                file_name = resume_file.filename
        elif resume_text:
            final_text = resume_text
        else:
            raise HTTPException(status_code=400, detail='Must provide either resume_text or resume_file')
        result = await service.parse_resume(user_id, final_text, file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Resume parsing failed: {str(e)}')

@app.put('/onboarding/resume/{resume_id}/parsed')
async def update_resume_parsed(resume_id: str, parsed_json: dict, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    try:
        resume = service.update_resume_parsed(user_id, resume_id, parsed_json)
        return {'status': 'updated', 'resume_id': str(resume.id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get('/onboarding/resume/versions', response_model=List[ResumeVersionResponse])
async def list_resume_versions(user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    versions = service.get_resume_versions(user_id)
    return [{'id': str(v.id), 'label': v.label, 'is_master': v.is_master, 'raw_text': v.raw_text, 'parsed_json': v.parsed_json, 'file_name': v.file_name, 'match_score': v.match_score, 'version_number': v.version_number, 'created_at': v.created_at} for v in versions]

@app.delete('/onboarding/resume/versions/{version_id}')
async def delete_resume_version(version_id: str, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    try:
        service.delete_resume_version(user_id, version_id)
        return {'status': 'deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post('/onboarding/job-targeting')
async def save_job_targeting(data: JobTargetingRequest, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    profile = service.save_job_targeting(user_id, data.model_dump())
    return {'status': 'saved', 'target_role': profile.target_role, 'industry': profile.industry}

@app.post('/onboarding/stories', response_model=PersonalStoryResponse)
async def create_story(data: PersonalStoryCreate, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    story = service.create_story(user_id, data.model_dump())
    return {'id': str(story.id), 'title': story.title, 'situation': story.situation, 'task': story.task, 'action': story.action, 'result': story.result, 'tags': story.tags or [], 'company_name': story.company_name, 'role_at_time': story.role_at_time, 'sort_order': story.sort_order, 'created_at': story.created_at}

@app.get('/onboarding/stories', response_model=List[PersonalStoryResponse])
async def list_stories(user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    stories = service.get_stories(user_id)
    return [{'id': str(s.id), 'title': s.title, 'situation': s.situation, 'task': s.task, 'action': s.action, 'result': s.result, 'tags': s.tags or [], 'company_name': s.company_name, 'role_at_time': s.role_at_time, 'sort_order': s.sort_order, 'created_at': s.created_at} for s in stories]

@app.put('/onboarding/stories/{story_id}', response_model=PersonalStoryResponse)
async def update_story(story_id: str, data: PersonalStoryUpdate, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    try:
        story = service.update_story(user_id, story_id, data.model_dump(exclude_unset=True))
        return {'id': str(story.id), 'title': story.title, 'situation': story.situation, 'task': story.task, 'action': story.action, 'result': story.result, 'tags': story.tags or [], 'company_name': story.company_name, 'role_at_time': story.role_at_time, 'sort_order': story.sort_order, 'created_at': story.created_at}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete('/onboarding/stories/{story_id}')
async def delete_story(story_id: str, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    try:
        service.delete_story(user_id, story_id)
        return {'status': 'deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post('/onboarding/preferences', response_model=PreferencesResponse)
async def save_preferences(data: PreferencesRequest, user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    prefs = service.save_preferences(user_id, data.model_dump())
    return {'id': str(prefs.id), 'tone': prefs.tone.value if prefs.tone else 'conversational', 'answer_length': prefs.answer_length.value if prefs.answer_length else 'medium', 'answer_format': prefs.answer_format.value if prefs.answer_format else 'star', 'created_at': prefs.created_at}

@app.get('/onboarding/preferences', response_model=Optional[PreferencesResponse])
async def get_preferences(user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    prefs = service.get_preferences(user_id)
    if not prefs:
        return None
    return {'id': str(prefs.id), 'tone': prefs.tone.value if prefs.tone else 'conversational', 'answer_length': prefs.answer_length.value if prefs.answer_length else 'medium', 'answer_format': prefs.answer_format.value if prefs.answer_format else 'star', 'created_at': prefs.created_at}

@app.post('/onboarding/complete')
async def complete_onboarding(user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    profile = service.complete_onboarding(user_id)
    return {'status': 'completed', 'onboarding_completed': True}

@app.get('/onboarding/status', response_model=OnboardingStatusResponse)
async def get_onboarding_status(user_id: str=Depends(get_current_user_id), service: OnboardingService=Depends(get_service)):
    return service.get_onboarding_status(user_id)

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': settings.service_name, 'port': settings.service_port}
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)