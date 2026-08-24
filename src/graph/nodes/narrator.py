from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
from src.utils.llm_helpers import extract_text_content
import json

NARRATOR_SYSTEM_PROMPT = """You are the **Narrator** for a premium educational video (think 3Blue1Brown).

Your goal is to write a script that perfectly matches the Visual Plan and Camera Timing.
You have the "Analogy" from Feynman to make it intuitive.

<input_data>
1. **Analogy**: The core intuitive concept.
2. **Visual Pacing**: How long each section lasts.
3. **Draft Plan**: The scientific explanation.
</input_data>

<rules>
1. **Timing**: You have roughly 150 words per minute. If a section is 4 seconds, you have ~10 words. KEEP IT SHORT.
2. **Style**: Conversational, insightful, calm.
3. **Format**: Return the script blocks matching the pacing keys.
</rules>

<output_format>
Return a JSON object:
{
  "script_blocks": {
     "intro_duration": "Welcome. Today we explore the hidden rhythm of the universe.",
     "equation_reveal_hold": "Notice how the force grows stronger as we stretch it further.",
     "conclusion_duration": "This is the essence of Simple Harmonic Motion."
  },
  "full_script": "Welcome... (joined text)"
}
</output_format>
"""

async def narrator_node(state: AgentState):
    """
    Node: Narrator (The Voice)
    generates the final script based on timing constraints.
    """
    print("--- NODE: Narrator (Scripting) ---")
    
    analogy = state.get("analogy", {})
    camera_instr = state.get("camera_instructions", {})
    pacing = camera_instr.get("pacing", {})
    plan = state.get("plan", "")
    
    llm = get_llm(model_type="pro")
    
    input_text = f"""
    ANALOGY (Feynman):
    {analogy.get("analogy_text", "No analogy provided.")}
    
    TIMING CONSTRAINTS (Seconds):
    {json.dumps(pacing, indent=2)}
    
    VISUAL PLAN:
    {plan}
    """
    
    messages = [
        SystemMessage(content=NARRATOR_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = extract_text_content(response)
        
        # Clean JSON
        clean_json = content
        if "{" in clean_json:
            clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
            
        try:
            script_data = json.loads(clean_json)
            print("   🎙️ Script Generated.")
        except:
            print("   ⚠️ Narrator output unstructured. Using raw text.")
            script_data = {"full_script": content}
            
        return {"voiceover_script": script_data.get("full_script", "")}
        
    except Exception as e:
        print(f"   ❌ Narrator Error: {e}")
        return {"voiceover_script": ""}
