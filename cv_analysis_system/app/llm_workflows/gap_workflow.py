# app/llm_workflows/gap_workflow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any, List

# --- Define the Shared State ---
class GapAnalysisState(TypedDict):
    """The state object passed between nodes in the LangGraph workflow."""
    cv_file_path: str
    job_title: str
    cv_text: str
    job_requirements: str
    skill_report: Optional[Dict[str, Any]]
    pdf_path: Optional[str]
    structured_cv_data: Optional[Dict[str, Any]]
    user_name: Optional[str]
    new_skills_to_add: Optional[List[str]]
    skills_for_roadmap: Optional[List[str]] # Kept for structure, but unused
    template_selection: str
    final_cv_tex_path: Optional[str]
    # roadmap_data: Optional[Dict[str, Any]] # Removed


# --- Import Nodes (Assuming all engine files are present) ---
from app.engines.nlp_analyzer import cv_reader_node, extract_data_node
from app.engines.cv_generator import render_and_save_node
from app.engines.gap_analysis_engine import (
    generate_job_requirements_node, 
    analyze_skill_gap_node, 
    generate_report_pdf_node
)
from app.engines.skill_verifier import skill_verification_node


# --- Build and Compile the Graph ---
def build_gap_analysis_graph():
    """
    Builds the 7-node workflow for CV Analysis and Generation.
    """
    graph = StateGraph(GapAnalysisState)
    
    # Nodes
    graph.add_node("read_cv", cv_reader_node)
    graph.add_node("extract_data", extract_data_node)
    graph.add_node("generate_job_requirements", generate_job_requirements_node)
    graph.add_node("analyze_skill_gap", analyze_skill_gap_node)
    graph.add_node("generate_pdf", generate_report_pdf_node)
    graph.add_node("verify_skills", skill_verification_node)
    graph.add_node("render_final_cv", render_and_save_node)
    
    # Edges
    graph.set_entry_point("read_cv")
    graph.add_edge("read_cv", "extract_data")
    graph.add_edge("extract_data", "generate_job_requirements")
    graph.add_edge("generate_job_requirements", "analyze_skill_gap")
    graph.add_edge("analyze_skill_gap", "generate_pdf")
    graph.add_edge("generate_pdf", "verify_skills") 
    
    # DIRECTLY connect verification to final CV rendering
    graph.add_edge("verify_skills", "render_final_cv") 
    graph.add_edge("render_final_cv", END)
    
    return graph.compile()