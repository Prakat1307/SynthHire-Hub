from shared.config import BaseServiceSettings

class ReportGeneratorSettings(BaseServiceSettings):
    service_name: str = 'report-generator'
    service_port: int = 8009
settings = ReportGeneratorSettings()