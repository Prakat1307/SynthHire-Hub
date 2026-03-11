import os
import sys
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

async def test_gemini():
    print(f'\n🧠 Testing Gemini API Key...')
    if not GEMINI_API_KEY or 'placeholder' in GEMINI_API_KEY:
        print('❌ [ERROR] GEMINI_API_KEY is missing/placeholder.')
        return False
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Gemini OK'")
        if response.text:
            print(f'✅ [SUCCESS] Gemini is working! Response: {response.text.strip()}')
            return True
        else:
            print('❌ [ERROR] Gemini returned empty response.')
            return False
    except Exception as e:
        print(f'❌ [ERROR] Gemini Failed: {e}')
        return False

def test_elevenlabs():
    print(f'\n🎤 Testing ElevenLabs API Key...')
    if not ELEVEN_LABS_API_KEY or 'placeholder' in ELEVEN_LABS_API_KEY:
        print('❌ [ERROR] ELEVEN_LABS_API_KEY is missing/placeholder.')
        return False
    url = 'https://api.elevenlabs.io/v1/voices'
    headers = {'xi-api-key': ELEVEN_LABS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            voices = data.get('voices', [])
            print(f'✅ [SUCCESS] ElevenLabs is working! Found {len(voices)} voices.')
            return True
        else:
            print(f'❌ [ERROR] ElevenLabs Failed: Status {response.status_code} - {response.text[:100]}')
            return False
    except Exception as e:
        print(f'❌ [ERROR] ElevenLabs Connection Error: {e}')
        return False

async def main():
    print('==========================================')
    print('      SynthHire API Verification')
    print('==========================================')
    gemini_ok = await test_gemini()
    eleven_ok = test_elevenlabs()
    print('\n==========================================')
    if gemini_ok and eleven_ok:
        print('🚀 ALL SYSTEMS GO! Both API keys are valid.')
    else:
        print('⚠️ Issues detected. Please check errors above.')
    print('==========================================')
if __name__ == '__main__':
    asyncio.run(main())