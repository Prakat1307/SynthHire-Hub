from shared.config import BaseServiceSettings

class UserServiceSettings(BaseServiceSettings):
    service_name: str = 'user-service'
    service_port: int = 8002
    free_sessions_per_month: int = 100
    pro_sessions_per_month: int = 500
    enterprise_sessions_per_month: int = -1
settings = UserServiceSettings()