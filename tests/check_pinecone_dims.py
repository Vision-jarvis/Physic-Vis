from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()

def check_indexes():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    for index_name in ["manim-docs-v2", "physics-knowledge", "error-healing"]:
        try:
            desc = pc.describe_index(index_name)
            print(f"Index: {index_name} | Dimension: {desc.dimension} | Metric: {desc.metric}")
        except Exception as e:
            print(f"Index: {index_name} | Error: {e}")

if __name__ == "__main__":
    check_indexes()
