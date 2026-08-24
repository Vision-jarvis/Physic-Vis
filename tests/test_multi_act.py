import sys
import os
import asyncio
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.orchestrator import MultiActOrchestrator
from src.graph.nodes.concept_mapper import concept_mapper_node
from src.graph.state import AgentState

async def test_multi_act():
    prompt = "Simple Harmonic Motion"
    print(f"🧪 Testing Multi-Act Workflow for: {prompt}")
    
    # 1. Concept Map
    print("   🧠 Running Concept Mapper...")
    dummy_state = AgentState(user_prompt=prompt, concept_graph={}, retry_count=0)
    concept_state = await concept_mapper_node(dummy_state)
    graph = concept_state["concept_graph"]
    print(f"   ✅ Concepts: {len(graph.get('concepts', []))}")
    
    # 2. Orchestrator
    orchestrator = MultiActOrchestrator()
    
    # Mocking the plan for speed: Force only 2 acts
    # We can subclass or monkeypatch, but let's just run it.
    # To save time, we might modify the plan inside the orchestrator if we could.
    # For now, let's trust it runs the full thing (SHM is 'simple' -> 3 acts).
    
    # For now, let's trust it runs the full thing (SHM is 'simple' -> 3 acts).
    
    final_video = await orchestrator.generate_video(prompt, graph)
    
    if final_video:
        print(f"✅ Test Passed: {final_video}")
    else:
        print("❌ Test Failed: No video returned.")

if __name__ == "__main__":
    asyncio.run(test_multi_act())
