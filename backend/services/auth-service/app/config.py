import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.config.base import BaseServiceSettings

class AuthSettings(BaseServiceSettings):
    service_name: str = 'auth-service'
    service_port: int = 8001
settings = AuthSettings()