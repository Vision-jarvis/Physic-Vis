import os
import inspect
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

def inspect_embeddings():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    print(f"Embeddings Class Members: {dir(embeddings)}")
    # Check if 'task_type' or 'output_dimensionality' are in the init
    print(f"Init Signature: {inspect.signature(embeddings.__init__)}")

if __name__ == "__main__":
    inspect_embeddings()
