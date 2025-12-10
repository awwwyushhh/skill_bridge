# CV Formatting: Manages LaTeX templating (merging data) and PDF compilation.

import os
import json
import time
from typing import Dict, Any
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, NotFound, InvalidArgument

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing from .env")

genai.configure(api_key=GEMINI_API_KEY)

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # points to app/
TEMPLATE_DIR = os.path.join(BASE_DIR, 'data', 'latex_templates')
OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_cvs')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GEMINI PROMPT
CV_STRUCTURING_PROMPT = """
You are an expert Resume Parser. 
Convert the provided CV Text into a strict JSON object that matches the schema below perfectly.
The JSON will be used to populate a LaTeX template.

JSON SCHEMA:
{{
  "personal_info": {{
    "name": "Full Name",
    "location": "City, Country",
    "phone": "Phone Number",
    "email": "Email Address",
    "linkedin": "LinkedIn URL",
    "github": "GitHub URL"
  }},
  "summary": "A professional summary (2-3 sentences max).",
  "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "education": [
    {{ 
      "degree": "Degree Name", 
      "institution": "University Name", 
      "year": "Year", 
      "details": "GPA/Honors" 
    }}
  ],
  "experience": [
    {{ 
      "company": "Company Name", 
      "role": "Job Title", 
      "duration": "Dates", 
      "location": "City", 
      "bullets": ["Achievement 1", "Achievement 2"] 
    }}
  ],
  "projects": [
    {{ 
      "name": "Project Title", 
      "description": "Tech stack and impact." 
    }}
  ],
  "leadership": [
     {{ 
       "role": "Role Name", 
       "description": "Responsibility." 
     }}
  ]
}}

If a field is missing, use empty strings or empty lists. Do not invent data.

CV TEXT:
{cv_text}
"""

class CVGenerator:
    def __init__(self):
        # 1. Model Priority List (Handles Quota Limits)
        self.model_priority = [
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite",
            "models/gemini-flash-latest",
            "models/gemini-pro"
        ]
        
        # 2. Configure Jinja2 for LaTeX-Native Syntax
        # This tells Python to look for \VAR{name} instead of {{ name }}
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(),
            block_start_string='\\BLOCK{',
            block_end_string='}',
            variable_start_string='\\VAR{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            lstrip_blocks=True
        )

    def _get_gemini_response(self, prompt: str) -> str:
        """Robust API caller with failover logic"""
        for model_name in self.model_priority:
            try:
                # print(f"Trying {model_name}...") # Uncomment for debug
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except (ResourceExhausted, ServiceUnavailable):
                print(f"⚠️  Quota hit on {model_name}. Switching...")
                time.sleep(1)
                continue
            except Exception as e:
                print(f"⚠️  Error on {model_name}: {e}. Switching...")
                continue
        
        # If all fail, wait 60s and try the lightweight model again
        print("⏳ All models exhausted. Sleeping 60s to reset quota...")
        time.sleep(60)
        return genai.GenerativeModel("models/gemini-2.0-flash-lite").generate_content(prompt).text

    def extract_structured_data(self, cv_text: str) -> Dict[str, Any]:
        """Sends CV text to LLM and gets JSON back"""
        print("🧠  Structuring CV data...")
        try:
            # Format the prompt
            prompt = CV_STRUCTURING_PROMPT.format(cv_text=cv_text)
            
            # Get response
            raw_response = self._get_gemini_response(prompt)
            
            # Clean Markdown (```json ... ```)
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            
            return json.loads(clean_json)
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            # Return safe fallback to prevent crash
            return {
                "personal_info": {"name": "Error Parsing Data"}, 
                "skills": [], "education": [], "experience": [], "projects": [], "leadership": []
            }

    def inject_missing_skills(self, structured_data: Dict[str, Any], new_skills: list) -> Dict[str, Any]:
        """
        Injects the user-verified skills into the 'skills' list of the CV data.
        """
        if not new_skills:
            return structured_data
            
        print(f"\n💉 Injecting {len(new_skills)} verified skills into CV data...")
        
        # Ensure the 'skills' key exists
        if "skills" not in structured_data:
            structured_data["skills"] = []
            
        # Add new skills if they aren't already there (deduplication)
        current_skills_lower = [s.lower() for s in structured_data["skills"]]
        
        for skill in new_skills:
            if skill.lower() not in current_skills_lower:
                structured_data["skills"].append(skill)
                print(f"   + Added: {skill}")
                
        return structured_data

    def render_cv(self, data: Dict[str, Any], template_name: str) -> str:
        """Injects JSON data into the LaTeX template"""
        print(f"🎨  Filling template: {template_name}...")
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            print(f"❌ Template Rendering Error: {e}")
            raise e

    def save_tex_file(self, content: str, user_name: str, template_name: str) -> str:
        """Saves the filled LaTeX code to a new file"""
        safe_name = "".join([c for c in user_name if c.isalnum() or c == '_']).strip()
        t_name = template_name.replace(".tex", "")
        
        filename = f"{OUTPUT_DIR}/{safe_name}_{t_name}_Optimized.tex"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filename

# MAIN EXECUTION (Standalone Test)
if __name__ == "__main__":
    job_role = input("Enter Target Job Role: ")
    cv_path = input("Enter CV PDF path: ").strip('"')
    
    print("\nSelect Template:")
    print("1. Modern (Two-Column)")
    print("2. ATS Classic (Clean)")
    print("3. Minimalist (Academic)")
    choice = input("Choice (1-3): ").strip()
    
    template_map = {
        "1": "template_1.tex",
        "2": "template_2.tex",
        "3": "template_3.tex"
    }
    selected_template = template_map.get(choice, "template_1.tex")

    # 1. Read PDF
    raw_text = ""
    if os.path.exists(cv_path):
        try:
            from pypdf import PdfReader
            reader = PdfReader(cv_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
            print(f"✅  PDF Loaded ({len(raw_text)} chars).")
        except Exception as e:
            print(f"❌ PDF Error: {e}")
            exit()
    else:
        print("❌ File not found.")
        exit()

    # 2. Run Generator
    generator = CVGenerator()
    
    try:
        # Extract Data
        cv_data = generator.extract_structured_data(raw_text)
        
        # Render LaTeX
        latex_code = generator.render_cv(cv_data, selected_template)
        
        # Save File
        name = cv_data.get('personal_info', {}).get('name', 'User')
        saved_file = generator.save_tex_file(latex_code, name, selected_template)

        print("-" * 30)
        print("✅  SUCCESS! CV Generated.")
        print(f"📂  File saved at: {saved_file}")
        print("👉  Upload this .tex file to Overleaf to get your PDF.")
        print("-" * 30)

    except Exception as e:
        print(f"❌ Failed: {e}")