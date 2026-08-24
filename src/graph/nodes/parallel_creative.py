from src.graph.state import AgentState
from src.graph.nodes.architect_batch import architect_batch_node
from src.graph.nodes.feynman import feynman_node
import asyncio

async def parallel_creative_node(state: AgentState):
    """
    Executes Creative Layers in Parallel using asyncio.gather:
    1. Feynman (Analogy)
    2. Architect Batch (Visual Plan + Camera)
    
    Optimization: Parallelizes Thinking vs Planning using native async concurrency.
    """
    print("--- NODE: Parallel Creative (Feynman + Architect) [ASYNC] ---")
    
    # Launch both nodes concurrently in the same event loop
    # They are both async functions, so this is trivial and thread-safe.
    task_feynman = feynman_node(state)
    task_architect = architect_batch_node(state)
    
    results = await asyncio.gather(task_feynman, task_architect, return_exceptions=True)
    
    merged_result = state.copy()
    
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"   ❌ Parallel Sub-node {i} failed: {res}")
            continue
        if isinstance(res, dict):
             for k, v in res.items():
                 merged_result[k] = v
                 
    return merged_result
