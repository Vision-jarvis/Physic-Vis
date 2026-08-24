import unittest
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.architect_batch import architect_batch_node

class TestArchitectBatch(unittest.TestCase):
    
    @patch('src.graph.nodes.architect_batch.BatchLLMProcessor')
    def test_node_logic(self, MockProcessor):
        # Setup Mock
        mock_instance = MockProcessor.return_value
        
        # Mock responses (Strings containing Markdown JSON)
        architect_resp = """
Here is the plan:
```json
{
  "visual_plan": "A double pendulum swinging",
  "scenes": ["Scene 1", "Scene 2"]
}
```
"""
        cinema_resp = """
Camera plan:
```json
{
  "camera_actions": ["Zoom In", "Pan Right"],
  "pacing": {"speed": "fast"}
}
```
"""
        mock_instance.batch_invoke.return_value = [architect_resp, cinema_resp]
        
        # Input State
        state = {
            "user_prompt": "Double Pendulum",
            "concept_graph": {"concept_sequence": ["Chaos", "Energy"]}
        }
        
        # Execute Node
        result = architect_batch_node(state)
        
        # Verify
        print("\nResult Keys:", result.keys())
        
        self.assertIn("plan", result)
        self.assertIn("camera_instructions", result)
        self.assertIn("pacing", result)
        
        self.assertEqual(result["plan"]["visual_plan"], "A double pendulum swinging")
        self.assertEqual(result["camera_instructions"][0], "Zoom In")

if __name__ == '__main__':
    unittest.main()
