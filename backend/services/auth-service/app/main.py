import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn
from .config import settings
from .database import get_db, create_tables
from .service import AuthService
from shared.auth.jwt_handler import JWTHandler
from shared.utils.redis_client import RedisClient
from shared.schemas.auth import UserCreate, UserLogin, TokenResponse, TokenRefreshRequest, TokenValidateRequest, TokenValidateResponse, UserResponse
jwt_handler: Optional[JWTHandler] = None
redis_client: Optional[RedisClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwt_handler, redis_client
    print(f'Initializing {settings.service_name}...')
    create_tables()
    jwt_handler = JWTHandler(public_key_path=settings.jwt_public_key_path, private_key_path=settings.jwt_private_key_path, algorithm=settings.jwt_algorithm)
    redis_client = RedisClient(settings.redis_url)
    print(f'{settings.service_name} started on port {settings.service_port}')
    yield
app = FastAPI(title='SynthHire Auth Service', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://synthhire.me", "https://www.synthhire.me"], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_auth_service(db: Session=Depends(get_db)) -> AuthService:
    return AuthService(db=db, jwt_handler=jwt_handler, redis=redis_client)

@app.post('/auth/register', response_model=TokenResponse)
async def register(data: UserCreate, service: AuthService=Depends(get_auth_service)):
    try:
        return await service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/auth/login', response_model=TokenResponse)
async def login(data: UserLogin, service: AuthService=Depends(get_auth_service)):
    try:
        return await service.login(data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post('/auth/refresh', response_model=TokenResponse)
async def refresh(body: TokenRefreshRequest, service: AuthService=Depends(get_auth_service)):
    try:
        return await service.refresh(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post('/auth/logout')
async def logout(body: TokenRefreshRequest, service: AuthService=Depends(get_auth_service)):
    await service.logout(body.refresh_token)
    return {'status': 'logged_out'}

@app.post('/auth/validate', response_model=TokenValidateResponse)
async def validate(body: TokenValidateRequest, service: AuthService=Depends(get_auth_service)):
    return await service.validate_token(body.token)

@app.get('/auth/me', response_model=UserResponse)
async def current_user(authorization: Optional[str]=Header(None), service: AuthService=Depends(get_auth_service)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
    token = authorization.replace('Bearer ', '')
    payload = jwt_handler.validate_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    try:
        return await service.get_current_user(payload)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': settings.service_name, 'port': settings.service_port}
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)
