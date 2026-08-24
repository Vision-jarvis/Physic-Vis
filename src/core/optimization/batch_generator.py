from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from src.core.llm import get_llm
from src.knowledge.retriever import retrieve_docs
from langchain_core.messages import SystemMessage, HumanMessage

class BatchCodeGenerator:
    """Generate code for ALL scenes in parallel."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def generate_all_scenes(self, video_plan: Dict) -> Dict[str, str]:
        """
        Generate Manim code for all scenes in parallel.
        
        Returns:
            {"HookScene": "code...", "IntuitionScene": "code...", ...}
        """
        # Extract all unique Manim objects needed across ALL acts
        all_manim_objects = set()
        for act in video_plan["acts"]:
            for scene in act.get("scenes", []):
                all_manim_objects.update(scene.get("manim_objects", []))
        
        # Parallel RAG query
        print(f"\\n📚 Fetching docs for {len(all_manim_objects)} Manim objects (Parallel)...")
        rag_context = {}
        
        # Reuse the executor to fetch docs
        # We need to map futures back to objects
        future_to_obj = {
            self.executor.submit(retrieve_docs, obj): obj 
            for obj in all_manim_objects
        }
        
        for future in as_completed(future_to_obj):
            obj = future_to_obj[future]
            try:
                rag_context[obj] = future.result()
            except Exception as e:
                print(f"  ⚠️ Failed to fetch docs for {obj}: {e}")
                rag_context[obj] = ""

        # Now generate code for each act in parallel
        futures = []
        for act in video_plan["acts"]:
            future = self.executor.submit(
                self._generate_act_code,
                act,
                video_plan.get("shared_context", {}),
                rag_context
            )
            futures.append((act["act_number"], future))
        
        # Collect results
        scene_codes = {}
        for act_num, future in futures:
            try:
                scene_name, code = future.result()
                scene_codes[scene_name] = code
                print(f"  ✓ Generated code for Act {act_num}")
            except Exception as e:
                print(f"  ✗ Failed to generate code for Act {act_num}: {e}")
                
        return scene_codes
    
    def _generate_act_code(self, act: Dict, shared_context: Dict, rag_context: Dict) -> Tuple[str, str]:
        """Generate code for single act."""
        llm = get_llm(temperature=0.5)
        
        scene_name = f"{act['type'].capitalize()}Scene"
        
        # Construct RAG string from context
        relevant_docs = ""
        for scene in act.get("scenes", []):
            for obj in scene.get("manim_objects", []):
                if obj in rag_context:
                    relevant_docs += f"\\n{rag_context[obj]}"
        
        # Simplified prompt - we already have full details
        prompt = f"""Generate Manim code for this act:

Type: {act['type']}
Scenes: {json.dumps(act.get('scenes', []), indent=2)}
Narration: {act.get('narration_script', '')}

Shared Context:
{json.dumps(shared_context, indent=2)}

Relevant Manim Docs:
{relevant_docs[:2000]} # Limit context window

Duration target: {act.get('duration', 60)}s

Use these colors: {shared_context.get('main_variables', {})}

Create class {scene_name}(MovingCameraScene) with construct() method.
CRITICAL: 
1. Inherit from MovingCameraScene.
2. Use self.add_fixed_in_frame_mobjects for HUD.
3. DO NOT use layout_helper.
RETURN ONLY PYTHON CODE, NO MARKDOWN."""
        
        response = llm.invoke([
            SystemMessage(content="You are a Manim expert. Generate clean, working code."),
            HumanMessage(content=prompt)
        ])
        
        code = response.content if isinstance(response.content, str) else response.content[0]
        
        # Extract code
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        # Inject headers and BaseScene
        # NOTE: parallel_renderer handles ffmpeg path injection via env vars
        header = """from manim import *

# Polyfill common missing constants/colors
BROWN_D = "#8B4513"
BROWN = BROWN_D
BROWN_A = "#A52A2A"
UP_LEFT = UL
FRAME_WIDTH = config.frame_width
FRAME_HEIGHT = config.frame_height

class BaseScene(MovingCameraScene):
    def construct(self):
        pass
        
    def wait_for_audio(self):
        # Placeholder for fast rendering
        self.wait(2)
        
    def add_fixed_in_frame_mobjects(self, *mobjects):
        # Polyfill for add_fixed_in_frame_mobjects if missing
        for mobj in mobjects:
            # First try the native method if it exists (on super)
            # But since we are here, it likely didn't exist or we shadowed it?
            # actually checking super() is hard in this dynamic string
            
            # Just add to scene strongly
            self.add(mobj)
            
            # Try to fix in frame if method exists (ManimCE way)
            if hasattr(mobj, "fix_in_frame"):
                try:
                    mobj.fix_in_frame()
                except:
                    pass
            # Or if camera has frame (ManimGL way?)
            elif hasattr(self.camera, "frame"):
                # try to attach to frame? No, keep it simple.
                pass
                
    def remove_fixed_in_frame_mobjects(self, *mobjects):
        # Polyfill for remove_fixed_in_frame_mobjects
        for mobj in mobjects:
            self.remove(mobj)
                
    def get_time(self):
        # Polyfill for get_time (old Manim) -> renderer.time (ManimCE)
        return self.renderer.time

"""
        # Replace inheritance
        code = code.replace("(MovingCameraScene)", "(BaseScene)")
        # If it didn't inherit from MovingCameraScene, force it (regex or simple replace might miss, but relying on prompt for now)
        # Fallback: if it inherited from Scene, change it too
        code = code.replace("(Scene)", "(BaseScene)")
        
        full_code = header + code
        
        return scene_name, full_code
