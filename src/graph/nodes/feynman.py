from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
from src.utils.llm_helpers import extract_text_content
import json

FEYNMAN_SYSTEM_PROMPT = """You are **Richard Feynman**, the Great Explainer.

Your goal is to take complex physics equations and concepts and translate them into **Intuitive Analogies**.
You are NOT teaching the math yet. You are building the intuition *before* the math.

<rules>
1. **Analogy First**: Always start with a real-world comparison (e.g., "Voltage is like water pressure").
2. **Visual Metaphor**: Suggest a simple visual that could represent this analogy (e.g., "A water tank with a pipe").
3. **Simplicity**: Use simple language. Avoid jargon.
4. **Tone**: Enthusiastic, curious, and clear.
</rules>

<output_format>
Return a JSON object with:
{
  "analogy_text": "Imagine a skateboarder in a half-pipe...",
  "visual_metaphor": "A U-shaped curve with a marble rolling back and forth.",
  "core_concept": "Conservation of Energy"
}
</output_format>
"""

async def feynman_node(state: AgentState):
    """
    Node: Feynman (The Explainer)
    Generate intuition and analogies.
    """
    print("--- NODE: Feynman (Analogy) ---")
    
    user_prompt = state.get("user_prompt")
    physics_data = state.get("physics_code", {})
    concept_graph = state.get("concept_graph", {})
    
    llm = get_llm(model_type="pro")
    
    # Extract key concepts to explain
    equations = physics_data.get("equations", [])
    explanation = physics_data.get("explanation", "")
    
    input_text = f"""
    USER PROMPT: {user_prompt}
    
    PHYSICS EXPLANATION:
    {explanation}
    
    EQUATIONS:
    {json.dumps(equations, indent=2)}
    
    CONCEPTS:
    {json.dumps(concept_graph, indent=2)}
    """
    
    messages = [
        SystemMessage(content=FEYNMAN_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = extract_text_content(response)
        
        # Robust JSON cleaning
        clean_json = content
        if "{" in clean_json:
            clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
        
        try:
            analogy_data = json.loads(clean_json)
            print("   💡 Analogy Generated.")
        except:
             print("   ⚠️ Feynman output unstructured. Using raw text.")
             analogy_data = {"analogy_text": content, "visual_metaphor": "Abstract representation"}
             
        return {"analogy": analogy_data}
        
    except Exception as e:
        print(f"   ❌ Feynman Error: {e}")
        return {"analogy": {}}
