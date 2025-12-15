# app/main.py

import os
import sys # Added for error handling
import json
from app.llm_workflows.gap_workflow import build_gap_analysis_graph, GapAnalysisState 
from dotenv import load_dotenv
import google.generativeai as genai # <-- CRITICAL NEW IMPORT

load_dotenv()

# --- CRITICAL FIX START: Configure SDK immediately after loading .env ---
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # Note: If this line fails, the workflow will stop, but the key is passed.
    except Exception as e:
        print(f"⚠️ Warning: Failed to configure genai, check API key format. Error: {e}")
        
# --- CRITICAL FIX END ---


# --- LOCAL TERMINAL ORCHESTRATION ---
def run_terminal_orchestration():
    """Orchestrates the CV Analysis and Generation LangGraph workflow."""
    
    # Use the variable defined globally for the configuration check
    if not API_KEY:
        print("\n❌ CRITICAL ERROR: GEMINI_API_KEY is not set in the .env file.")
        print("Please set your API key to run the LLM-powered workflow.")
        return

    print("=" * 60)
    print("🚀 CV ANALYSIS & GENERATION SYSTEM - TERMINAL MODE")
    print("=" * 60)
    
    # 1. Gather Inputs
    job_title = input("1. Enter Target Job Role (e.g., Senior Full-Stack Engineer): ").strip()
    cv_path = input("2. Enter CV File Path (PDF/TXT): ").strip('"').strip()
    template_choice = input("3. Enter Template Number (e.g., 1 for template_1.tex): ").strip()
    
    if not os.path.exists(cv_path):
        print(f"\n❌ Error: File not found at {cv_path}. Exiting.")
        return
        
    # 2. Compile and Initialize Graph State
    try:
        workflow = build_gap_analysis_graph()
        
        initial_input = GapAnalysisState(
            cv_file_path=cv_path,
            job_title=job_title,
            cv_text="", 
            skill_report=None,
            pdf_path=None,
            structured_cv_data=None,
            user_name=None,
            new_skills_to_add=None,
            skills_for_roadmap=None, 
            template_selection=template_choice,
            final_cv_tex_path=None
        )
        
        print("\n⏳ Running full LangGraph workflow...")
        
        # 3. Invoke the complete workflow
        final_state = workflow.invoke(initial_input)
        
        # 4. Final Output Display
        print("\n" + "=" * 60)
        print("✅ WORKFLOW COMPLETE!")
        print("=" * 60)
        
        print(f"🖼️ Final CV (.tex) Saved: {final_state.get('final_cv_tex_path', 'N/A')}")
        print(f"📄 Skill Gap Report PDF Saved: {final_state.get('pdf_path', 'N/A')}")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ WORKFLOW FAILED: A critical error occurred.")
        print(f"Error Details: {e}")
        # Use sys.excepthook or similar for clearer debug output if needed
        print("=" * 60)


if __name__ == "__main__":
    run_terminal_orchestration()