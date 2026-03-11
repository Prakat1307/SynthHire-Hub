from shared.config import BaseServiceSettings

class LearningServiceSettings(BaseServiceSettings):
    service_name: str = 'learning-service'
    service_port: int = 8012
    gemini_api_key: str = ''
    max_lessons_per_path: int = 10
settings = LearningServiceSettings()