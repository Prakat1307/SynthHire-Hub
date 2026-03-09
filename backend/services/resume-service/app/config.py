
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class ResumeSettings(BaseServiceSettings):
    service_name: str = "resume-service"
    service_port: int = 8018

settings = ResumeSettings()
