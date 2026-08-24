import sys
import os
import json
import ast
from typing import List, Dict

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.optimization.batch_generator import BatchCodeGenerator
from src.knowledge.retriever import retrieve_docs

# Mock Act for testing
TEST_ACT = {
    "act_number": 1,
    "type": "concept",
    "description": "Explain the concept of Vector Fields using arrows.",
    "duration": 15,
    "scenes": [
        {
            "name": "VectorFieldScene",
            "manim_objects": ["VectorField", "Arrow", "Scene"]
        }
    ],
    "narration_script": "A vector field assigns a vector to every point in space."
}

SHARED_CONTEXT = {
    "main_variables": {"func_color": "BLUE"},
    "concept_graph": {}
}

def count_hallucinations(code: str) -> List[str]:
    """Simple static analysis to find likely hallucinations."""
    hallucinations = []
    
    # Check for known hallucinated methods (from stats)
    check_list = [
        "remove_fixed_in_frame_mobjects", # Handled by polyfill now, but good to check if it appears raw usage without polyfill
        "get_time",
        "show_function", # Common hallucination for GraphScene
        "revert_to_original_size"
    ]
    
    for item in check_list:
        if f".{item}(" in code:
            hallucinations.append(item)
            
    # Check for import errors (simple string check)
    if "from manimlib" in code: # We use manim (CE), not manimlib (GL)
        hallucinations.append("manimlib_import")
        
    return hallucinations

def run_test():
    print("🧪 Starting RAG Impact Test...")
    generator = BatchCodeGenerator(max_workers=1)
    
    # 1. Generate WITH RAG
    print("\n📚 Generating WITH RAG...")
    # Manually fetch RAG for the test objects
    rag_context = {}
    for obj in TEST_ACT["scenes"][0]["manim_objects"]:
        rag_context[obj] = retrieve_docs(obj)
        
    name_rag, code_rag = generator._generate_act_code(TEST_ACT, SHARED_CONTEXT, rag_context)
    
    # 2. Generate WITHOUT RAG
    print("\n🚫 Generating WITHOUT RAG...")
    name_no_rag, code_no_rag = generator._generate_act_code(TEST_ACT, SHARED_CONTEXT, {}) # Empty context
    
    # 3. Analyze
    print("\n🔍 Analysis:")
    
    print(f"\n--- With RAG ({len(code_rag)} chars) ---")
    h_rag = count_hallucinations(code_rag)
    if h_rag:
        print(f"  ⚠️ Potential Hallucinations: {h_rag}")
    else:
        print("  ✓ No obvious hallucinations found.")
        
    print(f"\n--- Without RAG ({len(code_no_rag)} chars) ---")
    h_no_rag = count_hallucinations(code_no_rag)
    if h_no_rag:
        print(f"  ⚠️ Potential Hallucinations: {h_no_rag}")
    else:
        print("  ✓ No obvious hallucinations found.")
        
    # Check for specific RAG usage hints
    if "VectorField" in code_rag and "VectorField" in code_no_rag:
         print("\n  ℹ️  Both generated 'VectorField'. Check arguments manually if needed.")

if __name__ == "__main__":
    run_test()
