import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv()

from src.graph.workflow import create_graph

async def run_phase_1_test():
    print("\n🚀 Starting Phase 1 End-to-End Verification")
    print("===========================================")
    print("Goal: Verify ConceptMapper -> Graph -> StyleGuide -> Renderer")
    
    app = create_graph()
    
    # "3B1B-style" Request
    user_prompt = "Explain Simple Harmonic Motion using a mass on a spring. Show the restoration force vector."
    
    initial_state = {
        "user_prompt": user_prompt,
        "retry_count": 0,
        "logs": []
    }
    
    print(f"\n📝 User Prompt: {user_prompt}")
    
    print("\n⏳ Executing Graph (This may take 1-2 minutes)...")
    
    try:
        final_state = await app.ainvoke(initial_state)
        
        # 1. Check ConceptMapper Output
        print("\n🔍 Checking Step 1: ConceptMapper")
        concepts = final_state.get("concept_graph", {}).get("concepts", [])
        if concepts:
            print(f"   ✅ Concepts Identified: {concepts}")
        else:
            print("   ❌ ConceptMapper failed to produce key concepts.")

        # 2. Check Code for Style Checks
        print("\n🔍 Checking Step 2: 3B1B Style Enforcement")
        code = final_state.get("code", "")
        # Check for Dark Background and specific colors
        if 'config.background_color = "#1e1e1e"' in code or "#1e1e1e" in code:
            print("   ✅ Dark Background Detected (#1e1e1e).")
        else:
            print("   ⚠️ Potential Style Violation: Background color not found.")
            
        if "#58C4DD" in code or "BLUE_C" in code: # 3B1B Blue
             print("   ✅ 3B1B Blue Detected.")
        
        # 3. Check Video Output
        print("\n🔍 Checking Step 3: Renderer")
        video_path = final_state.get("render_output_path")
        if video_path and os.path.exists(video_path):
            print(f"   ✅ Video Generated Successfully: {video_path}")
        else:
            print(f"   ❌ Video Generation Failed. Path: {video_path}")
            if final_state.get("error"):
                print(f"   ⚠️ Error Triggered: {final_state.get('error')}")

    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_phase_1_test())
