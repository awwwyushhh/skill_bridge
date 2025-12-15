# app/routes/generation_routes.py

import os
from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse, JSONResponse
from app.engines.cv_generator import CVGenerator # Your generator class
from app.config import CVGenerationRequest, settings

router = APIRouter()
generator = CVGenerator()

@router.post("/generate-final-cv/")
async def generate_final_cv(request: CVGenerationRequest):
    """
    Generates the final LaTeX file using the chosen template, 
    injects user-confirmed skills, and returns the .tex file for download.
    """
    
    # 1. Inject missing confirmed skills
    # We call the method here, although the render_and_save_node in the graph 
    # would also call it if we ran the full graph. We keep this route separate 
    # to allow the user to choose the template *after* the analysis.
    
    # Use the LLM-structured data as the base
    base_data = request.structured_cv_data

    # Inject the skills confirmed by the user via the frontend
    final_data = generator.inject_missing_skills(base_data, request.new_skills_to_inject)

    # 2. Render LaTeX
    try:
        latex_content = generator.render_cv(final_data, request.template_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV Rendering failed: {e}")

    # 3. Save .tex file
    saved_tex_file = generator.save_tex_file(latex_content, request.user_name, request.template_name)
    
    # 4. Return the .tex file
    return FileResponse(
        path=saved_tex_file,
        media_type='application/x-tex',
        filename=os.path.basename(saved_tex_file),
        background=JSONResponse({"message": "File is ready."}) # Optional: Clean return
    )