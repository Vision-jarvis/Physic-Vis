from typing import Dict, List, Optional
import json

class VideoArchitect:
    """
    Plans the structure of a multi-act educational video.
    Breaks a complexity topic into 4-5 distinct acts with tailored goals.
    """
    
    ACT_TEMPLATES = {
        "hook": {
            "duration_target": "60",
            "goals": [
                "Pose intriguing question",
                "Show counterintuitive example",
                "Create curiosity gap"
            ],
            "visual_style": "Dynamic, fast-paced, colorful",
            "emotional_beat": "curiosity"
        },
        "intuition": {
            "duration_target": "90",
            "goals": [
                "Build visual intuition",
                "Use analogies and metaphors",
                "Show simple case first"
            ],
            "visual_style": "Clear, minimal, focused",
            "emotional_beat": "understanding"
        },
        "formalism": {
            "duration_target": "120",
            "goals": [
                "Introduce formal notation",
                "Derive key equations step-by-step",
                "Connect symbols to visual meaning"
            ],
            "visual_style": "Precise, equation-heavy, synchronized",
            "emotional_beat": "concentration"
        },
        "examples": {
            "duration_target": "90",
            "goals": [
                "Apply to 2-3 concrete examples",
                "Show parameter variations",
                "Demonstrate edge cases"
            ],
            "visual_style": "Varied, interactive, exploratory",
            "emotional_beat": "confidence"
        },
        # Optional 5th act
        "insights": {
            "duration_target": "60",
            "goals": [
                "Connect to broader concepts",
                "Reveal deeper patterns",
                "Leave with 'aha!' moment"
            ],
            "visual_style": "Synthesizing, zooming out, elegant",
            "emotional_beat": "revelation"
        }
    }
    
    def plan_multi_act_video(self, user_prompt: str, concept_graph: Dict) -> Dict:
        """
        Determines the acts required based on topic complexity.
        """
        complexity = self._assess_complexity(concept_graph)
        
        # Decide structure
        if complexity == "simple":
            acts = ["hook", "intuition", "examples"]
        elif complexity == "medium":
            acts = ["hook", "intuition", "formalism", "examples"]
        else: # complex
            acts = ["hook", "intuition", "formalism", "examples", "insights"]
            
        video_plan = {
            "acts": [],
            "total_duration_estimate": 0,
            "narrative_arc": " -> ".join([self.ACT_TEMPLATES[act]["emotional_beat"] for act in acts])
        }
        
        for i, act_type in enumerate(acts):
            template = self.ACT_TEMPLATES[act_type]
            duration = int(template["duration_target"])
            
            act_plan = {
                "act_number": i + 1,
                "act_type": act_type,
                "scene_name": f"{act_type.capitalize()}Scene",
                "goals": template["goals"],
                "visual_style": template["visual_style"],
                "emotional_beat": template["emotional_beat"],
                "duration_target": duration,
                "content_outline": f"Plan for {act_type}: {user_prompt}"
            }
            
            video_plan["acts"].append(act_plan)
            video_plan["total_duration_estimate"] += duration
            
        return video_plan

    def _assess_complexity(self, concept_graph: Dict) -> str:
        """
        Heuristic to determine topic complexity.
        """
        # If we have many prerequisites or a long sequence, it's complex.
        concepts = concept_graph.get("concepts", [])
        sequence = concept_graph.get("concept_sequence", [])
        
        if len(sequence) >= 6:
            return "complex"
        elif len(sequence) <= 3:
            return "simple"
        return "medium"
