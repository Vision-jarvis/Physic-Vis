import sys
import os
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.execution.local_runner import ManimExecutor

def test_renderer():
    print("\n🧪 Testing Layer 5: Renderer Node")
    print("=================================")
    
    # 1. Create a simple test scene
    output_dir = "tests/output"
    os.makedirs(output_dir, exist_ok=True)
    
    scene_code = """
from manim import *

class TestRenderScene(Scene):
    def construct(self):
        c = Circle(color=RED)
        self.play(Create(c), run_time=1)
"""
    scene_path = os.path.join(output_dir, "test_render.py")
    with open(scene_path, "w") as f:
        f.write(scene_code)
        
    print(f"📄 Created test scene: {scene_path}")
    
    # 2. Execute
    runner = ManimExecutor(output_dir=output_dir)
    print("🎬 Starting execution (In-Docker)...")
    
    try:
        # Correct handling of Dict return + Filename only
        result = runner.execute(os.path.basename(scene_path), "TestRenderScene")
        
        success = result.get('success', False)
        logs = result.get('stdout', '') + "\n" + result.get('stderr', '')
        
        print(f"\n✅ Execution Result: {success}")
        
        video_found = False
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".mp4"):
                    video_found = True
                    print(f"🎥 Found video: {os.path.join(root, file)}")
                    break
        
        if success and video_found:
             print("\n✅ Layer 5 PASSED: Video generated.")
        else:
             print("\n❌ Layer 5 FAILED: No video or execution error.")
             if not success:
                 print(f"Logs: {logs}")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    test_renderer()
