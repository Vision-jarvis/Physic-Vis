import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.cinematographer import cinematographer_node

async def test_cinematographer():
    print("\n🧪 Testing Layer 3: Cinematographer Node")
    print("==========================================")
    
    # Mock State: 3D Fluid Simulation
    mock_state = {
        "user_prompt": "Visualize the 3D velocity field of a fluid.",
        "concept_graph": {"concepts": ["Vector Field", "3D Space"]},
        "physics_code": {
            "principle": "Navier-Stokes",
            "equations": [r"\mathbf{v}(x,y,z,t)"]
        },
        "analogy": {
            "visual_metaphor": "Fly through a storm of arrows representing wind speed."
        }
    }
    
    try:
        # Run Node
        result = await cinematographer_node(mock_state)
        camera_data = result.get("camera_instructions", {})
        
        print(f"\n✅ Result keys: {result.keys()}")
        print(f"✅ Camera Data: {json.dumps(camera_data, indent=2)}")
        
        # Validation
        actions = camera_data.get("camera_actions", [])
        
        # Check for 3D rotation commands (phi, theta)
        has_3d_rotation = any("phi" in str(action) or "theta" in str(action) for action in actions)
        
        if has_3d_rotation:
             print("\n✅ Cinematographer Content Check: PASSED (Generated 3D camera moves)")
        else:
             print("\n⚠️ Cinematographer Content Check: WARNING (No 3D rotation found, might be 2D fallback)")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_cinematographer())
