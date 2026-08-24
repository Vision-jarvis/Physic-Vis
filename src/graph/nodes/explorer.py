from src.graph.state import AgentState
from src.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json

EXPLORER_SYSTEM_PROMPT = """You are a Physics Lab Designer.
Your goal is to identify "Explorable Parameters" in a given physics system.
An explorable parameter is a variable that, when changed, produces a visually distinct and educational effect.

INPUT:
1. Physics Equations (LaTeX)
2. Variable Definitions

OUTPUT:
Strict JSON:
{
  "parameters": [
    {
      "symbol": "k",
      "name": "Spring Constant",
      "range": [1, 10],
      "interesting_values": [1, 5, 10],
      "visual_effect": "Higher k means faster oscillation and stiffer spring."
    }
  ],
  "recommendation": "Show side-by-side comparison of k=1 vs k=10."
}
"""

async def explorer_node(state: AgentState):
    """
    Node X: The Explorer
    Identifies parameters to sweep/vary.
    """
    print("--- NODE: Parameter Explorer ---")
    physics = state.get("physics_code", {})
    
    if not physics or not physics.get("equations"):
        print("   ⚠️ No physics data to explore.")
        return {"parameter_sweep": None}
        
    llm = get_llm(temperature=0.5)
    
    input_text = f"""
    EQUATIONS: {physics.get('equations')}
    VARIABLES: {physics.get('variables', {})}
    EXPLANATION: {physics.get('explanation', '')}
    
    Identify 1-2 key parameters to explore.
    """
    
    messages = [
        SystemMessage(content=EXPLORER_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        sweep_plan = json.loads(content)
        print(f"   🧪 Exploration Plan: {len(sweep_plan.get('parameters', []))} parameters identified.")
        return {"parameter_sweep": sweep_plan}
        
    except Exception as e:
        print(f"   ❌ Explorer Failed: {e}")
        return {"parameter_sweep": None}
