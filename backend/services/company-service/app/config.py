from shared.config import BaseServiceSettings

class CompanyServiceSettings(BaseServiceSettings):
    service_name: str = "company-service"
    service_port: int = 8013

settings = CompanyServiceSettings()
