from shared.config import BaseServiceSettings

class CertificationServiceSettings(BaseServiceSettings):
    service_name: str = "certification-service"
    service_port: int = 8011
    certificate_ttl_days: int = 180  
    base_url: str = "http://localhost:8888"  

settings = CertificationServiceSettings()
