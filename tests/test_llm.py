import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.getcwd())

from src.graph.nodes.physicist import physicist_node
from src.graph.state import AgentState

load_dotenv()

async def test_physicist():
    print("🧪 Testing Physicist Node (Gemini 2.0)...")
    
    # Mock State
    state = AgentState(
        user_prompt="Visualize a simple pendulum",
        plan="Scene: A pendulum swinging. Object: Line and Circle.",
        physics_code=None,
        code=None,
        logs=None,
        video_path=None,
        retry_count=0,
        error=None
    )
    
    try:
        result = await physicist_node(state)
        print("\n✅ Physicist Node Success!")
        print(f"Output: {result['physics_code']}")
    except Exception as e:
        print(f"\n❌ Physicist Node Failed: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_physicist())
