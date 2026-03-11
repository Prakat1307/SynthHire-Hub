import sys
import os
import asyncio
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from .config import settings
from shared.schemas.assessment import CodeExecutionRequest, CodeExecutionResponse
app = FastAPI(title='SynthHire Code Executor', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.post('/execute', response_model=CodeExecutionResponse)
async def execute_code(req: CodeExecutionRequest):
    if req.language != 'python':
        return CodeExecutionResponse(status='error', stderr=f'Execution for {req.language} is not yet implemented in this preview.', execution_time_ms=0)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(req.code)
            temp_path = f.name
        start_time = time.time()
        process = await asyncio.create_subprocess_exec(sys.executable, temp_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=settings.execution_timeout_seconds)
            duration_ms = int((time.time() - start_time) * 1000)
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            passed = 0
            total = 0
            test_results = []
            if req.test_cases:
                total = len(req.test_cases)
                if process.returncode == 0:
                    passed = total
            return CodeExecutionResponse(status='success' if process.returncode == 0 else 'error', stdout=stdout_str, stderr=stderr_str, execution_time_ms=duration_ms, passed=passed, total=total, test_results=test_results)
        except asyncio.TimeoutError:
            process.kill()
            return CodeExecutionResponse(status='timeout', stderr='Execution timed out.', execution_time_ms=settings.execution_timeout_seconds * 1000)
    except Exception as e:
        return CodeExecutionResponse(status='error', stderr=str(e), execution_time_ms=0)
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': settings.service_name}
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.service_port)