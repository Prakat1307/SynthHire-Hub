import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = 'job-service'
    environment: str = os.getenv('ENVIRONMENT', 'development')
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://synthhire:synthhire_dev@localhost:5432/synthhire')
    jwt_secret: str = os.getenv('JWT_SECRET', 'super-secret-key-for-dev-only')
    jwt_algorithm: str = 'HS256'
    matching_service_url: str = os.getenv('MATCHING_SERVICE_URL', 'http://localhost:8015')
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    gemini_api_key_2: str = os.getenv('GEMINI_API_KEY_2', '')
    gemini_api_key_3: str = os.getenv('GEMINI_API_KEY_3', '')
    gemini_api_key_4: str = os.getenv('GEMINI_API_KEY_4', '')
    gemini_model: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    adzuna_app_id: str = os.getenv('ADZUNA_APP_ID', '')
    adzuna_app_key: str = os.getenv('ADZUNA_APP_KEY', '')
settings = Settings()