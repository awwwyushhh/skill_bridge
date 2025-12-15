# app/engines/nlp_analyzer.py

from app.llm_workflows.gap_workflow import GapAnalysisState
import os
import google.generativeai as genai
# Removed: from google.generativeai import types
import json
from pypdf import PdfReader 

MODEL_NAME = "models/gemini-2.5-flash"

CV_SCHEMA = """
{
  "name": "...",
  "summary": "...",
  "experience": [
    {"title": "...", "company": "...", "dates": "...", "description": "..."}
  ],
  "skills": ["...", "..."],
  "education": ["..."]
}
"""

def cv_reader_node(state: GapAnalysisState) -> GapAnalysisState:
    """Reads the CV file (PDF or TXT) and extracts raw text."""
    cv_path = state.get("cv_file_path")
    cv_text = ""
    print("🧠 Reading CV text...")

    if cv_path.lower().endswith('.txt'):
        try:
            with open(cv_path, 'r', encoding='utf-8') as f:
                cv_text = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read TXT file: {e}")

    elif cv_path.lower().endswith('.pdf'):
        try:
            reader = PdfReader(cv_path)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() or "" 
                
            if not cv_text.strip():
                raise ValueError("PDF opened but no text could be extracted. Check if the PDF is image-only or encrypted.")
            
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF file at {cv_path}: {e}")
            
    else:
        raise ValueError(f"Unsupported file type: {os.path.basename(cv_path)}. Please use .pdf or .txt.")
    
    return {"cv_text": cv_text}


def extract_data_node(state: GapAnalysisState) -> GapAnalysisState:
    """Uses LLM to structure the raw CV text into a clean JSON object."""
    cv_text = state.get("cv_text")
    if not cv_text or len(cv_text.strip()) < 50:
        raise RuntimeError("Cannot process CV: Raw CV text is empty or too short. Check the file path and PDF parsing in the previous node.")

    print("🧠 Structuring CV data...")
    prompt = f"""
    You are an expert CV parser. Analyze the following raw CV text and extract all 
    relevant fields into a structured JSON object. The JSON MUST strictly follow this schema.
    
    SCHEMA: {CV_SCHEMA}
    
    RAW CV TEXT:
    ---
    {cv_text}
    ---
    
    CRITICAL INSTRUCTION: Return ONLY the raw JSON object. Do not include markdown (```json) or any other formatting.
    """
    
    model = genai.GenerativeModel(MODEL_NAME)
    
    # --- FINAL FIX: Removing 'config' and relying on prompt engineering ---
    response = model.generate_content(prompt)
    # --- END FIX ---

    try:
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        structured_data = json.loads(raw_json)
        
        user_name = structured_data.get('name', 'Unknown_Candidate')
        return {"structured_cv_data": structured_data, "user_name": user_name}
        
    except Exception as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"Raw LLM Output: {response.text}")
        raise RuntimeError("LLM failed to generate valid structured CV JSON. Check the API response.")