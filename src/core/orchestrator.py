from src.core.architect_video import VideoArchitect
from src.core.stitcher import VideoStitcher
from src.graph.workflow import create_graph
from src.graph.state import AgentState
import os
import time

class MultiActOrchestrator:
    """
    Manages the lifecycle of a Multi-Act Video:
    1. Plan Acts (Architect)
    2. Generate Each Act (Agent Graph)
    3. Stitch (Stitcher)
    """
    
    def __init__(self):
        self.architect = VideoArchitect()
        self.stitcher = VideoStitcher()
        self.workflow = create_graph()
        
    async def generate_video(self, user_prompt: str, concept_graph: dict) -> str:
        """
        Full pipeline: Prompt -> Plan -> Acts -> Final Video
        """
        print(f"\n🎬 STARTING MULTI-ACT PRODUCTION: '{user_prompt}'")
        
        # 1. Plan
        video_plan = self.architect.plan_multi_act_video(user_prompt, concept_graph)
        print(f"   📝 Plan: {len(video_plan['acts'])} Acts ({video_plan['narrative_arc']})\n")
        
        act_results = []
        
        # 2. Execute Acts
        for act in video_plan["acts"]:
            print(f"   🎥 ACTION: Act {act['act_number']} - {act['act_type'].upper()}")
            print(f"      Goal: {act['goals'][0]}")
            
            # Construct Act-Specific Prompt
            act_prompt = self._create_act_prompt(user_prompt, act)
            
            # Initial State for Graph
            state = AgentState(
                user_prompt=act_prompt,
                concept_graph=concept_graph,
                plan=None,
                physics_code=None,
                code=None,
                logs=None,
                render_output_path=None,
                camera_instructions=None,
                analogy=None,
                voiceover_script=None,
                retry_count=0,
                error=None
            )
            
            # Run Graph
            try:
                final_state = await self.workflow.ainvoke(state)
                
                video_path = final_state.get("render_output_path")
                success = bool(video_path and os.path.exists(video_path))
                
                if success:
                    print(f"      ✅ Act {act['act_number']} Complete.")
                    # Rename likely to avoid overwrite? 
                    # The graph outputs to `output/media/...`. 
                    # Ideally we move it to a staging folder.
                    
                else:
                    print(f"      ❌ Act {act['act_number']} Failed.")
                
                act_results.append({
                    "act_number": act["act_number"],
                    "act_type": act["act_type"],
                    "success": success,
                    "video_path": video_path
                })
                
            except Exception as e:
                print(f"      ❌ Act Execution Error: {e}")
                act_results.append({"success": False})

        # 3. Stitch
        output_name = f"final_{int(time.time())}.mp4"
        output_path = os.path.join("output", output_name)
        
        try:
            final_path = self.stitcher.stitch_acts(act_results, output_path)
            return final_path
        except Exception as e:
            print(f"   ⚠️ Stitching failed: {e}")
            return None

    def _create_act_prompt(self, base_prompt: str, act: dict) -> str:
        """
        Specialize the prompt for the specific act.
        """
        visual_style = act["visual_style"]
        goals = "\n- ".join(act["goals"])
        
        return f"""
        TOPIC: {base_prompt}
        CONTEXT: This is Act {act['act_number']} of a multi-part video.
        
        ACT TYPE: {act['act_type'].upper()}
        EMOTIONAL BEAT: {act['emotional_beat']}
        VISUAL STYLE: {visual_style}
        
        GOALS:
        - {goals}
        
        DURATION TARGET: {act['duration_target']} seconds.
        
        Create a dedicated scene for this specific act.
        """
