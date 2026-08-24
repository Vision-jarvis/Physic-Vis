import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.workflow import create_graph

# Initialize App
app = create_graph()

async def run_integration_test():
    print("\n🚀 Starting Phase 4 Integration Test: 'Heisenberg Uncertainty Principle'")
    print("=======================================================================")
    
    user_prompt = "Explain the Heisenberg Uncertainty Principle using the analogy of a camera shutter speed."
    
    # Run the full graph
    inputs = {"user_prompt": user_prompt}
    
    print(f"\nINPUT: {user_prompt}")
    
    try:
        final_state = await app.ainvoke(inputs)
        
        # Check Final Output
        video_path = final_state.get("video_path")
        
        print("\n✅ Execution Complete.")
        
        if video_path and os.path.exists(video_path):
             print(f"✅ Video Generated Successfully: {video_path}")
             print("🎉 SYSTEM INTEGRATION VERIFIED.")
        else:
             print("❌ Video Generation Failed (Path invalid or missing).")
             print(f"Final State Logs: {final_state.get('logs', 'No logs')}")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
