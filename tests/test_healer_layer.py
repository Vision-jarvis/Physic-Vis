import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.healer import healer_node

async def test_healer():
    print("\n🧪 Testing Layer 7: Healer Node")
    print("================================")
    
    # Mock State: Failed Render
    broken_code = """
from manim import *
class PhysicsScene(Scene):
    def construct(self):
        c = Circle()
        # Deprecated/Wrong method
        p = c.point_from_angle(PI) 
        self.play(Create(c))
"""
    
    error_log = """
Traceback (most recent call last):
  File "scene.py", line 5, in construct
    p = c.point_from_angle(PI)
AttributeError: 'Circle' object has no attribute 'point_from_angle'. Did you mean: 'point_at_angle'?
"""

    mock_state = {
        "user_prompt": "Draw a circle and a point.",
        "code": broken_code,
        "renderer_output": {"error": error_log, "success": False}
    }
    
    try:
        # Run Node
        result = await healer_node(mock_state)
        fixed_code = result.get("code", "")
        
        print(f"\n✅ Result keys: {result.keys()}")
        print(f"✅ Code Length: {len(fixed_code)} chars")
        
        # Validation
        checks = {
            "Fixed Method": "point_at_angle" in fixed_code,
            "Removed Broken Method": "point_from_angle" not in fixed_code,
            "Valid Python": "class PhysicsScene" in fixed_code
        }
        
        passed_all = True
        for name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
            if not passed: passed_all = False
            
        if passed_all:
             print("\n✅ Healer Content Check: PASSED")
        else:
             print("\n❌ Healer Content Check: FAILED")
             print(f"Fixed Snippet:\n{fixed_code}...")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_healer())
