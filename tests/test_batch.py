import unittest
import os
import sys
import time
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.batch import BatchLLMProcessor

class TestBatchProcessor(unittest.TestCase):
    
    @patch('src.core.batch.ChatGoogleGenerativeAI')
    def test_batch_execution_time(self, MockLLM):
        """
        Verify that requests run in parallel.
        If we run 3 requests that take 0.1s each, total time should be ~0.1s, not 0.3s.
        """
        import asyncio
        
        # Mock behavior: sleep 0.1s then return "ok"
        async def mock_ainvoke(messages):
            await asyncio.sleep(0.1)
            response = MagicMock()
            response.content = f"Response to {messages[0]['content']}"
            return response
            
        # Configure mock
        mock_instance = MockLLM.return_value
        mock_instance.ainvoke.side_effect = mock_ainvoke
        
        processor = BatchLLMProcessor()
        
        requests = [
            {"messages": [{"role": "user", "content": "A"}]},
            {"messages": [{"role": "user", "content": "B"}]},
            {"messages": [{"role": "user", "content": "C"}]}
        ]
        
        start = time.time()
        results = processor.batch_invoke(requests)
        duration = time.time() - start
        
        print(f"\nExecution Duration: {duration:.4f}s")
        
        # Validation
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], "Response to A")
        self.assertEqual(results[1], "Response to B")
        self.assertEqual(results[2], "Response to C")
        
        # Parallel check: Should be significantly faster than serial (0.3s)
        # We allow some overhead, but 0.2s is a safe upper bound for 0.1s parallel tasks
        self.assertLess(duration, 0.25, "Execution should be parallel")

if __name__ == '__main__':
    unittest.main()
