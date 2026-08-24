import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.narrator import narrator_node

async def test_narrator():
    print("\n🧪 Testing Layer 5: Narrator Node")
    print("==================================")
    
    # Mock State: Navier-Stokes Mosh Pit
    mock_state = {
        "user_prompt": "Explain the Navier-Stokes equations for fluid dynamics.",
        "physics_code": {
             "explanation": "Equation describes flow of viscous fluids."
        },
        "analogy": {
            "analogy_text": "Imagine a mosh pit. Pressure is the crowd pushing you. Viscosity is the friction of bodies rubbing against each other. Advection is the momentum of the crowd moving as a whole.",
            "visual_metaphor": "Top down view of a concert crowd."
        },
        "camera_instructions": {
            "pacing": {"setup": 5, "action": 10, "climax": 8}
        }
    }
    
    try:
        # Run Node
        result = await narrator_node(mock_state)
        script_data = result.get("voiceover_script", {})
        
        print(f"\n✅ Result keys: {result.keys()}")
        print(f"✅ Script Data: {json.dumps(script_data, indent=2)}")
        
        # Validation
        # Note: Narrator node returns 'voiceover_script' as a string (the full script)
        if isinstance(script_data, str) and len(script_data) > 50:
            word_count = len(script_data.split())
            estimated_duration = (word_count / 150) * 60 # 150 wpm
            
            print(f"✅ Word Count: {word_count}")
            print(f"✅ Estimated Duration (150wpm): {estimated_duration:.2f}s")
            
            pacing_sum = sum(mock_state["camera_instructions"]["pacing"].values())
            print(f"ℹ️  Visual Pacing Sum: {pacing_sum}s")
            
            if estimated_duration > 0:
                 print("\n✅ Narrator Content Check: PASSED (Script generated)")
            else:
                 print("\n❌ Narrator Content Check: FAILED (Empty script)")
        elif isinstance(script_data, dict) and "script" in script_data:
             # Legacy check just in case
             print("\n⚠️ Narrator returned dict (unexpected but handled)")
        else:
             print("\n❌ Narrator Content Check: FAILED (Script output invalid format or too short)")
             print(f"Type: {type(script_data)}")
             print(f"Value: {script_data}")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_narrator())
