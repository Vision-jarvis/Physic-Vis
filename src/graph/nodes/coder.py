from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
from src.graph.utils.extractor import extract_manim_keywords
from src.knowledge.retriever import retrieve_docs
from src.core.style_guide import get_style_prompt
from src.utils.llm_helpers import extract_text_content, strip_code_fences
import json

MANIM_SPATIAL_RULES = """
CRITICAL COORDINATE SYSTEM RULES (Manim Community Edition v0.18+):
1. Screen Bounds (16:9): x ∈ [-7, 7], y ∈ [-4, 4].
2. Smart Positioning: Use `smart_position(mob)` (imported helper) for safety.
3. Scaling: `MathTex(...).scale(0.8)` (Do NOT pass scale as kwarg).
4. No `ShowCreation` (Use `Create`).
5. No `Base` parameter in Mobjects.
6. LaTeX Rules:
   - Use raw strings: `MathTex(r"\frac{a}{b}")`.
   - Avoid `\text{}` inside MathTex if possible, use `Tex` for text.
   - NO external packages (tikzpicture, etc.). Keep it standard.
"""

async def coder_node(state: AgentState):
    """
    Node C: The Coder (RAG-Enhanced)
    Uses Gemini 2.5 Pro + Manim Docs RAG to write the script.
    """
    print("--- NODE: Coder (RAG-Enhanced) ---")
    user_prompt = state.get("user_prompt")
    plan = state.get("plan", user_prompt)
    physics_data = state.get("physics_code", {})
    camera_instr = state.get("camera_instructions", {})
    
    # 1. Extract Keywords from the Architect's Plan
    keywords = extract_manim_keywords(plan)
    print(f"   🔑 Extracted Keywords: {keywords}")
    
    # 2. Retrieve Specific Docs
    rag_context = retrieve_docs(keywords[:5])
    
    # 3. Prepare Physics Context
    equations_str = ""
    if physics_data:
        eqs = physics_data.get("equations", [])
        explanation = physics_data.get("explanation", "")
        placement = physics_data.get("placement", "UP")
        equations_str = f"""
        REQUIRED EQUATIONS TO DISPLAY:
        {json.dumps(eqs, indent=2)}
        EXPLANATION TEXT: "{explanation}"
        PLACEMENT: {placement}
        """

    # 4. Prepare Camera & Timing Context
    camera_str = ""
    if camera_instr:
        actions = camera_instr.get("camera_actions", [])
        pacing = camera_instr.get("pacing", {})
        raw = camera_instr.get("raw_instructions", "")
        
        camera_str = f"""
        ### 🎥 CAMERA & TIMING INSTRUCTIONS (STRICTLY FOLLOW):
        
        PACING (run_time override):
        {json.dumps(pacing, indent=2)}
        
        CAMERA ACTIONS:
        {json.dumps(actions, indent=2)}
        
        RAW INSTRUCTIONS (Fallback):
        "{raw}"
        
        <camera_rules>
        1. IF action='zoom_to_mobject', use `self.play(self.camera.frame.animate.move_to(mob).set(width=...))` (ONLY FOR MovingCameraScene).
        2. IF action='restore', use `self.play(Restore(self.camera.frame))`.
        3. Apply `run_time` from the PACING dictionary.
        4. **CRITICAL FOR 3D SCENES**: 
           - DO NOT use `self.camera.frame.animate`. 
           - DO NOT use `self.camera.frame_center.animate`. 
           - USE `self.move_camera(phi=..., theta=..., zoom=..., frame_center=...)`.
           - **Do NOT use `begin_ambient_camera_rotation` with `about="z_axis"`. Use `about="theta"` (default) for Z-axis rotation.**
        5. **MANDATORY**: Use `MovingCameraScene` for 2D, `ThreeDScene` for 3D.
        </camera_rules>
        """

    # 5. Prepare Audio/Voiceover Context
    audio_str = ""
    voice_script = state.get("voiceover_script")
    
    if voice_script:
        segments = voice_script.get("segments", [])
        total_dur = voice_script.get("total_duration", 0)
        
        # Format segments for the LLM
        seg_list = []
        for i, seg in enumerate(segments):
            dur = seg.get("actual_duration", 3.0)
            text = seg.get("text", "")[:50] + "..."
            cue = seg.get("visual_cue", "General visual")
            seg_list.append(f"   - Segment {i+1}: Duration={dur:.2f}s | Cue='{cue}' | Text='{text}'")
            
        audio_context = "\n".join(seg_list)
        
        audio_str = f"""
        ### 🎙️ VOICEOVER SYNCHRONIZATION (CRITICAL):
        Total Voiceover Duration: {total_dur:.2f}s
        
        TIMING SEGMENTS:
        {audio_context}
        
        <timing_rules>
        1. You MUST synchronize your animations to these segments.
        2. Use `self.wait(...)` where appropriate to match the duration.
        3. Break your `construct` method into sections corresponding to these segments.
        4. Example:
           ```python
           # Segment 1 (Duration: 4.5s)
           self.play(Write(formula), run_time=2.0)
           self.wait(2.5) # Pad to reach ~4.5s
           ```
        5. DO NOT rush. If the audio is long, use slow animations or longer waits.
        </timing_rules>
        """

    # 6. Prepare Parameter Sweep Context
    sweep_str = ""
    sweep_data = state.get("parameter_sweep")
    
    if sweep_data:
        params = sweep_data.get("parameters", [])
        rec = sweep_data.get("recommendation", "Visualize the effect of changing parameters.")
        
        p_list = []
        for p in params:
            name = p.get("name")
            sym = p.get("symbol")
            vals = p.get("interesting_values", [])
            effect = p.get("visual_effect", "")
            p_list.append(f"   - {name} ({sym}): Test values {vals}. Effect: {effect}")
            
        sweep_context = "\n".join(p_list)
        
        sweep_str = f"""
        ### 🧪 PARAMETER EXPLORATION (SCIENTIFIC VISUALIZATION):
        Technique: {rec}
        
        VARIABLES TO VARY:
        {sweep_context}
        
        <exploration_rules>
        1. Create a scene that shows the effect of changing these variables.
        2. Preferred method: Side-by-side comparison (VGroup arranged horizontally).
        3. Or: Sequential transformation (animate ValueTracker from min to max).
        4. Display the value of the variable dynamically (DecimalNumber or MathTex).
        </exploration_rules>
        """

    # 5. Construct System Prompt
    style_instruction = get_style_prompt()
    
    system_prompt = f"""
    You are a Senior Manim Developer (v0.19.1).
    
    ### 🎨 VISUAL STYLE (3Blue1Brown):
    {style_instruction}
    
    {camera_str}
    
    {audio_str}
    
    {sweep_str}
    
    ### 📚 OFFICIAL DOCUMENTATION (USE THIS SYNTAX):
    {rag_context}
    
    ### 🛡️ LAYOUT & SAFETY RULES:
    {MANIM_SPATIAL_RULES}
    
    <instructions>
    1. **Imports**: `from manim import *` AND `from layout_helper import smart_position, fit_text`.
    2. **Class**: `class PhysicsScene(Scene):` or `class PhysicsScene(ThreeDScene):`. **NAME MUST BE `PhysicsScene`**.
    3. **Physics**: Implement the equations and explanation if provided.
    4. **Rate Functions**: YOU MUST use `rate_functions.linear`, `rate_functions.smooth`, `rate_functions.ease_in_out_sine`, etc. **NEVER use `out_quad` or `smooth` directly**. ALWAYS prefix with `rate_functions.`.
    5. **HUD/Fixed Elements**: DO NOT use `fix_in_frame` or `self.camera.fixed_in_frame_mobjects`. Use `self.add_fixed_in_frame_mobjects(mob)` instead.
    6. **Camera**: If using `Restore(self.camera.frame)`, you MUST call `self.camera.frame.save_state()` at the start of the scene.
    7. **Class**: ALWAYS use `class PhysicsScene(MovingCameraScene):`. Never use `Scene` directly, to ensure camera methods work.
    8. **Positioning**: DO NOT use `layout_helper`. Use standard methods: `to_corner`, `to_edge`, `next_to`, `move_to`, `align_to`.
    9. **Performance**: Avoid creating NEW Mobjects inside `add_updater` loops. pre-create them and update their attributes (points, position, color).
    10. **Output**: Return ONLY the Python code.
    </instructions>
    """
    
    input_text = f"""
    TASK: Write a Manim script for this request.
    
    USER PROMPT: {user_prompt}
    
    VISUAL PLAN:
    {plan}
    
    PHYSICS REQUIREMENTS:
    {equations_str}
    
    IMPORTANT:
    - If Camera Actions are present, you MUST inherit from `MovingCameraScene` (2D) or `ThreeDScene`.
    - `class PhysicsScene(MovingCameraScene):` is preferred for standard 2D physics with zoom.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=input_text)
    ]
    
    # Use Pro model for coding
    llm = get_llm(model_type="pro")
    
    response = await llm.ainvoke(messages)
    content = extract_text_content(response)

    clean_code = strip_code_fences(content)
    
    return {
        "code": clean_code, 
        "logs": [f"Retrieved docs for: {keywords}"]
    }
