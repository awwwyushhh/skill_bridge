# roadmap_mvp/generator_node.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from roadmap_mvp_state import RoadmapState

# Load environment variables
load_dotenv() # Try default first
if not os.getenv("GEMINI_API_KEY"):
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(parent_env, override=True)
    print(f"Loaded .env from: {parent_env}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing from .env")

genai.configure(api_key=GEMINI_API_KEY)

# Use the requested model
MODEL_NAME = "models/gemini-2.5-flash"

ROADMAP_PROMPT = """
You are a Career Coach.
The user wants to learn these skills: {skills}.
We have found some potential search links (simulated): {search_data}.

Create a structured learning roadmap in JSON format.
The JSON must have this structure:
{{
    "roadmap_title": "...",
    "modules": [
        {{
            "skill": "Skill Name",
            "week": 1,
            "topic": "...",
            "recommended_action": "...",
            "resources": ["Link 1", "Link 2"]
        }}
    ]
}}

Return ONLY valid JSON. No markdown.
"""

def generator_node(state: RoadmapState) -> RoadmapState:
    """
    LangGraph Node: Uses LLM to synthesize data into a roadmap.
    """
    skills = state.get("skills_to_learn", [])
    search_data = state.get("raw_search_data", {})
    
    print(f"\n🧠 Generator Node: Synthesizing roadmap using {MODEL_NAME}...")
    
    prompt = ROADMAP_PROMPT.format(skills=skills, search_data=search_data)
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Clean markdown if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "").strip()
            
        json_output = json.loads(raw_text)
        print("✅ Generator Node: Roadmap created successfully.")
        
        return {"final_roadmap_json": json_output}
        
    except Exception as e:
        print(f"❌ Generator Node Error: {e}")
        return {"final_roadmap_json": {"error": str(e)}}
