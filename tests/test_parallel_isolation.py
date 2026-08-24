import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from src.graph.nodes.parallel_creative import parallel_creative_node
from src.graph.state import AgentState

async def test_parallel():
    print("🚀 Starting Isolation Test for Parallel Creative Node...")
    
    state = {
        "user_prompt": "Visualize Simple Harmonic Motion. Zoom in on the spring force arrows when explaining Hooke's Law.",
        "concept_graph": {
            "concept_sequence": ["Hooke's Law", "Restoring Force", "SHM Oscillation"]
        },
        "physics_code": {
            "equations": ["F = -kx"],
            "explanation": "Hooke's Law states that the force is proportional to displacement."
        }
    }
    
    # parallel_creative_node is sync (internal threading)
    print("--- Calling parallel_creative_node ---")
    result = parallel_creative_node(state)
    
    print("\n✅ Node Execution Complete.")
    print(f"Keys in result: {result.keys()}")
    
    if "analogy" in result:
        print(f"Analogy: {result['analogy'].get('analogy_text')[:100]}...")
    if "plan" in result:
        print(f"Plan: {result['plan'].get('visual_plan')[:100]}...")
    if "camera_instructions" in result:
        print(f"Camera Actions: {len(result['camera_instructions'].get('actions', []))}")

if __name__ == "__main__":
    asyncio.run(test_parallel())
