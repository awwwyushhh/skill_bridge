# Skill Verification: This engine acts as the "Interviewer." It takes the list of missing skills, asks the LLM to generate specific Yes/No MCQs for them, and handles the user's answers in the terminal.

import os
import json
import time
import glob
import re
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, NotFound, InvalidArgument, PermissionDenied

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing from .env")

genai.configure(api_key=GEMINI_API_KEY)

class SkillVerifier:
    def __init__(self):
        # UPDATED PRIORITY LIST: Only using models confirmed to exist for my account
        self.model_priority = [
            "models/gemini-2.0-flash-lite",   # Best for simple tasks (Fast/Cheap)
            "models/gemini-2.0-flash",        # Standard
            "models/gemini-flash-latest",     # 1.5 Flash Alias
            "models/gemini-pro-latest"        # 1.5 Pro Alias
        ]

    def _get_gemini_response(self, prompt: str) -> str:
        """
        Robust API caller. Switches models if one fails.
        """
        for model_name in self.model_priority:
            try:
                # print(f"   ...Attempting {model_name}") # Uncomment to debug
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
                
            except (ResourceExhausted, ServiceUnavailable):
                print(f"   ⚠️  Quota hit on {model_name}. Waiting 10s to recover...")
                time.sleep(10)
                continue
            except (NotFound, PermissionDenied, InvalidArgument) as e:
                print(f"   ⚠️  {model_name} error. Switching...")
                continue
            except Exception as e:
                print(f"   ❌ Unexpected error on {model_name}: {e}")
                continue

        # Final Attempt
        print("   ⏳ All models exhausted. Sleeping 60s to FULLY reset quota...")
        time.sleep(60)
        try:
            return genai.GenerativeModel("models/gemini-2.0-flash-lite").generate_content(prompt).text
        except Exception as e:
            print(f"   ❌ Final retry failed: {e}")
            return ""

    def extract_missing_skills_from_pdf(self, pdf_path: str) -> list:
        # Extracts skills and cleans them up
        if not os.path.exists(pdf_path):
            print(f"Error: PDF not found at {pdf_path}")
            return []

        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            lines = text.split('\n')
            extracted_skills = []
            capture_mode = False
            
            for line in lines:
                clean_line = line.strip()
                
                # Start capturing after "Missing Skills" header
                if "Missing Skills" in clean_line and not capture_mode:
                    capture_mode = True
                    continue
                
                # Stop if we hit typical footer/next section markers
                if capture_mode and (clean_line.startswith("Summary") or clean_line.startswith("Matching")):
                    break

                if capture_mode:
                    # Detect bullet points
                    if clean_line.startswith("-") or clean_line.startswith("•"):
                        raw_skill = clean_line.lstrip("-• ").strip()
                        
                        # CLEANUP: Remove parenthetical explanations
                        # Turns "Feature Ownership (No professional history...)" -> "Feature Ownership"
                        simple_skill = re.sub(r'\s*\(.*?\)', '', raw_skill).strip()
                        
                        if simple_skill and len(simple_skill) < 50: 
                            extracted_skills.append(simple_skill)
            
            # LIMIT TO TOP 4 SKILLS as requested
            return extracted_skills[:4]

        except ImportError:
            print("Error: pypdf not installed. Please run 'pip install pypdf'")
            return []
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []

    def generate_questions(self, missing_skills: list) -> list:
        if not missing_skills:
            print("No missing skills to generate questions for.")
            return []

        print(f"Generating short verification questions for: {missing_skills}...")

        prompt = f"""
        You are a Technical Recruiter. A candidate is missing these skills: {missing_skills}.
        
        Generate a very short, crisp question for each skill.
        The question format should strictly be: "Do you have experience with [Skill Name]?"
        
        Return a strict JSON list of objects matching this schema exactly:
        [
            {{
                "skill": "Skill Name",
                "question": "Do you have experience with [Skill Name]?",
                "options": [
                    "1. Yes",
                    "2. No"
                ]
            }}
        ]
        
        Do not output markdown formatting. Return only the raw JSON list.
        """
        
        raw_text = self._get_gemini_response(prompt)
        
        if not raw_text:
            print("❌ AI returned empty response (Check Quota/Permissions).")
            return []

        try:
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"❌ Error parsing JSON. Raw output: {raw_text[:100]}...")
            return []

    def verify_skills_with_user(self, questions: list):
        skills_to_add_to_cv = []
        skills_for_roadmap = []

        print("\n" + "="*50)
        print("🔍 SKILL CHECK")
        print("="*50)
        
        for q in questions:
            # Simple Display
            print(f"🔹 {q['question']}")
            
            while True:
                choice = input("   👉 (1) Yes / (2) No: ").strip()
                if choice == "1":
                    print(f"   ✅ Added '{q['skill']}' to CV.\n")
                    skills_to_add_to_cv.append(q['skill'])
                    break
                elif choice == "2":
                    print(f"   🚀 Sent '{q['skill']}' to Roadmap.\n")
                    skills_for_roadmap.append(q['skill'])
                    break
                else:
                    print("   ⚠️ Invalid input. Enter 1 or 2.")

        return skills_to_add_to_cv, skills_for_roadmap

# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    verifier = SkillVerifier()
    
    # 1. Auto-find latest report
    list_of_files = glob.glob('Skill_Report_*.pdf') 
    
    pdf_path = None
    if list_of_files:
        pdf_path = max(list_of_files, key=os.path.getctime)
        print(f"Found latest report: {pdf_path}")
    else:
        pdf_path = input("Enter path to Skill Gap Report PDF: ").strip('"')

    if pdf_path and os.path.exists(pdf_path):
        # 2. Extract (Will only return top 4 skills now)
        extracted_missing_skills = verifier.extract_missing_skills_from_pdf(pdf_path)
        
        if extracted_missing_skills:
            # 3. Generate Questions (Short & Crisp)
            questions = verifier.generate_questions(extracted_missing_skills)
            
            if questions:
                # 4. Verify
                cv_updates, roadmap_updates = verifier.verify_skills_with_user(questions)
                
                print("\n" + "="*30)
                print("FINAL OUTPUT")
                print(f"CV Updates: {cv_updates}")
                print(f"Roadmap Updates: {roadmap_updates}")
            else:
                print("❌ Failed to generate questions.")
        else:
            print("No missing skills found in the PDF (or parsing failed).")
    else:
        print("PDF file not found.")