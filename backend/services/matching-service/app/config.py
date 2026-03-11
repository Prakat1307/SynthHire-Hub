import os
from shared.config import BaseServiceSettings

class MatchingServiceSettings(BaseServiceSettings):
    service_name: str = 'matching-service'
    service_port: int = 8015
    mock_llm: bool = os.getenv('MOCK_LLM', 'true').lower() == 'true'
settings = MatchingServiceSettings()