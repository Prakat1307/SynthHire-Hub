
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class SpeechSettings(BaseServiceSettings):
    service_name: str = "speech-pipeline"
    service_port: int = 8004
    
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    
    stt_provider: str = "groq-whisper"
    groq_api_key: str = ""
    
    tts_provider: str = "edge-tts"
    tts_voice: str = "en-US-ChristopherNeural"

settings = SpeechSettings()
