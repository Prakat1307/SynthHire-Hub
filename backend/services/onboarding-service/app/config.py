
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class OnboardingSettings(BaseServiceSettings):
    service_name: str = "onboarding-service"
    service_port: int = 8017

settings = OnboardingSettings()
