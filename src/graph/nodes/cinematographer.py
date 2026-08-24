from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
from src.utils.llm_helpers import extract_text_content
import json

CINEMATOGRAPHER_SYSTEM_PROMPT = """You are the **Director of Photography** and **Editor** for a Manim physics animation.

Your goal is to take a generic visual plan and turn it into a **Cinematic Experience**.
You control TWO things:
1. **Camera**: Where the viewer looks (Zoom, Pan, Rotate).
2. **Time**: How long animations play (Pacing).

<camera_rules>
1. **Focus on Math**: When a complex equation appears, ZOOM IN (e.g., scale frame by 0.6 around the equation).
2. **Context**: When showing a big diagram, ZOOM OUT or PAN to fit everything.
3. **Dynamic Motion**: Don't just sit still. Use slow pans for static scenes.
4. **Resets**: After focusing on a detail, `Restore()` the camera to show the big picture.
</camera_rules>

<timing_rules>
1. **Reading Speed**: Assume the viewer reads at 150 words per minute.
2. **Equation Digestion**: Add 2-3 extra seconds for complex formulas.
3. **Transition**: Standard transition time is 1.0s.
</timing_rules>

<output_format>
Return a JSON object with:
{
  "camera_actions": [
    {"t": "start", "action": "set_frame", "width": 14},
    {"t": "equation_reveal", "action": "zoom_to_mobject", "target": "eq_group", "scale": 1.2}
  ],
  "pacing": {
    "intro_duration": 4.0,
    "main_animation_duration": 8.0,
    "conclusion_duration": 3.0
  },
  "visual_style_notes": "Use a smooth ease_in_out interpolation for all camera moves."
}
</output_format>
"""

async def cinematographer_node(state: AgentState):
    """
    Node: Cinematographer
    Adds camera directives and timing logic to the plan.
    """
    print("--- NODE: Cinematographer (Camera & Timing) ---")
    
    user_prompt = state.get("user_prompt")
    plan = state.get("plan", "")
    physics_data = state.get("physics_code", {})
    
    llm = get_llm(model_type="pro")
    
    input_text = f"""
    USER PROMPT: {user_prompt}
    
    VISUAL PLAN (Architect):
    {plan}
    
    PHYSICS CONTENT (Physicist):
    {json.dumps(physics_data, indent=2)}
    """
    
    messages = [
        SystemMessage(content=CINEMATOGRAPHER_SYSTEM_PROMPT),
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
            camera_instructions = json.loads(clean_json)
            print("   🎥 Camera Instructions Generated.")
        except:
             print("   ⚠️ Cinematographer output unstructured. Formatting as text-based instructions.")
             camera_instructions = {"raw_instructions": content}
             
        return {"camera_instructions": camera_instructions}
        
    except Exception as e:
        print(f"   ❌ Cinematographer Error: {e}")
        # Fallback to empty instructions (safe default)
        return {"camera_instructions": {}}
