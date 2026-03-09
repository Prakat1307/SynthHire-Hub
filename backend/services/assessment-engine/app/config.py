
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class AssessmentSettings(BaseServiceSettings):
    service_name: str = "assessment-engine"
    service_port: int = 8006
    
    openai_model: str = "gpt-4o"
    gemini_api_key: str = None
    gemini_model: str = "gemini-2.5-flash"

settings = AssessmentSettings()
