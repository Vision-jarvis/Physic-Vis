import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.workflow import create_graph
from src.execution.local_runner import LocalDockerRunner
from dotenv import load_dotenv

# Ensure env vars are loaded
load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Newton's Architect - CLI")
    parser.add_argument("--prompt", type=str, required=True, help="The physics simulation to generate")
    args = parser.parse_args()
    
    # 1. build graph
    app = create_graph()
    
    print(f"🚀 Starting Generation for: '{args.prompt}'")
    
    # 2. Run the chain (Architect -> Physicist -> Coder)
    # 2. Run the chain (Architect -> Physicist -> Coder -> Renderer -> Healer?)
    try:
        # Initialize state with retry_count = 0
        result_state = await app.ainvoke({
            "user_prompt": args.prompt,
            "retry_count": 0
        })
    except Exception as e:
        print(f"❌ Graph Execution Failed: {e}")
        return
    
    # 3. Output Result
    video_path = result_state.get("video_path")
    error = result_state.get("error")
    logs = result_state.get("logs", "No logs")
    code = result_state.get("code", "No code")

    print("\n📜 Final Code:")
    print("-" * 40)
    print(code)
    print("-" * 40)
    
    if video_path and not error:
        print(f"\n✅ Success! Video saved at: {video_path}")
    else:
        print(f"\n❌ Rendering Failed after self-healing attempts.")
        print(f"Error: {error}")
        print("-" * 20 + " Logs " + "-" * 20)
        print(logs)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
