import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.feynman import feynman_node

async def test_feynman():
    print("\n🧪 Testing Layer 4: Feynman Node")
    print("====================================")
    
    # Mock State: Navier-Stokes
    mock_state = {
        "user_prompt": "Explain the Navier-Stokes equations for fluid dynamics.",
        "physics_code": {
            "principle": "Navier-Stokes equations",
            "equations": [r"\rho \frac{D \mathbf{v}}{Dt} = -\nabla p + \mu \nabla^2 \mathbf{v} + \mathbf{f}"]
        },
        "concept_graph": {
            "concepts": ["Viscosity", "Momentum", "Pressure"]
        }
    }
    
    try:
        # Run Node
        result = await feynman_node(mock_state)
        analogy = result.get("analogy", {})
        
        print(f"\n✅ Result keys: {result.keys()}")
        print(f"✅ Analogy Text: {analogy.get('analogy_text')}")
        print(f"✅ Visual Metaphor: {analogy.get('visual_metaphor')}")
        
        # Assertions
        if "analogy" in result and "analogy_text" in analogy and len(analogy["analogy_text"]) > 10:
             print("\n✅ Feynman Content Check: PASSED")
        else:
             print("\n❌ Feynman Content Check: FAILED")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_feynman())
