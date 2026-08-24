import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from src.graph.nodes.architect_batch import architect_batch_node
from src.graph.state import AgentState

async def test_batch():
    print("🚀 Starting Sequential Test for Architect Batch Node...")
    
    state = {
        "user_prompt": "Visualize Simple Harmonic Motion. Zoom in on the spring force arrows when explaining Hooke's Law.",
        "concept_graph": {
            "concept_sequence": ["Hooke's Law", "Restoring Force", "SHM Oscillation"]
        }
    }
    
    print("--- Calling architect_batch_node ---")
    result = await architect_batch_node(state)
    
    print("\n✅ Node Execution Complete.")
    print(f"Keys in result: {result.keys()}")
    
    if "plan" in result:
        print(f"Plan: {json.dumps(result['plan'], indent=2)[:200]}...")
    if "camera_instructions" in result:
        print(f"Camera Actions: {len(result['camera_instructions'].get('actions', []))}")

if __name__ == "__main__":
    asyncio.run(test_batch())
