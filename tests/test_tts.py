import sys
import os
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.narration.tts import VoiceSynthesizer
from src.core.config import settings
from dotenv import load_dotenv
import os

load_dotenv()

def test_tts():
    print(f"🔑 Key present: {'Yes' if settings.eleven_labs_api_key else 'No'}")
    
    tts = VoiceSynthesizer(provider="elevenlabs")
    text = "Hello! This is a test of the physics engine voice system."
    path = "output/test_audio/test_speech.mp3"
    
    try:
        tts.synthesize(text, path)
        print(f"✅ Success: {path}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_tts()
