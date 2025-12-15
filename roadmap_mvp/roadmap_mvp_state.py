# roadmap_mvp/roadmap_mvp_state.py

from typing import TypedDict, List, Dict, Any, Optional

class RoadmapState(TypedDict):
    """The state object shared across the roadmap generation workflow."""
    skills_to_learn: List[str]               # Input: Skills provided by the user
    raw_search_data: Dict[str, Any]          # Output of Scraper Node: Raw text/data from search tool
    final_roadmap_json: Optional[Dict[str, Any]] # Output of Generator Node: Clean, structured JSON roadmap