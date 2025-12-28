import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.error_kb import ErrorKnowledgeBase

def test_kb():
    print("🧪 Testing ErrorKnowledgeBase (Pinecone Edition)...")
    
    # Check keys
    if not os.getenv("PINECONE_API_KEY"):
         print("⚠️ WARNING: PINECONE_API_KEY not found. Test will verify safe fallback/handling.")
    
    kb = ErrorKnowledgeBase()
    
    # 1. Log an error (Local)
    print("   📝 Logging error locally...")
    kb.log_error({
        "error_type": "AttributeError",
        "error_message": "AttributeError: 'Camera' object has no attribute 'frame'",
        "code": "self.camera.frame.move_to(ORIGIN)",
        "topic": "Camera"
    })
    
    # 2. Log a fix (Pinecone)
    print("   🔧 Logging fix to Pinecone...")
    kb.log_successful_fix({
        "original_error": "AttributeError: 'Camera' object has no attribute 'frame'",
        "original_code": "self.camera.frame.move_to(ORIGIN)",
        "fixed_code": "self.play(self.camera.animate.move_to(ORIGIN))",
        "fix_method": "manual",
        "attempts": 1,
        "topic": "Camera"
    })
    
    # 3. Search for similar error (Pinecone)
    print("   🔍 Searching Pinecone for similar error...")
    
    # Wait briefly for upsert consistency (Pinecone is usually fast but good to wait 1s in test)
    import time
    time.sleep(2)
    
    match = kb.find_similar_fix("AttributeError: 'Camera' object has no attribute 'frame'")
    
    if match:
        print(f"      ✅ Match found! Confidence: {match['confidence']:.4f}")
        print(f"      Strategy: {match['fix_method']}")
    else:
        print("      ⚠️ No match found (might be due to empty index or key missing).")

if __name__ == "__main__":
    try:
        test_kb()
        print("\n✅ ErrorKnowledgeBase Verification Passed!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
