import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.workflow import create_graph

async def test_graph_integration():
    print("\n🔗 Testing Phase 1 Graph Integration")
    print("====================================")
    
    app = create_graph()
    
    print("✅ Graph Compiled Successfully.")
    
    # 1. Check Entry Point
    # Accessing underlying graph structure
    # This might depend on LangGraph version, but let's try to infer from compiled object
    
    print("\n🔍 Inspecting Workflow Structure:")
    # We can't easily inspect the compiled graph object edges directly without private attributes
    # But we can run a dry-run or check the first node execution
    
    mock_state = {
        "user_prompt": "Explain Torque.",
        "retry_count": 0,
        "logs": []
    }
    
    print(f"🎬 Starting Workflow Execution (Dry Run - single step)")
    
    # Run just the first step
    # We expect 'concept_mapper' to be the first node called
    
    try:
        # We will iterate 1 step
        async for output in app.astream(mock_state):
            node_name = list(output.keys())[0]
            print(f"   👉 Executed Node: {node_name}")
            
            if node_name == "concept_mapper":
                data = output[node_name]
                if "concept_graph" in data:
                    print("   ✅ Concept Graph populated in State.")
                    print(f"   🧠 Concepts: {data['concept_graph'].get('concepts')}")
                    break # Success!
                else:
                    print("   ❌ Concept Mapper ran but returned no graph.")
                    break
            else:
                 print(f"   ❌ WRONG ENTRY POINT. Expected 'concept_mapper', got '{node_name}'")
                 break
                 
    except Exception as e:
        print(f"❌ Graph Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_graph_integration())
