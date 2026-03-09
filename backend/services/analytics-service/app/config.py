from shared.config import BaseServiceSettings

class AnalyticsServiceSettings(BaseServiceSettings):
    service_name: str = "analytics-service"
    service_port: int = 8010

settings = AnalyticsServiceSettings()
