# roadmap_mvp/main.py

from langgraph.graph import StateGraph, END
from roadmap_mvp_state import RoadmapState
from scraper_node import scraper_node
from generator_node import generator_node
import json
import os # Import the os module for path handling

# ... (build_roadmap_graph function remains unchanged) ...

def build_roadmap_graph():
    """Builds and compiles the two-node LangGraph workflow."""
    graph = StateGraph(RoadmapState)
    
    graph.add_node("search_courses", scraper_node)
    graph.add_node("synthesize_links", generator_node)
    
    graph.set_entry_point("search_courses")
    graph.add_edge("search_courses", "synthesize_links")
    graph.add_edge("synthesize_links", END)
    
    return graph.compile()


def run_roadmap_mvp():
    print("=" * 50)
    print("Roadmap Generation MVP Test")
    print("=" * 50)
    
    skills_input = input("Enter missing skills (comma-separated, e.g., Figma, Advanced SQL): ")
    skills_to_test = [s.strip() for s in skills_input.split(',') if s.strip()]
    
    if not skills_to_test:
        print("No skills entered. Exiting.")
        return
    
    workflow = build_roadmap_graph()
    initial_state = RoadmapState(
        skills_to_learn=skills_to_test,
        raw_search_data={},
        final_roadmap_json=None
    )

    try:
        print(f"\n🚀 Running workflow for: {skills_to_test}...")
        final_state = workflow.invoke(initial_state)

        roadmap = final_state.get("final_roadmap_json", {"error": "No output generated."})
        
        # --- NEW CODE TO WRITE TO FILE ---
        output_filename = "upskilling_roadmap.json"
        
        # Convert Python dictionary to a JSON formatted string
        json_output_string = json.dumps(roadmap, indent=4)
        
        # Write the string to a file
        with open(output_filename, 'w') as f:
            f.write(json_output_string)
            
        # Get the absolute path for clean output
        absolute_path = os.path.abspath(output_filename)
        # --- END NEW CODE ---

        print("\n" + "=" * 50)
        print("✅ WORKFLOW COMPLETE!")
        print(f"📄 FINAL ROADMAP SAVED TO: {absolute_path}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ CRITICAL WORKFLOW FAILURE: {e}")

if __name__ == "__main__":
    run_roadmap_mvp()