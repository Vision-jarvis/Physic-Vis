from src.graph.state import AgentState
from src.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json

SCRIPT_SYSTEM_PROMPT = """You are a master science communicator (like Grant Sanderson or Feynman).
Your goal is to write a narration script for a physics video.

CONTEXT:
You will be given:
1. The User's Prompt (Topic)
2. The Act Context (e.g., "Intuition")
3. The Visual Plan (what is shown on screen)

INSTRUCTIONS:
- Write a script that synchronizes with the visuals.
- Keep it engaging, conversational, yet precise.
- Break it into segments. 
- Output STRICT JSON.

JSON FORMAT:
{
  "segments": [
    {
      "text": "Imagine a ball spinning...",
      "visual_cue": "Show ball",
      "estimated_duration": 3.0
    },
    ...
  ],
  "total_estimated_duration": 45.0
}
"""

async def script_writer_node(state: AgentState):
    """
    Generates the voiceover script.
    """
    print("--- NODE: Script Writer ---")
    
    prompt = state.get("user_prompt")
    plan = state.get("plan", {})
    concept_graph = state.get("concept_graph", {})
    
    # We might not have 'act_context' directly in state unless passed specifically.
    # But often the prompt contains "CONTEXT: Act 1..."
    
    llm = get_llm(temperature=0.7)
    
    messages = [
        SystemMessage(content=SCRIPT_SYSTEM_PROMPT),
        HumanMessage(content=f"""
        TOPIC: {prompt}
        VISUAL PLAN: {json.dumps(plan, indent=2)}
        CONCEPTS: {json.dumps(concept_graph.get('concepts', []), indent=2)}
        """)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        script = json.loads(content)
        print("   ✅ Script Generated.")
        
        return {"voiceover_script": script}
        
    except Exception as e:
        print(f"   ❌ Script Generation Failed: {e}")
        return {"voiceover_script": None}
