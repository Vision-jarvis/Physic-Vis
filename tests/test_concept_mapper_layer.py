import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env before imports that might need it
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.concept_mapper import concept_mapper_node

async def test_concept_mapper():
    print("\n🧪 Testing Layer 0: Concept Mapper Node")
    print("=======================================")
    
    mock_state = {
        "user_prompt": "Explain the Navier-Stokes equations for fluid dynamics.",
    }
    
    try:
        print(f"INPUT: {mock_state['user_prompt']}")
        result = await concept_mapper_node(mock_state)
        
        graph_data = result.get("concept_graph")
        print("\n✅ OUTPUT GRAPH:")
        print(graph_data)
        
        # Validation
        if graph_data and "concepts" in graph_data and "prerequisites" in graph_data:
            print("\n✅ Structure Check: PASSED")
            print(f"   Concepts: {len(graph_data['concepts'])}")
        else:
             print("\n❌ Structure Check: FAILED (Missing keys)")
             
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_concept_mapper())
