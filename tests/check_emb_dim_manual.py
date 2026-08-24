import os
import sys
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check_dim():
    print("--- Checking gemini-embedding-001 with manual Matryoshka truncation (768) ---")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector = embeddings.embed_query("What is the Create animation?")
        
        # Truncate to first 768 dimensions
        truncated = vector[:768]
        
        # Re-normalize (optional but recommended for cosine metric)
        norm = np.linalg.norm(truncated)
        if norm > 0:
            truncated = [v / norm for v in truncated]
        
        print(f"   Original Dimension: {len(vector)}")
        print(f"   Truncated Dimension: {len(truncated)}")
        print(f"   Re-normalized Norm: {np.linalg.norm(truncated)}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    check_dim()
