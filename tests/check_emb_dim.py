import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.llm import get_embeddings

def check_dim():
    print("--- Checking text-embedding-004 ---")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vector = embeddings.embed_query("What is the Create animation?")
        print(f"   Model used: {embeddings.model}")
        print(f"   Vector Dimension: {len(vector)}")
    except Exception as e:
        print(f"   Error text-embedding-004: {e}")

    print("\n--- Checking gemini-embedding-001 ---")
    try:
        embeddings2 = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector2 = embeddings2.embed_query("What is the Create animation?")
        print(f"   Model used: {embeddings2.model}")
        print(f"   Vector Dimension: {len(vector2)}")
    except Exception as e:
        print(f"   Error gemini-embedding-001: {e}")

if __name__ == "__main__":
    check_dim()
