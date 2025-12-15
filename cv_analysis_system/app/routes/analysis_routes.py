# app/routes/analysis_routes.py

import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from starlette.responses import JSONResponse
from app.engines.nlp_analyzer import parse_cv 
from app.llm_workflows.gap_workflow import build_gap_analysis_graph
from app.state import GapAnalysisState 
from app.config import SkillGapReportSchema, settings
from uuid import uuid4

router = APIRouter()
ANALYSIS_GRAPH = build_gap_analysis_graph() # Compile the graph once on startup

# Use the 'generated_cvs' folder for temporary uploads as well
TEMP_UPLOAD_DIR = os.path.join(settings.OUTPUT_DIR, "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@router.post("/analyze-cv/", response_model=SkillGapReportSchema)
async def analyze_cv(
    job_title: str = Form(...), 
    file: UploadFile = File(...)
):
    """
    FR-2.1, FR-2.2, FR-2.3: Uploads CV, runs LangGraph analysis 
    (Read -> Structure -> Gap Check -> PDF Report).
    """
    
    unique_id = str(uuid4())
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, f"{unique_id}_{file.filename}")
    
    # 1. Save File Temporarily
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saving error: {e}")

    # 2. Execute LangGraph Workflow (Starts at 'read_cv' node)
    try:
        # NOTE: cv_reader_node will handle the text extraction from the path
        initial_input = GapAnalysisState(
            cv_file_path=temp_file_path,
            job_title=job_title,
            cv_text="", # Text will be filled by the node
            skill_report=None,
            pdf_path=None,
            new_skills_to_add=None,
            template_selection="template_1.tex" # Default template for extraction node
        )
        
        # The LangGraph executes the entire chain: Read -> Extract -> Analyze -> PDF -> VERIFY -> RENDER -> END
        # To test the flow *up to* the PDF, we will manually stop the full graph here in a clean test run.
        # Since the full graph is compiled, we run the full chain for complete state.
        final_state = ANALYSIS_GRAPH.invoke(initial_input)
        
        # 3. Cleanup and Return
        os.remove(temp_file_path)
        
        report = final_state.get("skill_report", {})
        
        return SkillGapReportSchema(
            summary=report.get("summary", "Analysis complete, but summary failed."),
            matching_skills=report.get("matching_skills", []),
            missing_skills=report.get("missing_skills", []),
            pdf_path=final_state.get("pdf_path", "N/A") # Path to the generated PDF
        )

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"FATAL LANGGRAPH ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis workflow failed: {e}")