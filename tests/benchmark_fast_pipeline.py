import time
import os
import sys

# Ensure src is directly importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.optimization.pipeline import FastMultiActPipeline

def benchmark_pipeline():
    """Compare different pipeline speeds."""
    test_prompt = "Explain the concept of Inertia with visual examples"
    
    pipeline = FastMultiActPipeline()
    
    print(f"\\n{'='*60}")
    print(f"TESTING: Fast Multi-Act Pipeline (Hierarchical + Parallel)")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        video = pipeline.generate(test_prompt)
        elapsed = time.time() - start
        print(f"\\n✅ SUCCESS: Video generated in {elapsed:.1f}s")
        print(f"Video path: {video}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"\\n❌ FAILED: Error after {elapsed:.1f}s")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    benchmark_pipeline()
