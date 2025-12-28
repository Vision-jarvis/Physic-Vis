from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List, Dict
from src.core.llm import get_llm, get_embeddings
from src.graph.state import AgentState
import json
import os
from pinecone import Pinecone

# Define the Structured Output Schema for Gemini
class PhysicsOutput(BaseModel):
    principle: str = Field(description="The core physics principle involved (e.g. 'Conservation of Momentum')")
    equations: List[str] = Field(description="List of LaTeX equations (max 3) crucial to the scene.")
    explanation: str = Field(description="A clear, undergraduate-level explanation of the concept.")
    variables: Dict[str, str] = Field(description="Key variables and their units (e.g. {'F': 'Force (N)'})")
    placement: str = Field(description="Suggested screen placement for the text (e.g. 'top_left', 'bottom_right')")

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

async def physicist_node(state: AgentState):
    """
    Node B: The Physicist
    Uses Gemini 1.5 Pro to derive equations and explanations.
    """
    print("--- NODE: Physicist ---")
    user_prompt = state["user_prompt"]
    plan = state.get("plan", "No specific plan provided.")
    
    # --- RAG RETRIEVAL START ---
    rag_context = ""
    try:
        print("   🔍 Querying Physics Knowledge Base...")
        embeddings = get_embeddings()
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("physics-knowledge")
        
        vector = embeddings.embed_query(user_prompt)
        results = index.query(vector=vector, top_k=1, include_metadata=True)
        
        if results['matches'] and results['matches'][0]['score'] > 0.7:
             meta = results['matches'][0]['metadata']
             print(f"   ✅ RAG Hit: {meta['concept']} (Score: {results['matches'][0]['score']:.2f})")
             rag_context = f"""
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
            print("   ⚠️ No relevant knowledge found (Score < 0.7). Relying on Gemini knowledge.")
            
    except Exception as e:
        print(f"   ❌ RAG Check Failed: {e}")
    # --- RAG RETRIEVAL END ---
    
    llm = get_llm(model_type="pro")
    
    # Force the model to output structured JSON
    structured_llm = llm.with_structured_output(PhysicsOutput)
    
    input_text = f"""
    User Request: {user_prompt}
    Architect's Plan: {plan}
    
    {rag_context}
    
    Identify the physics and equations.
    """
    
    messages = [
        SystemMessage(content=PHYSICIST_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await structured_llm.ainvoke(messages)
        return {"physics_code": response.dict()}
    except Exception as e:
        print(f"Physicist Node Error: {e}")
        # Fallback for prototype if LLM fails (though retry logic should handle this later)
        return {
            "physics_code": {
                "principle": "Error in Physics Node",
                "equations": [],
                "explanation": f"Failed to generate physics: {str(e)}",
                "variables": {},
                "placement": "top_left"
            }
        }
