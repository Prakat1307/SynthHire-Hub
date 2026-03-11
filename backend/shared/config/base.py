from pydantic_settings import BaseSettings
from typing import Optional, List

class BaseServiceSettings(BaseSettings):
    service_name: str = 'unknown'
    service_port: int = 8000
    debug: bool = False
    database_url: str = 'postgresql://synthhire:localdev123@localhost:5432/synthhire'
    mongodb_url: str = 'mongodb://synthhire:localdev123@localhost:27017/synthhire?authSource=admin'
    redis_url: str = 'redis://localhost:6379/0'
    rabbitmq_url: str = 'amqp://synthhire:localdev123@localhost:5672/'
    jwt_public_key_path: str = 'keys/jwt_public.pem'
    jwt_private_key_path: str = 'keys/jwt_private.pem'
    jwt_algorithm: str = 'RS256'
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7
    auth_service_url: str = 'http://localhost:8001'
    user_service_url: str = 'http://localhost:8002'
    session_orchestrator_url: str = 'http://localhost:8003'
    speech_pipeline_url: str = 'http://localhost:8004'
    code_executor_url: str = 'http://localhost:8005'
    assessment_engine_url: str = 'http://localhost:8006'
    emotion_analysis_url: str = 'http://localhost:8007'
    coaching_engine_url: str = 'http://localhost:8008'
    analytics_service_url: str = 'http://localhost:8010'
    report_generator_url: str = 'http://localhost:8009'
    openai_api_key: str = ''
    groq_api_key: str = ''
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    use_local_ai: bool = False
    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'phi4'
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = 'us-east-1'
    s3_bucket: str = 'synthhire-media'
    cors_origins: List[str] = ['http://localhost:3000', 'http://localhost:80']

    class Config:
        env_file = '.env'
        extra = 'allow'