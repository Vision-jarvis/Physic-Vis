import json
import os
import sys
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Add project root to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.llm import get_embeddings

load_dotenv()

INDEX_NAME = "physics-knowledge"

def load_data():
    path = os.path.join(os.path.dirname(__file__), "data", "comprehensive_physics.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ingest():
    print("⚛️  Ingesting Physics Knowledge...")
    
    # 1. Load Data
    data = load_data()
    print(f"📄 Loaded {len(data)} concepts from JSON.")

    # 2. Setup Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: PINECONE_API_KEY NOT FOUND in .env")
        return

    pc = Pinecone(api_key=api_key)
    
    # Check/Create Index
    existing_indexes = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        print(f"📦 Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME, 
            dimension=768, # Dimension for models/embedding-001
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(10) # Wait for initialization
    else:
        print(f"✅ Index '{INDEX_NAME}' exists.")

    index = pc.Index(INDEX_NAME)

    # 3. Embedding & Upsert
    embeddings = get_embeddings()
    vectors = []
    
    print("🧠 Generating Embeddings...")
    for item in data:
        # Semantic Search Target: Topic - Concept: Explanation
        text_to_embed = f"{item['topic']} - {item['concept']}: {item['explanation']}"
        vector = embeddings.embed_query(text_to_embed)
        
        # Store essential data in metadata
        metadata = {
            "topic": item['topic'],
            "concept": item['concept'],
            "latex_equations": json.dumps(item['latex_equations']), # Store as string
            "variables": json.dumps(item['variables']), # Store as string
            "explanation": item['explanation'],
            "manim_visual_cues": item['manim_visual_cues']
        }
        
        vectors.append({
            "id": item['id'],
            "values": vector,
            "metadata": metadata
        })
    
    # Batch Upsert (Pinecone limitation: 100 vectors usually fine for one batch here)
    index.upsert(vectors=vectors)
    print(f"🚀 Successfully upserted {len(vectors)} vectors to Pinecone!")

if __name__ == "__main__":
    try:
        ingest()
    except Exception as e:
        print(f"❌ Ingestion Failed: {e}")
