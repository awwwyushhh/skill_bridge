# app/llm_workflows/gap_workflow.py (Top section of the file)

from typing import TypedDict, Optional, Dict, Any, List
# from langgraph.graph import StateGraph, END # Rest of the file would include the graph build

# --- Define the Shared State (CENTRAL DATA OBJECT) ---
class GapAnalysisState(TypedDict):
    """The state object passed between nodes in the LangGraph workflow."""
    
    # 1. Input Data
    cv_file_path: str
    job_title: str
    template_selection: str
    
    # 2. Raw Intermediate Data
    cv_text: str
    job_requirements: str
    
    # 3. Structured Intermediate Data
    structured_cv_data: Optional[Dict[str, Any]]
    user_name: Optional[str]

    # 4. Analysis & Verification Results
    skill_report: Optional[Dict[str, Any]] # Full JSON report from analysis node
    pdf_path: Optional[str] # Path to the generated skill report PDF
    new_skills_to_add: Optional[List[str]] # Skills user confirms they possess (for final CV)
    skills_for_roadmap: Optional[List[str]] # Skills user confirms they are missing (for future use)

    # 5. Final Output
    final_cv_tex_path: Optional[str] # Path to the final generated LaTeX CV file

# The rest of the file would contain the 'build_gap_analysis_graph' function...