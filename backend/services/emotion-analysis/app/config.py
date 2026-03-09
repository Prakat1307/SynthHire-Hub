from shared.config import BaseServiceSettings

class EmotionAnalysisSettings(BaseServiceSettings):
    service_name: str = "emotion-analysis"
    service_port: int = 8007
    
    detector_backend: str = "opencv"
    emotion_model: str = "Emotion"

settings = EmotionAnalysisSettings()
