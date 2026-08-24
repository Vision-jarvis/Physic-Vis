import asyncio
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

async def test_emb():
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Testing with API Key: {api_key[:10]}...")
    
    try:
        # Test 1: models/ prefix + task_type
        print("\nTest 1: models/text-embedding-004 + task_type='retrieval_query'")
        emb1 = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", task_type="retrieval_query", google_api_key=api_key)
        res1 = await emb1.aembed_query("Hello world")
        print(f"✅ Test 1 Success. Dim: {len(res1)}")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")

    try:
        # Test 2: no models/ prefix
        print("\nTest 2: text-embedding-004 + task_type='retrieval_query'")
        emb2 = GoogleGenerativeAIEmbeddings(model="text-embedding-004", task_type="retrieval_query", google_api_key=api_key)
        res2 = await emb2.aembed_query("Hello world")
        print(f"✅ Test 2 Success. Dim: {len(res2)}")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")

    try:
        # Test 3: no task_type
        print("\nTest 3: models/text-embedding-004 (no task_type)")
        emb3 = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
        res3 = await emb3.aembed_query("Hello world")
        print(f"✅ Test 3 Success. Dim: {len(res3)}")
    except Exception as e:
        print(f"❌ Test 3 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_emb())
