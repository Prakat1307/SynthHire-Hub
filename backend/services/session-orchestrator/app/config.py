
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class OrchestratorSettings(BaseServiceSettings):
    service_name: str = "session-orchestrator"
    service_port: int = 8003
    max_session_duration_minutes: int = 60
    max_exchanges_per_session: int = 50

settings = OrchestratorSettings()
