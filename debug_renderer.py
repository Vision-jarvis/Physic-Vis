from src.execution.local_runner import ManimExecutor
import os

def debug_render():
    print("🚀 Starting Debug Render...")
    executor = ManimExecutor(output_dir="output")
    
    filename = "scene_e466f7ac.py"
    filepath = os.path.join("output", filename)
    
    if not os.path.exists(filepath):
        print(f"❌ File {filepath} not found!")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    print(f"📜 Code loaded from {filename}")
    
    # Run using the exact same class used in the workflow
    status, logs, video_path = executor.run_code(code)
    
    print(f"\n--- RENDER STATUS: {status} ---")
    print(f"--- VIDEO PATH: {video_path} ---")
    print(f"\n--- LOGS START ---\n{logs}\n--- LOGS END ---")

if __name__ == "__main__":
    debug_render()
