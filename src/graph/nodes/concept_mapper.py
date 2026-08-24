from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
import json
import ast

from src.utils.llm_helpers import extract_text_content

CONCEPT_MAPPER_SYSTEM_PROMPT = """You are a **Pedagogical Expert** and **Curriculum Designer** (inspired by 3Blue1Brown/Khan Academy).

Your goal is to break down a physics topics into a **Concept Dependency Graph**.
Before generating an animation, you must determine what the viewer needs to know FIRST.

<output_format>
Return a JSON object with:
{
  "concepts": ["Concept A", "Concept B", "Concept C"],
  "prerequisites": {
    "Concept C": ["Concept A", "Concept B"],
    "Concept B": ["Concept A"]
  },
  "narrative_flow": "First we introduce A, then show how it leads to B, and finally combine them into C.",
  "metaphors": ["Analogy 1", "Analogy 2"]
}
</output_format>

<rules>
1. **Atomic Concepts**: Break the request down into small, teachable units.
2. **Logical Flow**: Ensure prerequisites are valid. You can't explain 'Torque' without 'Force' and 'Lever Arm'.
3. **Cognitive Load**: If there are more than 3 new concepts, suggest splitting the video (but for now just list them).
</rules>
"""

async def concept_mapper_node(state: AgentState):
    """
    Node 0: Concept Mapper
    Determines pedagogical structure before visual planning.
    """
    print("--- NODE: Concept Mapper (Pedagogy) ---")
    user_prompt = state.get("user_prompt")
    
    llm = get_llm(model_type="pro") # Gemini 3.0 Pro for reasoning
    
    input_text = f"USER REQUEST: {user_prompt}"
    
    messages = [
        SystemMessage(content=CONCEPT_MAPPER_SYSTEM_PROMPT + "\n\nIMPORTANT: Return ONLY the raw JSON string. No markdown, no backticks, no explanations."),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = extract_text_content(response)
        
        print(f"DEBUG RAW CONTENT: {repr(content)}")
        
        # Robust cleaning: Find first { and last }
        clean_json = content
        if "{" in clean_json:
            start = clean_json.find("{")
            end = clean_json.rfind("}")
            if end != -1:
                clean_json = clean_json[start:end+1]
        
        clean_json = clean_json.strip()
        print(f"DEBUG CLEAN JSON: {repr(clean_json)}")
        
        try:
            graph_data = json.loads(clean_json)
        except json.JSONDecodeError:
            # Fallback for Python dictionary format (single quotes)
            try:
                graph_data = ast.literal_eval(clean_json)
            except:
                raise ValueError("Could not parse JSON or Dict output")
        
        print(f"   🧠 Concepts identified: {graph_data.get('concepts', [])}")
        print(f"   👉 Flow: {graph_data.get('narrative_flow', 'Linear')}")
        
        return {
            "concept_graph": graph_data
        }
        
    except Exception as e:
        print(f"   ⚠️ Concept Mapper Failed: {e}. Proceeding with raw prompt.")
        return {
             "concept_graph": {"error": str(e)}
        }
