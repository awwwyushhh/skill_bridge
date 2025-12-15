# app/engines/cv_generator.py

from app.llm_workflows.gap_workflow import GapAnalysisState
import os
from jinja2 import Environment, FileSystemLoader
import google.generativeai as genai

MODEL_NAME = "gemini-2.5-flash" 

# Define paths relative to the project structure
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'app', 'data', 'latex_templates')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'app', 'data', 'generated_cvs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def render_and_save_node(state: GapAnalysisState) -> GapAnalysisState:
    """
    LangGraph Node: Renders the structured data into a LaTeX CV using Jinja2.
    Contains the fix for the template path error.
    """
    structured_data = state.get("structured_cv_data")
    template_choice = state.get("template_selection")
    user_name = state.get("user_name", "Candidate")
    
    if not structured_data:
        raise RuntimeError("CV Data Missing: Cannot render CV.")
    
    # --- TEMPLATE PATH CORRECTION (The Fix) ---
    if template_choice.isdigit():
        template_filename = f"template_{template_choice}.tex"
    elif not template_choice.endswith(".tex"):
        template_filename = f"{template_choice}.tex"
    else:
        template_filename = template_choice
    # ------------------------------------------
    
    try:
        print(f"🎨 Filling template: {template_filename}...")
        
        # Setup Jinja2 environment (configured for LaTeX)
        env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            block_start_string=r'\BLOCK{', block_end_string=r'}', 
            variable_start_string=r'\VAR{', variable_end_string=r'}',
            comment_start_string=r'\#{', comment_end_string=r'}', 
            line_statement_prefix='%%', trim_blocks=True, lstrip_blocks=True
        )
        
        template = env.get_template(template_filename)
        
        # Render the template
        rendered_tex = template.render(data=structured_data)
        
        # Define output path
        safe_name = user_name.replace(" ", "_").replace(".", "")
        output_filename = f"{safe_name}_Optimized_CV_{template_choice}.tex"
        final_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Save the rendered .tex file
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(rendered_tex)
            
        print(f"✅ Final CV (.tex) saved to: {final_path}")
        return {"final_cv_tex_path": final_path}
        
    except Exception as e:
        print(f"❌ Template Rendering Error for '{template_filename}': {e}")
        raise Exception(f"Template Rendering Error: {e}")