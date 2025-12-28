import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify key presence (optional, but good for debugging early)
if not os.getenv("GEMINI_API_KEY"):
    print("Warning: GEMINI_API_KEY not found in environment. Check your .env file.")
