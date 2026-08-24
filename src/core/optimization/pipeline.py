from typing import Dict
import time
import os
from src.core.optimization.global_planner import GlobalVideoPlanner
from src.core.optimization.batch_generator import BatchCodeGenerator
from src.core.optimization.parallel_renderer import ParallelRenderer
from src.core.optimization.fast_stitcher import FastVideoStitcher
from src.graph.nodes.concept_mapper import concept_mapper_node
from src.graph.nodes.concept_mapper import concept_mapper_node


BASE_SCENE_HEADER = """from manim import *

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
                pass
                
    def remove_fixed_in_frame_mobjects(self, *mobjects):
        # Polyfill for remove_fixed_in_frame_mobjects
        for mobj in mobjects:
            self.remove(mobj)
                
    def get_time(self):
        # Polyfill for get_time (old Manim) -> renderer.time (ManimCE)
        return self.renderer.time

"""

def create_initial_state(prompt: str, mode: str) -> Dict:
    """Create initial state for pipeline."""
    return {
        "user_prompt": prompt,
        "plan": None,
        "physics_code": None,
        "code": None,
        "logs": None,
        "render_output_path": None,
        "concept_graph": None,
        "color_scheme": None,
        "camera_instructions": None,
        "analogy": None,
        "voiceover_script": None,
        "parameter_sweep": None,
        "retry_count": 0,
        "error": None,
        "original_error": None,
        "original_code": None,
        "fix_method": None
    }

