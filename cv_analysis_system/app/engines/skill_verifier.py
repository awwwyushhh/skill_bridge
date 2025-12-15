# app/engines/skill_verifier.py

import os
import json
import time
import re
import google.generativeai as genai
# Removed: from google.generativeai import types
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, NotFound, InvalidArgument, PermissionDenied
from pypdf import PdfReader 
from app.llm_workflows.gap_workflow import GapAnalysisState
from typing import List, Dict, Any

# Load environment variables (for GEMINI_API_KEY check, handled in main)
load_dotenv()
MODEL_PRIORITY_LIST = ["models/gemini-2.5-flash"]

# --- Helper Functions (LLM Call and PDF Extraction) ---

def _get_gemini_response(prompt: str) -> str:
    """Robust API caller."""
    for model_name in MODEL_PRIORITY_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            # --- FINAL FIX: Removing 'config' ---
            response = model.generate_content(prompt)
            # --- END FIX ---
            return response.text
        except (ResourceExhausted, ServiceUnavailable):
            print(f"   ⚠️  Quota hit on {model_name}. Waiting 10s...")
            time.sleep(10)
            continue
        except (NotFound, PermissionDenied, InvalidArgument) as e:
            print(f"   ⚠️  {model_name} error ({type(e).__name__}). Switching...")
            continue
        except Exception as e:
            print(f"   ❌ Unexpected error on {model_name}: {e}")
            continue

    print("   ⏳ All models exhausted. Sleeping 60s...")
    time.sleep(60)
    try:
        return genai.GenerativeModel("models/gemini-2.5-flash").generate_content(prompt).text
    except Exception as e:
        print(f"   ❌ Final retry failed: {e}")
        return ""

def extract_missing_skills_from_pdf(pdf_path: str) -> List[str]:
    """Extracts missing skills list directly from the generated Skill Gap Report PDF."""
    if not os.path.exists(pdf_path):
        return []

    try:
        reader = PdfReader(pdf_path)
        text = "".join(page.extract_text() + "\n" for page in reader.pages)
        
        lines = text.split('\n')
        extracted_skills = []
        capture_mode = False
        
        for line in lines:
            clean_line = line.strip()
            if "Missing Skills" in clean_line and not capture_mode:
                capture_mode = True
                continue
            if capture_mode and (clean_line.startswith("Summary") or clean_line.startswith("Matching")):
                break
            if capture_mode and (clean_line.startswith("-") or clean_line.startswith("•")):
                raw_skill = clean_line.lstrip("-• ").strip()
                simple_skill = re.sub(r'\s*\(.*?\)', '', raw_skill).strip()
                if simple_skill and len(simple_skill) < 50: 
                    extracted_skills.append(simple_skill)
        
        return extracted_skills[:4]

    except Exception as e:
        print(f"Error parsing PDF for missing skills: {e}")
        return []

def generate_questions(missing_skills: List[str]) -> List[Dict[str, Any]]:
    """Generates verification questions using the LLM."""
    prompt = f"""
    You are a Technical Recruiter. A candidate is missing these skills: {missing_skills}.
    Generate a very short, crisp question for each skill.
    The question format should strictly be: "Do you have experience with [Skill Name]?"
    Return a strict JSON list of objects matching this schema exactly:
    [ {{"skill": "Skill Name", "question": "...", "options": ["1. Yes", "2. No"]}} ]
    
    CRITICAL INSTRUCTION: Return ONLY the raw JSON object. Do not include markdown (```json) or any other formatting.
    """
    
    # --- FINAL FIX: Calling the robust helper without configuration ---
    raw_text = _get_gemini_response(prompt)
    # --- END FIX ---
    
    if not raw_text: return []

    try:
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except json.JSONDecodeError:
        print(f"❌ Error parsing JSON from AI: {raw_text[:100]}...")
        return []


def verify_skills_with_user(questions: List[Dict[str, Any]]):
    """Handles the terminal user interaction for skill verification."""
    skills_to_add_to_cv = []
    skills_for_roadmap = [] 

    print("\n" + "="*50)
    print("🔍 SKILL CHECK (Requires Terminal Input)")
    print("="*50)
    
    for q in questions:
        print(f"🔹 {q['question']}")
        while True:
            choice = input("   👉 (1) Yes / (2) No: ").strip()
            if choice == "1":
                skills_to_add_to_cv.append(q['skill'])
                break
            elif choice == "2":
                skills_for_roadmap.append(q['skill'])
                break
            else:
                print("   ⚠️ Invalid input. Enter 1 or 2.")

    return skills_to_add_to_cv, skills_for_roadmap

# --- LangGraph Node ---

def skill_verification_node(state: GapAnalysisState) -> GapAnalysisState:
    """LangGraph node: Orchestrates skill verification with the user."""
    pdf_path = state.get("pdf_path")
    
    if not pdf_path or not os.path.exists(pdf_path):
        print("⚠️  Skill Verification skipped: PDF report not found in state.")
        return {"new_skills_to_add": [], "skills_for_roadmap": []}
        
    print(f"\n🔍 Starting Skill Verification using report: {pdf_path}")
    
    extracted_missing_skills = extract_missing_skills_from_pdf(pdf_path)
    
    if not extracted_missing_skills:
        print("   ✅ No missing skills found. Proceeding to CV generation.")
        return {"new_skills_to_add": [], "skills_for_roadmap": []}

    questions = generate_questions(extracted_missing_skills)
    
    if not questions:
        print("❌ Failed to generate verification questions. Proceeding with empty list.")
        return {"new_skills_to_add": [], "skills_for_roadmap": []}

    skills_to_add_to_cv, skills_for_roadmap = verify_skills_with_user(questions)

    return {
        "new_skills_to_add": skills_to_add_to_cv, 
        "skills_for_roadmap": skills_for_roadmap,
    }