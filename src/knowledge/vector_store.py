import os
import time
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = "manim-docs-v2"

def get_pinecone_index():
    """
    Returns the Pinecone Index object for Manim docs.
    """
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment")
        
    pc = Pinecone(api_key=api_key)
    return pc.Index(INDEX_NAME)
