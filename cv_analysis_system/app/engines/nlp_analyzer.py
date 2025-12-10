# FR-2.1: Handles CV file parsing (PDF/DOCX) and data extraction of skills, experience, etc.

# Purpose: CV Parsing Node for LangGraph Workflow

import os
from PyPDF2 import PdfReader


def parse_cv(file_path: str):
    """
    Extract raw text from PDF or TXT CV.
    Returns clean plain text for LangGraph / console usage.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return None

        # Detect file extension
        file_extension = os.path.splitext(file_path)[1].lower()

        # PDF parsing
        if file_extension == ".pdf":
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()

        # TXT parsing
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()

        # Unsupported file type
        else:
            return None

    except Exception:
        # Any unexpected failure
        return None


def cv_reader_node(state: dict):
    """
    LangGraph node.
    Input state:
        { "cv_file_path": "<path>" }
    Output state:
        { "cv_text": "<extracted text>" }
    """
    file_path = state.get("cv_file_path")
    extracted = parse_cv(file_path)
    return {
        "cv_text": extracted if extracted else ""
    }


if __name__ == "__main__":
    # Sample direct test
    SAMPLE_CV_PATH = r"F:\cv_analyzer\Ux-designer-resume-example-5.pdf"

    extracted_text = parse_cv(SAMPLE_CV_PATH)

    if extracted_text:
        print("CV Content Extracted Successfully\n")
        print(extracted_text)
    else:
        print("Failed to extract content from CV")