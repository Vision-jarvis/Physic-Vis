import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph.workflow import create_graph

async def run_verification():
    print("🚀 Starting PHASE 3 End-to-End Verification (The Guide)...")
    
    app = create_graph()
    
    # Prompt: Something abstract that needs an analogy
    prompt = "Explain Voltage and Current concepts."
    print(f"INPUT: {prompt}")
    
    full_state = {}
    
    max_steps = 25
    step_count = 0
    
    async for output in app.astream({"user_prompt": prompt}, recursion_limit=max_steps):
        step_count += 1
        for key, value in output.items():
            print(f"--- NODE: {key} ---")
            
            # Update full state
            if isinstance(value, dict):
                full_state.update(value)
            
            if key == "feynman":
                analogy = value.get("analogy", {})
                print(f"   💡 Analogy: {analogy.get('analogy_text', '')[:100]}...")
                print(f"   🖼️ Visual: {analogy.get('visual_metaphor', '')}")
                
            if key == "narrator":
                script = value.get("voiceover_script", "")
                print(f"   🎙️ Script Length: {len(script)} chars")
                print(f"   📜 Snippet: {script[:100]}...")
            
            if key == "renderer":
                if value.get("video_path"):
                    print(f"   ✅ Video Generated: {value.get('video_path')}")
                else:
                    print(f"   ❌ Render Failed.")
                    print(f"   📜 ERROR LOGS:\n{value.get('logs', 'No logs available')}")

    print("\n🔍 Phase 3 Checklist:")
    
    checks = {
        "Feynman Data": full_state.get("analogy", {}).get("analogy_text") is not None,
        "Narrator Script": full_state.get("voiceover_script") is not None,
        "Video File": full_state.get("video_path") is not None
    }
    
    for check, passed in checks.items():
        print(f"   {'✅' if passed else '❌'} {check}")

if __name__ == "__main__":
    asyncio.run(run_verification())
