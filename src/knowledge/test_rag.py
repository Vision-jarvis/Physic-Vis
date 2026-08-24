import os
import sys
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.core.llm import get_embeddings
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INDEX_NAME = "manim-docs-v2"

def test_query(query, filter_dict=None):
    print(f"\n🔎 Query: '{query}'")
    if filter_dict:
        print(f"   Filter: {filter_dict}")
        
    embeddings = get_embeddings()
    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME, 
        embedding=embeddings,
        pinecone_api_key=PINECONE_API_KEY
    )
    
    # Search
    if filter_dict:
        results = vectorstore.similarity_search(query, k=3, filter=filter_dict)
    else:
        results = vectorstore.similarity_search(query, k=3)
        
    print(f"   Found {len(results)} results:")
    for i, res in enumerate(results):
        meta = res.metadata
        print(f"   [{i+1}] {meta.get('class_name', 'Unknown')} ({meta.get('type')})")
        print(f"       Source: {meta.get('source')}")
        snippet = res.page_content.replace('\n', ' ')[:100]
        print(f"       Snippet: {snippet}...")

def main():
    print("🧪 Testing Manim RAG...")
    
    # 1. Test Definition Retrieval
    test_query("What is the Create animation?", {"type": "definition", "class_name": "Create"})
    
    # 2. Test Example Retrieval
    test_query("Show me an example of Create", {"type": "example", "class_name": "Create"})
    
    # 3. Test General Search (No filter)
    test_query("How to animate text?")

if __name__ == "__main__":
    main()
