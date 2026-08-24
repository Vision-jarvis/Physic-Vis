import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.physicist import physicist_node

async def test_physicist():
    print("\n🧪 Testing Layer 1: Physicist Node")
    print("=======================================")
    
    # Mock Input from ConceptMapper (Simulating Navier-Stokes)
    mock_state = {
        "user_prompt": "Explain the Navier-Stokes equations for fluid dynamics.",
        "concept_graph": {
            "concepts": [
                "Continuity Equation",
                "Momentum Equation (Newton's Second Law for Fluids)",
                "Pressure Gradient",
                "Viscous Forces",
                "Material Derivative"
            ],
            "prerequisites": ["Vector Calculus", "Newton's Laws"]
        }
    }
    
    try:
        print(f"INPUT Concepts: {mock_state['concept_graph']['concepts']}")
        result = await physicist_node(mock_state)
        
        print("\n🔍 FULL RESULT DEBUG:")
        print(result)
        
        physics_data = result.get("physics_code")
        print("\n✅ OUTPUT PHYSICS DATA:")
        print(physics_data)
        
        if physics_data is None:
             print("❌ ERROR: physics_code is None")
             return
        
        # Verification
        # Check for common Navier-Stokes symbols: partials, nabla, rho, mu, or force vectors
        # Note: physics_data is a dict, so we convert to str to check content
        data_str = str(physics_data)
        if any(sym in data_str for sym in ["partial", "nabla", "rho", "mu", "mathbf", "frac"]):
             print("\n✅ Physics Content Check: PASSED (Contains calculus/physics notation)")
        else:
             print("\n❌ Physics Content Check: FAILED (Missing expected symbols)")
             print(f"Debug Raw: {data_str[:200]}...") # Print start of data for debug
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_physicist())
