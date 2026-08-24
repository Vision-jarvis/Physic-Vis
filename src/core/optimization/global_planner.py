from typing import Dict, List, Optional
import json
from src.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

class GlobalVideoPlanner:
    """Plans entire video in single pass - no redundant LLM calls."""
    
    def plan_complete_video(self, prompt: str, concept_graph: Dict) -> Dict:
        """
        Single LLM call to plan ALL acts at once.
        
        Returns:
            {
                "acts": [...],  # All 3-5 acts
                "shared_context": {...},  # Reusable across acts
                "global_color_scheme": {...},
                "narrative_thread": "..."
            }
        """
        llm = get_llm(temperature=0.7)
        
        system_prompt = """You are planning a complete multi-act physics video.

CRITICAL: Plan ALL acts in ONE response to maintain consistency.

Output JSON:
{
    "video_metadata": {
        "total_duration": 300,
        "complexity": "medium",
        "narrative_thread": "Main idea connecting all acts"
    },
    "shared_context": {
        "key_equation": "F = ma",
        "main_variables": {"F": "BLUE", "m": "YELLOW", "a": "GREEN"},
        "visual_metaphor": "Ball on track"
    },
    "acts": [
        {
            "act_number": 1,
            "type": "hook", # Options: hook, intuition, definition, interaction, conclusion
            "duration": 60,
            "scenes": [
                {
                    "description": "Show ball rolling",
                    "manim_objects": ["Circle", "Arrow"],
                    "camera_move": "zoom_in"
                }
            ],
            "narration_script": "Imagine a ball rolling down a hill..."
        },
        // ... all other acts
    ]
}
"""
        
        user_prompt = f"""Plan complete video for: {prompt}

Concept graph: {json.dumps(concept_graph, indent=2)}

Generate 3-5 acts with complete details for each. Make them flow naturally."""
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        content = response.content if isinstance(response.content, str) else response.content[0]
        
        try:
            # Clean markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            plan = json.loads(content)
            return plan
        except Exception as e:
            print(f"Error parsing global plan: {e}")
            print(f"Raw content: {content}")
            # Fallback minimal plan
            return {
                "video_metadata": {"total_duration": 180, "complexity": "medium"},
                "shared_context": {},
                "acts": [{"act_number": 1, "type": "hook", "scenes": []}]
            }
