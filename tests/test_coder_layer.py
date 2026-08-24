import asyncio
import sys
import os
import re
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Mock manim if not present
sys.modules["manim"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.coder import coder_node

async def test_coder():
    print("\n🧪 Testing Layer 6: Coder Node")
    print("==================================")
    
    # Mock State: Navier-Stokes Mosh Pit (Full Chain Data)
    mock_state = {
        "user_prompt": "Explain the Navier-Stokes equations for fluid dynamics.",
        "plan": "1. Intro to crowd. 2. Show forces. 3. Show equation.",
        "physics_code": {
             "principle": "Navier-Stokes",
             "equations": [r"\rho \frac{D \mathbf{v}}{Dt} = -\nabla p + \mu \nabla^2 \mathbf{v} + \mathbf{f}"],
             "explanation": "Equation describes flow of viscous fluids."
        },
        "analogy": {
            "analogy_text": "Imagine a mosh pit. Pressure is the crowd pushing you. Viscosity is the friction of bodies rubbing against each other.",
            "visual_metaphor": "Top down view of a concert crowd."
        },
        "camera_instructions": {
            "camera_actions": [{"t": "setup", "action": "set_camera_orientation", "phi": "75 * DEGREES"}],
            "pacing": {"setup": 5, "action": 10}
        },
        "voiceover_script": "Let's visualize a fluid like a chaotic mosh pit."
    }
    
    try:
        # Run Node
        result = await coder_node(mock_state)
        code = result.get("code", "")
        
        print(f"\n✅ Result keys: {result.keys()}")
        print(f"✅ Code Length: {len(code)} chars")
        
        # Validation
        checks = {
            "PhysicsScene Class": "class PhysicsScene" in code,
            "ThreeDScene (due to phi)": "ThreeDScene" in code or "MovingCameraScene" in code, # specific 3D check
            "Layout Helper Import": "from layout_helper import" in code,
            "Smart Position": "smart_position(" in code,
            "No Deprecated ShowCreation": "ShowCreation" not in code,
            "Environment Config": "config.background_color" in code or "#1e1e1e" in code
        }
        
        passed_all = True
        for name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
            if not passed: passed_all = False
            
        if passed_all:
             print("\n✅ Coder Content Check: PASSED")
        else:
             print("\n❌ Coder Content Check: FAILED")
             # Print start of code for debug
             print(f"Code Snippet:\n{code[:500]}...")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_coder())
