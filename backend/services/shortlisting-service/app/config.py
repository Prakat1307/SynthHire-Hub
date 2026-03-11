from shared.config import BaseServiceSettings

class ShortlistingServiceSettings(BaseServiceSettings):
    service_name: str = 'shortlisting-service'
    service_port: int = 8014
settings = ShortlistingServiceSettings()