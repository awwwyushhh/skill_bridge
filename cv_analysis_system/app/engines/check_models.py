# Working: Checking the working of Gemini Models with the provided API key.

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print("Checking available models for my API key...")
    try:
        # iterate over models and print those that support content generation
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")