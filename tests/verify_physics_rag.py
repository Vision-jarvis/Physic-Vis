import os
import sys
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.llm import get_embeddings

load_dotenv()

INDEX_NAME = "physics-knowledge"

def verify_rag():
    print("🔍 Verifying Physics RAG...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(INDEX_NAME)
    
    embeddings = get_embeddings()
    
    test_queries = [
        "Bernoulli's Principle",
        "Maxwell's Equations",
        "Time Dilation",
        "Schrödinger Equation"
    ]
    
    for query in test_queries:
        print(f"\n❓ Querying: '{query}'")
        vector = embeddings.embed_query(query)
        
        results = index.query(
            vector=vector,
            top_k=1,
            include_metadata=True
        )
        
        if results['matches']:
            match = results['matches'][0]
            print(f"   ✅ Found: {match['metadata']['topic']} - {match['metadata']['concept']}")
            print(f"   📝 Excerpt: {match['metadata']['explanation'][:100]}...")
        else:
            print("   ❌ No match found.")

if __name__ == "__main__":
    verify_rag()
