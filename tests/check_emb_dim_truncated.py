import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check_dim():
    print("--- Checking gemini-embedding-001 with 768 truncation ---")
    try:
        # Some versions of langchain-google-genai allow passing model_kwargs or direct params
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            # We hope this is passed through to the underlying API call
            output_dimensionality=768
        )
        vector = embeddings.embed_query("What is the Create animation?")
        print(f"   Model used: {embeddings.model}")
        print(f"   Vector Dimension: {len(vector)}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    check_dim()
