import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()

def check_models():
    # Try bare names and prefixes
    models_to_try = [
        "text-embedding-004",
        "models/text-embedding-004",
        "embedding-001",
        "models/embedding-001"
    ]
    
    for m in models_to_try:
        print(f"--- Trying {m} ---")
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model=m, task_type="retrieval_query")
            vector = embeddings.embed_query("Test query")
            print(f"   SUCCESS! Dimension: {len(vector)}")
        except Exception as e:
            print(f"   FAILED: {e}")

if __name__ == "__main__":
    check_models()
