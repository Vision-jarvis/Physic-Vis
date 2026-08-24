import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Centralized configuration management.
    """
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.eleven_labs_api_key = os.getenv("ELEVEN_LABS_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        
        # Models
        # Using 2.0 Flash as the fast orchestrator by default for batch ops, unless overridden
        self.model_orchestrator = "gemini-3.1-pro-preview" 
        self.model_reasoning = "gemini-3.1-pro-preview" 
        
        # Output
        self.output_dir = "output"
        
# Global instance
settings = Settings()

if not settings.gemini_api_key:
    print("Warning: GEMINI_API_KEY not set.")
