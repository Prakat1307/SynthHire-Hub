import aiohttp
from typing import Dict, Any, Optional
import json

class ServiceClient:

    def __init__(self, base_url: str, timeout: int=120):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def get(self, path: str, headers: Dict[str, str]=None) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f'{self.base_url}{path}'
            default_headers = {'Content-Type': 'application/json', 'X-Internal-Service': 'true'}
            if headers:
                default_headers.update(headers)
            async with session.get(url, headers=default_headers) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    raise Exception(f'Service call failed: {resp.status} - {error_text}')
                return await resp.json()

    async def post(self, path: str, data: Dict[str, Any]=None, headers: Dict[str, str]=None) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f'{self.base_url}{path}'
            default_headers = {'Content-Type': 'application/json', 'X-Internal-Service': 'true'}
            if headers:
                default_headers.update(headers)
            async with session.post(url, json=data, headers=default_headers) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    raise Exception(f'Service call failed: {resp.status} - {error_text}')
                return await resp.json()