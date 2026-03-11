import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("backend/.env")

gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

try:
    # Need to check if this SDK version supports tools='google_search_retrieval'
    model = genai.GenerativeModel('gemini-2.5-flash')
    # Try sending a prompt that explicitly asks to search Google
    prompt = "Search the web for the public LinkedIn profile of Prakat Gupta (linkedin.com/in/me/ or similar). What is their headline and experience? Return as JSON."
    
    response = model.generate_content(prompt)
    print("Normal generation:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
