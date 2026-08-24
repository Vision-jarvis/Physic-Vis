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
    parser.add_argument("--multi-act", action="store_true", help="Generate a multi-act long-form video.")
    args = parser.parse_args()
    
    if args.multi_act:
        from src.core.orchestrator import MultiActOrchestrator
        from src.graph.nodes.concept_mapper import concept_mapper_node
        from src.graph.state import AgentState
        
        runner = MultiActOrchestrator()
        print("🧠 Generating Concept Graph...")
        # Create a dummy state just for concept mapper
        dummy_state = AgentState(user_prompt=args.prompt, concept_graph={}, retry_count=0)
        
        concept_state = await concept_mapper_node(dummy_state)
        
        final_video = await runner.generate_video(args.prompt, concept_state["concept_graph"])
        print(f"🎉 Final Video: {final_video}")
        return

    
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
    video_path = result_state.get("render_output_path")
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
