# FR-2.2 & FR-2.3: Orchestrator; executes the LangGraph flow and prepares data for the report.

import os
import json
import time
from fpdf import FPDF
from dotenv import load_dotenv
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from google.api_core.exceptions import ResourceExhausted, NotFound, InvalidArgument, ServiceUnavailable, PermissionDenied

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing from .env")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Configuration: Priority List
# UPDATED: Using verified aliases found in your account
MODEL_PRIORITY_LIST = [
    "models/gemini-2.0-flash-lite",   # Try Lite first (Efficiency)
    "models/gemini-2.0-flash",        # Standard Flash
    "models/gemini-flash-latest",     # CORRECTED: The alias your account has access to
    "models/gemini-2.0-flash-exp",    # Experimental backup (often has free quota)
    "models/gemini-pro-latest"        # Fallback Pro model
]

# Prompt templates
JOB_REQ_PROMPT = """
As a senior technical recruiter, generate a detailed set of requirements
for the job title: "{job_title}".

Return a structured format with three sections:

1. Key Responsibilities
2. Required Technical Skills
3. Essential Soft Skills
"""

SKILL_GAP_PROMPT = """
As an expert career coach, analyze the CV against job requirements.
Return a structured JSON object with keys:

1. summary  (one short paragraph)
2. matching_skills  (list)
3. missing_skills (list)

Do not include anything outside the JSON.

JOB REQUIREMENTS:
{job_requirements}

CV TEXT:
{cv_text}
"""

# Shared state class
class GapAnalysisState(dict):
    job_title: str
    cv_text: str
    job_requirements: str
    skill_report: dict
    pdf_path: str

# Helper: The Model Hopper
def generate_safe(prompt):
    last_exception = None
    
    for model_name in MODEL_PRIORITY_LIST:
        try:
            # print(f"Trying model: {model_name}...") # Uncomment for debug
            model = genai.GenerativeModel(model_name)
            return model.generate_content(prompt)
            
        except (ResourceExhausted, ServiceUnavailable) as e:
            print(f"⚠️  Quota hit on {model_name}. Switching...")
            last_exception = e
            time.sleep(1) # Brief pause
            continue
            
        except (PermissionDenied, NotFound, InvalidArgument, ValueError) as e:
            print(f"⚠️  {model_name} not accessible/found. Switching...")
            last_exception = e
            continue
            
        except Exception as e:
            print(f"❌ Critical error on {model_name}: {e}")
            last_exception = e
            continue
            
    # If all models fail, wait and force a retry on the most stable alias
    print("⏳ All models exhausted. Sleeping 60s to reset quota...")
    time.sleep(60)
    try:
        print("🔄 Retrying with gemini-flash-latest...")
        model = genai.GenerativeModel("models/gemini-flash-latest")
        return model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(f"Final retry failed: {e}")

# Node 1: Generate Job Requirements
def generate_job_requirements_node(state: GapAnalysisState):
    print(f"Generative Job Requirements for: {state['job_title']}...")
    response = generate_safe(JOB_REQ_PROMPT.format(job_title=state["job_title"]))
    state["job_requirements"] = response.text.strip()
    return state

# Node 2: Analyze Skill Gap
def analyze_skill_gap_node(state: GapAnalysisState):
    print("Analyzing Gap...")
    prompt = SKILL_GAP_PROMPT.format(
        cv_text=state["cv_text"],
        job_requirements=state["job_requirements"]
    )
    
    response = generate_safe(prompt)
    raw = response.text.strip()
    
    # Clean up markdown
    if raw.startswith("```json"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    elif raw.startswith("```"):
         raw = raw.replace("```", "").strip()

    try:
        skill_report = json.loads(raw)
    except json.JSONDecodeError:
        print("⚠️  Warning: Gemini returned malformed JSON.")
        skill_report = {
            "summary": "Error parsing JSON response.",
            "matching_skills": [],
            "missing_skills": [],
            "raw_response": raw
        }
        
    state["skill_report"] = skill_report
    return state

# Node 3: Generate Skill Report PDF
def generate_report_pdf_node(state: GapAnalysisState):
    print("Generating PDF...")
    report = state["skill_report"]
    
    safe_title = "".join([c for c in state["job_title"] if c.isalnum() or c in (' ', '_')]).strip()
    filename = f"Skill_Report_{safe_title.replace(' ', '_')}.pdf"

    pdf = FPDF()
    pdf.add_page()
    
    # Fonts and Layout
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, f"Skill Gap Report: {state['job_title']}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    
    # Handle encoding safely
    summary_text = report.get("summary", "N/A").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Matching Skills", ln=True)
    pdf.set_font("Arial", "", 11)
    for skill in report.get("matching_skills", []):
        clean_skill = str(skill).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, f"- {clean_skill}")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Missing Skills", ln=True)
    pdf.set_font("Arial", "", 11)
    for skill in report.get("missing_skills", []):
        clean_skill = str(skill).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, f"- {clean_skill}")

    pdf.output(filename)
    state["pdf_path"] = filename
    return state

# Build Workflow
def build_gap_analysis_graph():
    graph = StateGraph(GapAnalysisState)
    graph.add_node("generate_job_requirements", generate_job_requirements_node)
    graph.add_node("analyze_skill_gap", analyze_skill_gap_node)
    graph.add_node("generate_pdf", generate_report_pdf_node)
    
    graph.set_entry_point("generate_job_requirements")
    graph.add_edge("generate_job_requirements", "analyze_skill_gap")
    graph.add_edge("analyze_skill_gap", "generate_pdf")
    graph.add_edge("generate_pdf", END)
    
    return graph.compile()

# Main Execution Block
if __name__ == "__main__":
    job_title = input("Enter job title: ")
    cv_path = input("Enter path to CV file: ").strip('"') # Handle quotes

    if not os.path.exists(cv_path):
        print(f"❌ Error: File not found at {cv_path}")
    else:
        cv_text = ""
        print(f"Reading file: {cv_path}...")

        # 1. Try PDF Extraction
        if cv_path.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(cv_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        cv_text += extracted + "\n"
                print(f"✅ PDF loaded ({len(cv_text)} chars extracted).")
            except ImportError:
                print("❌ Error: pypdf is not installed. Run 'pip install pypdf'")
                exit()
            except Exception as e:
                print(f"❌ Failed to read PDF: {e}")
                exit()

        # 2. Fallback to Text Reading
        else:
            try:
                with open(cv_path, "r", encoding="utf-8") as f:
                    cv_text = f.read()
            except UnicodeDecodeError:
                print("⚠️  UTF-8 decode failed, trying Latin-1...")
                with open(cv_path, "r", encoding="latin-1") as f:
                    cv_text = f.read()

        if not cv_text.strip():
            print("❌ Error: Could not extract any text from the file.")
        else:
            workflow = build_gap_analysis_graph()
            initial_input = {
                "job_title": job_title,
                "cv_text": cv_text
            }
            
            try:
                final_state = workflow.invoke(initial_input)
                print("-" * 30)
                print("✅ SUCCESS: Skill Report Generated!")
                print("📄 PDF saved at:", final_state["pdf_path"])
            except Exception as e:
                print(f"❌ An error occurred: {e}")