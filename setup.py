# Script for package setup, installation, and dependency management.

import os
from pathlib import Path

# --- Configuration ---
PROJECT_NAME = "cv_analysis_system"

# Define the structure and the content of each file/directory
structure = {
    PROJECT_NAME: {
        # Root files
        ".env": "# Environment variables for LLM API keys (e.g., OPENAI_API_KEY) and secrets.",
        "requirements.txt": "# List of Python dependencies (FastAPI/Flask, spacy, langgraph, openai, jinja2, etc.)",
        "README.md": "# Project documentation and setup instructions.",
        "setup.py": "# Script for package setup, installation, and dependency management.",

        # App Directory (Backend)
        "app": {
            "main.py": "# Backend API entry point (FastAPI/Flask instance); initializes config and routes.",
            "config.py": "# Configuration settings for the application (DB settings, model paths, etc.).",
           
            # Engines
            "engines": {
                "nlp_analyzer.py": "# FR-2.1: Handles CV file parsing (PDF/DOCX) and data extraction of skills, experience, etc.",
                "gap_analysis_engine.py": "# FR-2.2 & FR-2.3: Orchestrator; executes the LangGraph flow and prepares data for the report.",
                "cv_generator.py": "# CV Formatting: Manages LaTeX templating (merging data) and PDF compilation.",
            },
           
            # LLM Workflows
            "llm_workflows": {
                "gap_workflow.py": "# Defines the LangGraph nodes, state, and flow for the hybrid skill gap analysis."
            },

            # Data
            "data": {
                "job_roles.json": "// JSON file for Archetype job definitions and core skill sets (Ground Truth).",
                "latex_templates": {
                    "template_1.tex": "% Base LaTeX template for CV formatting (Option 1).",
                    "template_2.tex": "% Base LaTeX template for CV formatting (Option 2).",
                    "template_3.tex": "% Base LaTeX template for CV formatting (Option 3).",
                }
            },

            # Routes
            "routes": {
                "analysis_routes.py": "# API endpoints for CV upload, analysis trigger, and gap reporting.",
                "generation_routes.py": "# API endpoints for skill confirmation, CV format selection, and final PDF generation.",
            }
        }
    }
}

def create_structure(base_path, content_dict):
    """Recursively creates directories and files based on the dictionary."""
    for name, content in content_dict.items():
        path = base_path / name
       
        if isinstance(content, dict):
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content)
        else:
            # It's a file, write the content
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content + "\n")

if __name__ == "__main__":
    base_dir = Path.cwd()
    create_structure(base_dir, structure)
    print("\n✅ Project structure created successfully in the 'cv_analysis_system' folder!")