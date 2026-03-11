import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import json
import asyncio

class GeminiClient:

    def __init__(self, api_key: str=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY not found in environment')
        genai.configure(api_key=self.api_key)
        self.generation_config = {'temperature': 0.7, 'top_p': 0.95, 'top_k': 40, 'max_output_tokens': 8192}
        self.safety_settings = [{'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'}, {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'}, {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'}, {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'}]

    async def generate_content(self, prompt: str, system_instruction: str=None, model_name: str='gemini-flash-latest', temperature: float=0.7, json_mode: bool=False) -> str:
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config={**self.generation_config, 'temperature': temperature})
            full_prompt = prompt
            if system_instruction:
                full_prompt = f'System Instruction: {system_instruction}\n\n{prompt}'
            response = await asyncio.to_thread(model.generate_content, full_prompt, safety_settings=self.safety_settings)
            return response.text
        except Exception as e:
            print(f'Gemini API Error: {str(e)}')
            raise e

    async def get_audio_transcription(self, audio_data: bytes) -> str:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            prompt = 'Transcribe the following audio exactly as spoken. Return only the text.'
            response = await asyncio.to_thread(model.generate_content, [prompt, {'mime_type': 'audio/mp3', 'data': audio_data}])
            return response.text.strip()
        except Exception as e:
            print(f'Gemini Audio Transcription Error: {str(e)}')
            return ''