
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from shared.config.base import BaseServiceSettings

class CodeExecutorSettings(BaseServiceSettings):
    service_name: str = "code-executor"
    service_port: int = 8005
    
    execution_timeout_seconds: int = 5
    max_memory_mb: int = 128

settings = CodeExecutorSettings()
