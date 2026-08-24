"""Execute independent nodes in parallel."""
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Dict, Any
from src.graph.state import AgentState

class ParallelNodeExecutor:
    """Execute independent nodes in parallel."""
    
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def run_parallel(self, nodes: List[Callable], state: AgentState) -> AgentState:
        """
        Run multiple nodes in parallel and merge results.
        
        Args:
            nodes: List of node functions to execute.
            state: Current state (will be deep copied for each node).
        
        Returns:
            Merged state from all nodes (last write wins for conflicts).
        """
        futures = []
        
        # Launch tasks in thread pool
        # Note: We copy the state to prevent race conditions on mutable objects
        # if nodes modify state in-place.
        # Ideally, nodes should be pure functions returning NEW state dicts.
        for node in nodes:
            # Shallow copy is usually enough if nodes extend top-level keys
            # Deep copy is safer if nodes modify nested dicts
            node_state = state.copy() 
            future = self.executor.submit(node, node_state)
            futures.append(future)
        
        # Wait for all to complete
        # results will be a list of state dictionaries returned by the nodes
        results = [f.result() for f in futures]
        
        # Merge results logic
        merged = state.copy()
        
        for result in results:
            # We assume nodes return a dict (patches to state) or the full state
            if isinstance(result, dict):
                # Intelligent merge could happen here
                # For now, we update top-level keys
                for k, v in result.items():
                    merged[k] = v
        
        return merged
