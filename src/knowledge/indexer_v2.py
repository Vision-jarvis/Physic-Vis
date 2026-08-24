import os
import json
import time
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from src.core.llm import get_embeddings
from dotenv import load_dotenv

load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INDEX_NAME = "manim-docs-v2"  # New index for clean start

def setup_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = pc.list_indexes().names()
    
    if INDEX_NAME not in existing:
        print(f"Creating Index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768, # Gemini embedding dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(5) # Wait for ready
    else:
        print(f"Index {INDEX_NAME} exists.")
        
    return pc.Index(INDEX_NAME)

def ingest():
    print("🚀 Starting Ingestion Process...")
    
    # 1. Load Data
    json_path = "manim_knowledge_v2.json"
    if not os.path.exists(json_path):
        print("❌ Data file not found. Run scraper_v2.py first.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"📦 Loaded {len(data)} items to index.")
    
    # 2. Setup Embeddings & Vector Store
    embeddings = get_embeddings()
    
    # 3. Batch Upsert
    # PineconeVectorStore handles batching, but for huge datasets specific batching is safer.
    # Given the size (~few thousand), standard from_texts should work, but let's batch to be safe and show progress.
    
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size
    
    print(f"🧠 Vectorizing and Upserting in {total_batches} batches...")

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        texts = [item["text"] for item in batch]
        metadatas = [item["metadata"] for item in batch]
        
        # Using from_texts stores documents
        PineconeVectorStore.from_texts(
            texts=texts,
            embedding=embeddings,
            index_name=INDEX_NAME,
            metadatas=metadatas,
            pinecone_api_key=PINECONE_API_KEY
        )
        print(f"   Batch {i//batch_size + 1}/{total_batches} done.")
        
    print("🎉 Ingestion Complete.")

if __name__ == "__main__":
    setup_index()
    ingest()
