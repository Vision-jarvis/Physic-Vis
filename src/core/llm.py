import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

def get_llm(model_type: str = "flash", temperature: float = None):
    """
    Factory function to get the appropriate Gemini model.
    
    Args:
        model_type: "flash" for fast (Architect/Validator) or "pro" for reasoning (Coder/Physicist)
        temperature: Override default temperature if provided.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    model_name = "gemini-3.1-pro-preview" if model_type == "flash" else "gemini-3.1-pro-preview"
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=SecretStr(api_key),
        temperature=temperature if temperature is not None else (0.2 if model_type == "pro" else 0.7),
        convert_system_message_to_human=True, # LangChain quirk for Google
        max_retries=3,
        request_timeout=300,
    )

def get_embeddings():
    """
    Factory function to get Google GenAI Embeddings.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Use the name without prefix as it's sometimes preferred by the SDK
    # Use gemini-embedding-001 with manual Matryoshka truncation to 768D
    # to match the existing Pinecone indices.
    model_name = "models/gemini-embedding-001"
    print(f"   [DEBUG] get_embeddings() using model: {model_name} (768 truncated)")
    
    base_embeddings = GoogleGenerativeAIEmbeddings(
        model=model_name, 
        google_api_key=api_key
    )
    
    # Custom wrapper for truncation
    class TruncatedEmbeddings:
        def __init__(self, base):
            self.base = base
            self.model = base.model
            
        def embed_query(self, text: str):
            vector = self.base.embed_query(text)
            # Truncate to 768 and re-normalize
            truncated = vector[:768]
            import numpy as np
            norm = np.linalg.norm(truncated)
            if norm > 0:
                truncated = [v / norm for v in truncated]
            return truncated
            
        def embed_documents(self, texts: list[str]):
            vectors = self.base.embed_documents(texts)
            import numpy as np
            results = []
            for v in vectors:
                t = v[:768]
                n = np.linalg.norm(t)
                if n > 0:
                    t = [x / n for x in t]
                results.append(t)
            return results

    return TruncatedEmbeddings(base_embeddings)
