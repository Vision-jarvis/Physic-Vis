import unittest
import os
import sys
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution.parallel import ParallelNodeExecutor

class TestParallelExecutor(unittest.TestCase):
    
    def test_parallel_execution_and_merge(self):
        """
        Run two dummy nodes that sleep 0.1s.
        Total time should be ~0.1s, not 0.2s.
        """
        def node_a(state):
            time.sleep(0.1)
            return {"result_a": "A done"}
            
        def node_b(state):
            time.sleep(0.1)
            return {"result_b": "B done"}
            
        executor = ParallelNodeExecutor(max_workers=2)
        initial_state = {"user_prompt": "Test"}
        
        start = time.time()
        merged = executor.run_parallel([node_a, node_b], initial_state)
        duration = time.time() - start
        
        print(f"\nExecution Duration: {duration:.4f}s")
        
        # 1. Check Merge
        self.assertEqual(merged["result_a"], "A done")
        self.assertEqual(merged["result_b"], "B done")
        self.assertEqual(merged["user_prompt"], "Test") # Preserved
        
        # 2. Check Parallelism
        self.assertLess(duration, 0.15, "Should run in parallel (approx 0.1s)")

if __name__ == '__main__':
    unittest.main()
