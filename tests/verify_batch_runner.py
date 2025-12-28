import os
import json
import asyncio
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.workflow import create_graph

OUTPUT_DIR = "tests/batch_verification_output"

TEST_CONCEPTS = [
    {"topic": "Classical Mechanics", "concept": "Newton's First Law", "manim_visual_cues": "Show a block moving on a frictionless surface vs rough surface."},
    {"topic": "Waves", "concept": "Simple Harmonic Motion", "manim_visual_cues": "Visualize a pendulum and its corresponding sine wave graph side-by-side."},
    {"topic": "Optics", "concept": "Refraction", "manim_visual_cues": "Show a light ray bending as it passes from air to water (Snell's Law)."},
    {"topic": "Electromagnetism", "concept": "Lenz's Law", "manim_visual_cues": "Show a magnet moving through a coil and the induced current opposing the motion."},
    {"topic": "Quantum Mechanics", "concept": "Heisenberg Uncertainty Principle", "manim_visual_cues": "Visualize the trade-off between position and momentum wave packets."}
]

async def run_verification_batch():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"🚀 Starting Verification Batch ({len(TEST_CONCEPTS)} items)...")
    app = create_graph()
    
    success_count = 0
    
    for i, item in enumerate(TEST_CONCEPTS):
        topic = item['topic']
        concept = item['concept']
        print(f"\n[{i+1}/{len(TEST_CONCEPTS)}] 🎬 Processing: {concept} ({topic})")
        
        inputs = {
            "user_prompt": f"Create a cinematic Manim animation about {concept}. {item['manim_visual_cues']}",
            "retry_count": 0
        }
        
        try:
            result = await app.ainvoke(inputs, {"recursion_limit": 50})
            
            video_path = result.get("video_path")
            if video_path and os.path.exists(video_path):
                print(f"   ✅ SUCCESS: {video_path}")
                success_count += 1
                
                # Copy to output dir for easy viewing
                safe_name = f"{topic}_{concept}".replace(" ", "_").replace("'", "")
                dest = os.path.join(OUTPUT_DIR, f"{safe_name}.mp4")
                import shutil
                shutil.copy(video_path, dest)
                print(f"   💾 Saved to: {dest}")
                
                # Check if it was fixed by Healer/RAG
                if result.get("original_error"):
                    print(f"   🧠 RAG HEALED this item! (Method: {result.get('fix_method')})")
                    
            else:
                print(f"   ❌ FAILED: {result.get('error')}")
                print(f"   Logs: {str(result.get('logs'))[-300:]}")
                
        except Exception as e:
            print(f"   💥 CRASH: {e}")
            
    print(f"\n🏁 Verification Complete! Success Rate: {success_count}/{len(TEST_CONCEPTS)}")

if __name__ == "__main__":
    asyncio.run(run_verification_batch())
