import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

def get_llm(model_type: str = "flash"):
    """
    Factory function to get the appropriate Gemini model.
    
    Args:
        model_type: "flash" for fast (Architect/Validator) or "pro" for reasoning (Coder/Physicist)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    # User requested 2.5 models (2025 releases)
    model_name = "gemini-2.5-flash" if model_type == "flash" else "gemini-2.5-pro"
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=SecretStr(api_key),
        temperature=0.2 if model_type == "pro" else 0.7,
        convert_system_message_to_human=True # LangChain quirk for Google
    )

def get_embeddings():
    """
    Factory function to get Google GenAI Embeddings.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=api_key
    )
