import unittest
import os
import sys
import shutil
import json
import tempfile

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cache import CacheManager

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache
        self.test_dir = tempfile.mkdtemp()
        self.cache = CacheManager(cache_dir=self.test_dir)
        
    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
        
    def test_llm_cache_lifecycle(self):
        """Test saving and retrieving LLM responses."""
        prompt = "Explain quantum physics"
        system = "You are Feynman"
        temp = 0.7
        response = "It's like a mosh pit."
        
        # 1. Should be empty initially
        cached = self.cache.get_llm_response(prompt, system, temp)
        self.assertIsNone(cached, "Cache should be empty")
        
        # 2. Save
        self.cache.save_llm_response(prompt, system, temp, response)
        
        # 3. Retrieve (Memory Hit)
        cached_mem = self.cache.get_llm_response(prompt, system, temp)
        self.assertEqual(cached_mem, response, "Should retrieve from memory")
        
        # 4. Clear Memory and Retrieve (Disk Hit)
        self.cache.clear()
        cached_disk = self.cache.get_llm_response(prompt, system, temp)
        self.assertEqual(cached_disk, response, "Should retrieve from disk")
        
        # 5. Verify Disk File Exists
        # Manually check if file was created
        files = os.listdir(self.cache.llm_cache_dir)
        self.assertEqual(len(files), 1, "Should have one cache file")
        
    def test_rag_cache_lifecycle(self):
        """Test saving and retrieving RAG context."""
        query = "Navier Stokes"
        index = "physics"
        context = "Equation 1... Equation 2..."
        
        # 1. Save
        self.cache.save_rag_context(query, index, context)
        
        # 2. Retrieve
        self.cache.clear() # Force disk read
        retrieved = self.cache.get_rag_context(query, index)
        self.assertEqual(retrieved, context)

    def test_cache_key_robustness(self):
        """Test that key generation is stable."""
        key1 = self.cache._generate_key({"a": 1, "b": 2})
        key2 = self.cache._generate_key({"b": 2, "a": 1}) # Different order
        self.assertEqual(key1, key2, "Dictionary order shouldn't matter")

if __name__ == '__main__':
    unittest.main()
