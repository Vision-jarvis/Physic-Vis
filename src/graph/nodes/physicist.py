from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List, Dict
from src.core.llm import get_embeddings
from src.graph.state import AgentState
from src.core.cache import cached_llm_call, cached_rag_retrieval
import json
import os
from pinecone import Pinecone

# --- PROMPTS ---
PHYSICIST_SYSTEM_PROMPT = """You are Dr. Richard Feynman, a world-class Physics Educator.
Your goal is to identify the core physics principles behind a requested animation and provide the EXACT LaTeX equations needed to display them.

<constraints>
1. **Accuracy**: Equations must be dimensionally correct.
2. **LaTeX**: formatting must be perfect for Manim's MathTex class. Use double backslashes for escape sequences if needed (e.g. \\frac).
3. **Simplicity**: Do not overwhelm the screen. limits to 3 key equations.
4. **Educational Value**: The explanation should be insightful, not just descriptive.
5. **RAG Compliance**: If "MATCHED FORMULAS" are provided in the input, YOU MUST USE THEM EXACTLY. Do not modify standard variables.
</constraints>

Example Output:
{
  "principle": "Simple Harmonic Motion",
  "equations": ["T = 2\\pi \\sqrt{\\frac{L}{g}}"],
  "explanation": " The period of a pendulum depends only on its length and gravity, not its mass.",
  "variables": {"T": "Period (s)", "L": "Length (m)", "g": "Gravity (9.8 m/s^2)"},
  "placement": "top_right"
}
"""

def retrieve_physics_context(query: str) -> str:
    """
    Helper function for RAG that wraps Pinecone logic.
    """
    try:
        print(f"   🔍 Querying Pinecone: '{query}'")
        embeddings = get_embeddings()
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("physics-knowledge")
        
        vector = embeddings.embed_query(query)
        results = index.query(vector=vector, top_k=1, include_metadata=True)
        
        if results['matches'] and results['matches'][0]['score'] > 0.7:
             meta = results['matches'][0]['metadata']
             print(f"   ✅ RAG Hit: {meta['concept']} (Score: {results['matches'][0]['score']:.2f})")
             return f"""
             <MATCHED_FORMULAS>
             Concept: {meta['concept']}
             Equations (Verified): {meta.get('latex_equations', '[]')}
             Variables: {meta.get('variables', '{}')}
             Explanation: {meta.get('explanation', '')}
             Visual Cues: {meta.get('manim_visual_cues', '')}
             
             INSTRUCTION: Use these PRECISE equations. Do not hallucinate derivations.
             </MATCHED_FORMULAS>
             """
        else:
            return "" # No hit
            
    except Exception as e:
        print(f"   ❌ RAG Retrieval Failed: {e}")
        return ""

from src.utils.llm_helpers import extract_text_content, strip_code_fences

async def physicist_node(state: AgentState):
    """
    Node B: The Physicist (Optimized with Caching)
    """
    print("--- NODE: Physicist (Cached) ---")
    user_prompt = state["user_prompt"]
    plan = state.get("plan", "No specific plan provided.")
    
    # 1. Cached RAG
    rag_context = cached_rag_retrieval(
        query=user_prompt,
        index_name="physics-knowledge",
        retriever_func=retrieve_physics_context
    )
    
    if rag_context:
        print("   ✅ Using Cached/Retrieved Physics Context.")
    else:
        print("   ⚠️ No Physics Context found (Gemini Reasoning Only).")

    # 2. Cached LLM
    input_text = f"""
    User Request: {user_prompt}
    Architect's Plan: {plan}
    
    {rag_context}
    
    Identify the physics and equations. Return Valid JSON.
    """
    
    response_str = await cached_llm_call(
        prompt=input_text,
        system_prompt=PHYSICIST_SYSTEM_PROMPT,
        temperature=0.4, # Slightly different to ensure new cache key
        model_type="flash" # Use fast/stable model
    )
    
    # Parse JSON
    try:
        # Use robust extraction
        content = strip_code_fences(extract_text_content(response_str))
        physics_data = json.loads(content)
        print("   ⚛️  Physics Data Generated.")
        return {"physics_code": physics_data}
    except Exception as e:
        print(f"   ❌ Physicist Parse Error (JSON): {e}")
        
        # Fallback: Try repairing the JSON
        from src.graph.utils.response_handler import repair_json
        
        # In case the content was a list, or normal JSON strings.
        # physicist is returning code, not structured json in the base case so we just use strip_code_fences.
        try:
            from src.utils.llm_helpers import extract_text_content
            text_content = extract_text_content(response_str) # Use response_str
        except Exception:
            text_content = response_str # Fallback if extract_text_content fails or is not needed

        # Corrected line: apply strip_code_fences then repair_json
        clean_json = repair_json(strip_code_fences(text_content))
        try:
             physics_data = json.loads(clean_json)
             print("   ⚠️ Parsed after repair_json().")
             return {"physics_code": physics_data}
        except Exception as e2:
             print(f"   ❌ Physicist Parse Error (Repair Failed): {e2}")
             # Last resort: text explanation
             return {
                "physics_code": {
                    "principle": "Analysis Error", 
                    "equations": [], 
                    "explanation": f"Could not parse physics data: {user_prompt}"
                }
            }
