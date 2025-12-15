import random
import time
from typing import List, Dict, Any
from roadmap_mvp_state import RoadmapState

def scraper_node(state: RoadmapState) -> RoadmapState:
    """
    LangGraph Node: Simulates searching for courses.
    """
    skills: List[str] = state.get("skills_to_learn", [])
    
    if not skills:
        print("❌ Scraper Node: No skills provided.")
        return {"raw_search_data": {}}
        
    print(f"\n🌐 Scraper Node: Searching for courses for {skills}...")
    
    # Simulate search latency
    time.sleep(1)
    
    raw_search_data = {}
    for skill in skills:
        # Mock results for MVP
        print(f"   🔎 Found results for: {skill}")
        raw_search_data[skill] = [
            f"https://www.coursera.org/search?query={skill}",
            f"https://www.udemy.com/courses/search/?q={skill}",
            f"https://www.edx.org/search?q={skill}"
        ]
        
    print(f"✅ Scraper Node: Found raw search data for {len(raw_search_data)} skills.")
    return {"raw_search_data": raw_search_data}