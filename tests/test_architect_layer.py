import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.architect import architect_node

async def test_architect():
    print("\n🧪 Testing Layer 2: Architect Node")
    print("====================================")
    
    mock_state = {
        "user_prompt": "Create a 2D animation showing a red circle transforming into a blue square.",
        "physics_code": {"explanation": "Simple geometric transformation."}
    }
    
    try:
        print(f"INPUT: {mock_state['user_prompt']}")
        result = await architect_node(mock_state)
        print("\n✅ OUTPUT PLAN:")
        print(result.get("plan"))
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_architect())
