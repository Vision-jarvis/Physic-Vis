import os
import sys
import unittest
from dotenv import load_dotenv
from pinecone import Pinecone

# Add src to path
sys.path.append(os.getcwd())
from src.core.llm import get_embeddings

load_dotenv()

class TestRAG(unittest.TestCase):
    def setUp(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = "physics-knowledge"
        self.embeddings = get_embeddings()

    def test_retrieval(self):
        print("\n🧪 Testing RAG Retrieval...")
        query = "Lorentz Force"
        
        # 1. Embed Query
        vector = self.embeddings.embed_query(query)
        
        # 2. Query Pinecone
        index = self.pc.Index(self.index_name)
        results = index.query(
            vector=vector,
            top_k=1,
            include_metadata=True
        )
        
        match = results['matches'][0]
        score = match['score']
        metadata = match['metadata']
        
        print(f"   Query: '{query}'")
        print(f"   Top Hit: {metadata['concept']} (Score: {score:.4f})")
        print(f"   Retrieved Equations: {metadata['latex_equations']}")
        
        # Assertions
        self.assertGreater(score, 0.7)
        self.assertIn("Lorentz Force", metadata['concept'])
        self.assertIn("\\vec{F}", metadata['latex_equations'])

if __name__ == "__main__":
    unittest.main()
