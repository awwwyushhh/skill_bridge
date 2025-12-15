import os

# --- Configuration for Roadmap MVP ---
PROJECT_NAME = "roadmap_mvp"

# Define the structure as a list of paths
# We include the subdirectory for clarity, but os.makedirs handles it.
structure_paths = [
    PROJECT_NAME,
]

# Files to create (paths relative to the PROJECT_NAME root)
files_to_create = [
    os.path.join(PROJECT_NAME, "main.py"),
    os.path.join(PROJECT_NAME, "generator_node.py"),
    os.path.join(PROJECT_NAME, "scraper_node.py"),
    os.path.join(PROJECT_NAME, "roadmap_mvp_state.py"),
    os.path.join(PROJECT_NAME, "requirements.txt"),
    os.path.join(PROJECT_NAME, "README.md"),
]

def create_roadmap_structure():
    """Creates the necessary directories and empty files for the MVP."""
    
    # 1. Create the root folder
    try:
        os.makedirs(PROJECT_NAME, exist_ok=True)
        print(f"✅ Directory '{PROJECT_NAME}' created (or already exists).")
    except Exception as e:
        print(f"❌ FATAL ERROR: Could not create base directory '{PROJECT_NAME}'. Check permissions.")
        print(f"Details: {e}")
        return

    # 2. Create the files
    for file_path in files_to_create:
        try:
            # os.makedirs ensures the parent directories exist (redundant here, but safe)
            # We use 'w' to create an empty file
            with open(file_path, 'w') as f:
                f.write("# File created automatically for setup." + "\n")
            print(f"   Created file: {file_path}")
        except Exception as e:
            print(f"❌ Error creating file {file_path}: {e}")
            
    print("\n✅ Roadmap MVP structure creation complete!")

if __name__ == "__main__":
    create_roadmap_structure()