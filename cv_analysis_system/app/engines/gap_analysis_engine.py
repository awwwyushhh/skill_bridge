# app/engines/gap_analysis_engine.py

from app.llm_workflows.gap_workflow import GapAnalysisState
import google.generativeai as genai
# Removed: from google.generativeai import types
import json
import os
from fpdf import FPDF # Assuming fpdf2 is installed

MODEL_NAME = "models/gemini-2.5-flash"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def generate_job_requirements_node(state: GapAnalysisState) -> GapAnalysisState:
    """Uses LLM to generate strict job requirements for the target role."""
    job_title = state.get("job_title")
    print(f"Generative Job Requirements for: {job_title}...")
    
    prompt = f"""
    You are a Senior Recruiter. Generate a comprehensive list of core and advanced skills 
    and requirements for a '{job_title}' role. The requirements should be strict and 
    include modern industry standards (e.g., specific cloud platforms, testing frameworks, advanced tools).
    
    Format the output as a simple, unformatted text list.
    """
    
    model = genai.GenerativeModel(MODEL_NAME)
    # --- FINAL FIX: Removing 'config' ---
    response = model.generate_content(prompt)
    # --- END FIX ---
    
    return {"job_requirements": response.text}


def analyze_skill_gap_node(state: GapAnalysisState) -> GapAnalysisState:
    """Compares CV skills against job requirements to identify gaps."""
    job_requirements = state.get("job_requirements")
    structured_data = state.get("structured_cv_data")
    
    print("Analyzing Skill Gap...")
    
    prompt = f"""
    You are a Skill Analyst. Compare the Candidate's Profile against the Job Requirements.
    1. List all skills the candidate is **MISSING** (gaps).
    2. List all skills the candidate **POSSESSES** (matches).
    3. Output the result as a strict JSON object. The 'missing_skills' list MUST be simple strings (e.g., ["TypeScript", "Docker"]).
    
    JOB REQUIREMENTS:
    {job_requirements}
    
    CANDIDATE PROFILE (STRUCTURED DATA):
    {json.dumps(structured_data, indent=2)}
    
    JSON SCHEMA:
    {{
        "analysis_summary": "A brief analysis of the candidate's strongest areas and biggest gaps.",
        "possesses_skills": ["skill1", "skill2"],
        "missing_skills": ["skill3", "skill4"]
    }}
    
    CRITICAL INSTRUCTION: Return ONLY the raw JSON object. Do not include markdown (```json) or any other formatting.
    """
    
    model = genai.GenerativeModel(MODEL_NAME)
    # --- FINAL FIX: Removing 'config' and relying on prompt engineering ---
    response = model.generate_content(prompt)
    # --- END FIX ---
    
    try:
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        skill_report = json.loads(raw_json)
        
        missing_skills = skill_report.get('missing_skills', [])
        
        return {
            "skill_report": skill_report,
            "skills_for_roadmap": missing_skills,
        }
    except Exception as e:
        print(f"❌ JSON Parsing Error in Gap Analysis: {e}")
        raise RuntimeError("LLM failed to generate valid gap analysis JSON.")


def generate_report_pdf_node(state: GapAnalysisState) -> GapAnalysisState:
    """Generates a PDF report summarizing the gap analysis."""
    skill_report = state.get("skill_report")
    user_name = state.get("user_name")
    
    print("Generating PDF...")
    
    pdf_path = os.path.join(ROOT_DIR, 'Skill_Report.pdf')
    
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(0, 10, txt=f"Skill Gap Report for {user_name}", ln=1, align="C")
        
        pdf.set_font("Arial", size=12, style='')
        pdf.ln(5)
        
        # Summary
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(0, 10, "Analysis Summary", ln=1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, skill_report.get('analysis_summary', 'N/A'))
        
        # Missing Skills
        pdf.ln(5)
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(0, 10, "Missing Skills (Gaps)", ln=1)
        pdf.set_font("Arial", size=12)
        for skill in skill_report.get('missing_skills', []):
            pdf.cell(0, 7, f"• {skill}", ln=1)

        pdf.output(pdf_path)
        
    except Exception as e:
        print(f"⚠️ PDF Generation Failed: {e}. Ensure fpdf2 is installed.")
    
    print("✅ PDF Generation complete.")
    return {"pdf_path": pdf_path}