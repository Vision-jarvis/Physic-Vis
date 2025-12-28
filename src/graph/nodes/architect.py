from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
import json

# --- PASS 1: THE DIRECTOR ---
DIRECTOR_SYSTEM_PROMPT = """You are the **Creative Director** for a high-end educational science channel (like Kurtzgesagt or 3Blue1Brown). 
Your goal is to design the **Cinematic Vision** for a physics animation. Do not worry about code yet.

<output_format>
Return a JSON object with:
{
  "mood": "e.g. Ethereal, High-Energy, Dark & Neon",
  "camera_motion": "e.g. Slow continuous panning, Static wide shot, Dramatic zoom",
  "color_palette": ["#Hex1", "#Hex2", "#Hex3"],
  "narrative_pacing": "e.g. Start slow, accelerate at impact, freeze frame at end",
  "visual_style": "e.g. Glowing edges, Minimalist lines, Realistic textures"
}
</output_format>
"""

# --- PASS 2: THE ARCHITECT ---
ARCHITECT_SYSTEM_PROMPT = """You are the **Lead Visual Architect**. 
Your job is to translate the **Director's Vision** and **User's Request** into a precise **Manim Implementation Plan**.

<inputs>
1. **Director's Vision**: The aesthetic guide (mood, colors, camera).
2. **User Prompt**: The core subject matter.
3. **Physics Context**: Equations or concepts identified by the Physicist.
</inputs>

<instructions>
Create a detailed STEP-BY-STEP visual plan.
- **Camera**: 
    - For 2D Scenes: Use `self.camera.frame.animate.set(width=...)` or `.move_to(...)` if needed.
    - For 3D Scenes (Primary): Use `self.set_camera_orientation(phi=..., theta=...)`. 
    - **CRITICAL**: Do NOT mix 2D "frame zoom" logic with 3D orientation. If 3D, stick to `set_camera_orientation` and `move_camera`.
- **Objects**: List every Shape, Line, or Graph needed. Specify colors from the palette.
- **Animations**: Describe the `Create`, `Transform`, or `Update` calls. 
- **Pacing**: Use `run_time` values based on the Director's pacing.
</instructions>

Output as a numbered list (Markdown).
"""

async def architect_node(state: AgentState):
    """
    Node A: The Architect (Dual-Pass Director's Cut)
    Pass 1: Director (Creative Vision)
    Pass 2: Architect (Technical Spec)
    """
    print("--- NODE: Architect (Director's Cut) ---")
    user_prompt = state.get("user_prompt")
    physics_data = state.get("physics_code", {})
    
    # --- PASS 1: THE DIRECTOR ---
    llm_director = get_llm(model_type="pro") # High creativity
    
    director_input = f"""
    USER REQUEST: {user_prompt}
    PHYSICS CONTEXT: {physics_data.get('explanation', 'None')}
    """
    
    print("   🎬 Director is dreaming...")
    director_response = await llm_director.ainvoke([
        SystemMessage(content=DIRECTOR_SYSTEM_PROMPT),
        HumanMessage(content=director_input)
    ])
    
    # Try to parse JSON, fallback to raw text if needed
    try:
        director_vision = director_response.content.replace("```json", "").replace("```", "").strip()
        vision_json = json.loads(director_vision)
        print(f"   ✨ Vision: {vision_json.get('mood', 'Undefined')}")
    except:
        print("   ⚠️ Director output unstructured, using raw text.")
        director_vision = director_response.content

    # --- PASS 2: THE ARCHITECT ---
    llm_architect = get_llm(model_type="pro") # High reasoning
    
    architect_input = f"""
    USER REQUEST: {user_prompt}
    
    DIRECTOR'S VISION:
    {director_vision}
    
    PHYSICS DATA:
    {json.dumps(physics_data, indent=2)}
    """
    
    print("   📐 Architect is drafting...")
    architect_response = await llm_architect.ainvoke([
        SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
        HumanMessage(content=architect_input)
    ])
    
    final_plan = architect_response.content
    
    return {"plan": final_plan}
