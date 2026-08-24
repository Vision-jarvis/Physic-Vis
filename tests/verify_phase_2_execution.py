import asyncio
import sys
import os
import re

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from src.graph.workflow import create_graph
from src.core.llm import get_llm

async def run_verification():
    print("🚀 Starting Phase 2 End-to-End Verification (Director's Cut)...")
    
    app = create_graph()
    
    # Prompt that requires camera work (Zoom into details)
    prompt = "Visualize Simple Harmonic Motion. Zoom in on the spring force arrows when explaining Hooke's Law."
    
    print(f"INPUT: {prompt}")
    
    full_state = {}
    
    async for output in app.astream({"user_prompt": prompt}, recursion_limit=15):
        for key, value in output.items():
            print(f"--- NODE: {key} ---")
            
            # Update full state with new values
            if isinstance(value, dict):
                full_state.update(value)
            
            if key == "cinematographer":
                instr = value.get("camera_instructions", {})
                print(f"   🎥 Camera Actions: {len(instr.get('camera_actions', []))}")
                print(f"   ⏱️ Pacing details: {instr.get('pacing', {})}")
            
            if key == "coder":
                code = value.get("code", "")
                print(f"\n📝 GENERATED CODE preview:\n{code[:500]}...\n")
                if "MovingCameraScene" in code:
                    print("   ✅ Detected MovingCameraScene inheritance.")
                else:
                    print("   ❌ WARNING: Standard Scene detected (Expected MovingCameraScene).")
                
                if "self.camera.frame.animate" in code:
                    print("   ✅ Detected camera animation commands.")
                else:
                    print("   ⚠️ No explicit camera animation found in code.")
                    
            if key == "renderer":
                if value.get("video_path"):
                    print(f"   ✅ Video Generated: {value.get('video_path')}")
                else:
                    print(f"   ❌ Render Failed. Logs:\n{value.get('logs')[:500]}...")

    print("\n🔍 Phase 2 Checklist:")
    code = full_state.get("code", "")
    
    checks = {
        "MovingCameraScene": "MovingCameraScene" in code,
        "Camera Animate": "self.camera.frame.animate" in code or "Restore(" in code,
        "Video File": full_state.get("render_output_path") is not None
    }
    
    for check, passed in checks.items():
        print(f"   {'✅' if passed else '❌'} {check}")
        
    if full_state.get("code"):
        print("\n📜 FULL CODE DUMP:")
        print(full_state["code"])


if __name__ == "__main__":
    asyncio.run(run_verification())