class FastMultiActPipeline:
    """Complete optimized pipeline for multi-minute videos."""
    
    def __init__(self):
        self.planner = GlobalVideoPlanner()
        self.code_generator = BatchCodeGenerator(max_workers=4)
        self.renderer = ParallelRenderer(max_parallel=3)
        self.stitcher = FastVideoStitcher()
    
    def generate(self, prompt: str, concept_graph: Dict = None) -> str:
        """
        Generate complete multi-minute video in optimized fashion.
        """
        start_time = time.time()
        
        # Step 0: Concept mapping (if not provided)
        if concept_graph is None:
            print("\\n🧠 Analyzing concept structure...")
            import asyncio
            state = create_initial_state(prompt, "ConceptMap")
            # Run async node in sync context
            state = asyncio.run(concept_mapper_node(state))
            concept_graph = state["concept_graph"]
        
        # Step 1: Global planning (1 LLM call for everything)
        print("\\n🎬 Planning complete video structure...")
        plan_start = time.time()
        video_plan = self.planner.plan_complete_video(prompt, concept_graph)
        plan_time = time.time() - plan_start
        
        num_acts = len(video_plan["acts"])
        print(f"✓ Planned {num_acts} acts in {plan_time:.1f}s")
        
        # Step 2: Parallel code generation
        print("\\n💻 Generating code for all scenes...")
        code_start = time.time()
        scene_codes = self.code_generator.generate_all_scenes(video_plan)
        code_time = time.time() - code_start
        print(f"✓ Generated {len(scene_codes)} scenes in {code_time:.1f}s")
        
        # Step 3: Parallel rendering
        print("\\n🎥 Rendering all scenes...")
        render_start = time.time()
        
        # Initial render of all scenes
        scenes_to_render = scene_codes
        all_results = {}
        
        # Retry loop for healing
        max_retries = 3
        curr_retry = 0
        
        while curr_retry <= max_retries:
            if not scenes_to_render:
                break
                
            # Render current batch
            batch_results = self.renderer.render_all_scenes(scenes_to_render)
            all_results.update(batch_results) # Update global results
            
            # Check failures
            failed_scenes = {
                name: res for name, res in batch_results.items() 
                if not res["success"]
            }
            
            if not failed_scenes:
                print("  ✓ All scenes rendered successfully.")
                break
                
            if curr_retry == max_retries:
                print(f"  ❌ Max retries reached. Failed scenes: {list(failed_scenes.keys())}")
                break
                
            # Trigger Healer for failed scenes
            print(f"\\n  🩹 Healing {len(failed_scenes)} failed scenes (Attempt {curr_retry+1}/{max_retries})...")
            
            healed_codes = self._heal_failures(failed_scenes, scenes_to_render, video_plan)
            
            if not healed_codes:
                print("  ⚠️ Healer could not generate fixes.")
                break
                
            # Prepare next batch
            scenes_to_render = healed_codes
            # Update main code store
            scene_codes.update(healed_codes)
            
            curr_retry += 1
            
        render_time = time.time() - render_start
        
        successful = sum(1 for r in all_results.values() if r["success"])
        print(f"✓ Rendered {successful}/{len(scene_codes)} scenes in {render_time:.1f}s")
        
        # Step 4: Stitch together
        # Order matters!
        video_paths = []
        for act in video_plan["acts"]:
            scene_name = f"{act['type'].capitalize()}Scene"
            if scene_name in all_results and all_results[scene_name]["success"]:
                video_paths.append(all_results[scene_name]["render_output_path"])
        
        if not video_paths:
            raise RuntimeError("No successful renders to stitch")
        
        output_path = f"output/videos/fast_complete_{str(int(time.time()))}.mp4"
        os.makedirs("output/videos", exist_ok=True)
        final_video = self.stitcher.stitch_with_transitions(video_paths, output_path)
        
        total_time = time.time() - start_time
        
        # Report
        print(f"\\n{'='*80}")
        print(f"✓ VIDEO GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"  Planning:    {plan_time:6.1f}s")
        print(f"  Coding:      {code_time:6.1f}s")
        print(f"  Rendering:   {render_time:6.1f}s")
        print(f"  Stitching:   {time.time() - render_start - render_time:6.1f}s")
        print(f"  {'─'*40}")
        print(f"  TOTAL:       {total_time:6.1f}s ({total_time/60:.1f} min)")
        print(f"  Output:      {final_video}")
        print(f"{'='*80}\\n")
        
        return final_video



    def _heal_failures(self, failed_scenes: Dict, current_codes: Dict, plan: Dict) -> Dict[str, str]:
        """Run healer on failed scenes in parallel."""
        import asyncio
        from src.graph.nodes.healer import healer_node
        import re
        
        healed_codes = {}
        
        # Helper to run async healer for one scene
        async def heal_single(name, error_res, code):
            # Find Act topic for context
            topic = "General Physics"
            for act in plan["acts"]:
                if f"{act['type'].capitalize()}Scene" == name:
                    topic = act.get("description", topic)
                    break
            
            # Construct mini-state
            state = {
                "code": code,
                "logs": error_res["error"],
                "retry_count": 0, # Healer manages its own internal logic, but we track loop here
                "physics_code": {"topic": topic}
            }
            
            try:
                # Healer returns updated state
                new_state = await healer_node(state)
                if new_state and "code" in new_state and not new_state.get("error"):
                    raw_healed_code = new_state["code"]
                    
                    # Force inject robust BaseScene header
                    # Find start of the main scene class
                    match = re.search(f"class {name}", raw_healed_code)
                    if match:
                        body = raw_healed_code[match.start():]
                        # Ensure we inherit from BaseScene in the body
                        body = body.replace(f"class {name}(MovingCameraScene)", f"class {name}(BaseScene)")
                        body = body.replace(f"class {name}(Scene)", f"class {name}(BaseScene)")
                        return name, BASE_SCENE_HEADER + "\n" + body
                    else:
                        print(f"  ⚠️ Healer returned no header match for {name}")
                        # Fallback: Just return what Healer gave if we can't find class def
                        # But warn or try to prepend if it looks like just a class
                        return name, raw_healed_code
                else:
                    print(f"  ⚠️ Healer returned invalid state for {name}: {new_state.keys() if new_state else 'None'}")
                    if new_state and "error" in new_state:
                         print(f"  ⚠️ Healer error detail: {new_state['error']}")
                        
            except Exception as e:
                print(f"  ❌ Healer exception for {name}: {e}")
            return name, None

        # Run all heals
        async def run_batch():
            tasks = []
            for name, res in failed_scenes.items():
                code = current_codes[name]
                tasks.append(heal_single(name, res, code))
            return await asyncio.gather(*tasks)
            
        results = asyncio.run(run_batch())
        
        for name, new_code in results:
            if new_code:
                healed_codes[name] = new_code
                
        return healed_codes
