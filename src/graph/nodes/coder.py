from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
import json
import os
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def retrieve_manim_docs(query: str, k: int = 5) -> str:
    """Retrieves relevant Manim documentation from Pinecone."""
    api_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = "manim-knowledge"
    
    if not pinecone_key or not api_key:
        return ""
        
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = PineconeVectorStore(
            index_name=index_name, 
            embedding=embeddings,
            pinecone_api_key=pinecone_key
        )
        # Search for both specific classes in the query and general concepts
        docs = vectorstore.similarity_search(query, k=k)
        
        context_str = "\n".join([
            f"--- Class: {d.metadata.get('name')} ---\n"
            f"Signature: {d.metadata.get('full_signature')}\n"
            f"Description: {d.page_content}" 
            for d in docs
        ])
        return context_str
    except Exception as e:
        print(f"RAG Warning: Failed to retrieve Manim docs: {e}")
        return ""

MANIM_SPATIAL_RULES = """
CRITICAL COORDINATE SYSTEM RULES (Manim Community Edition v0.18):

Screen Bounds (16:9 aspect ratio):
- X-axis: -7.0 to +7.0 (width = 14 units)
- Y-axis: -4.0 to +4.0 (height = 8 units)
- Z-axis: -5.0 to +5.0 (depth, for 3D scenes)

MANDATORY PLACEMENT RULES:
1. ALL objects MUST be positioned within: x ∈ [-6, 6], y ∈ [-3.5, 3.5]
2. Text/Equations MUST be scaled down using `.scale(0.8)` after creation. DO NOT pass `scale=` as an argument.
3. If equation length > 10 characters, use `.scale(0.6)`.
4. NEVER use move_to() with coordinates outside bounds.

ANTI-PATTERNS (DO NOT USE THESE):
❌ `MathTex(..., scale=0.5)` -> INVALID. Use `MathTex(...).scale(0.5)`.
❌ `next_to(..., alignment=...)` -> INVALID. Use `next_to(..., aligned_edge=...)`.
❌ `Mobject(..., base=...)` -> INVALID. 'base' is not a valid argument.
❌ `Color("#hex").interpolate()` -> INVALID. Use `ManimColor("#hex").interpolate()`.
❌ `remove_updater()` -> INVALID. Must pass function or use `clear_updaters()`.
❌ `LightSource` -> INVALID. Use `PointLight` or `AmbientLight`.
❌ `get_line_from_axis_to_point(..., stroke_opacity=...)` -> INVALID.
❌ `self.camera.frame` (Only for MovingCameraScene) -> Use `self.camera.animate.zoom(1.2)` or `set_focal_distance`.
❌ `set_glow()` or `add_glow_effect()` -> NOT AVAILABLE.
❌ `numpy_array.rotate()` -> Use `Start.animate.rotate(angle)` or `Rotate(mobject)`.
❌ `FadeInFrom` -> Deprecated. Use `FadeIn(mob, shift=DOWN)`.
❌ `ShowCreation` -> Deprecated. Use `Create`.

VALIDATION CHECKLIST:
✓ All move_to() coordinates within [-6, 6] × [-3.5, 3.5]?
✓ No `self.camera.frame` unless inheriting MovingCameraScene?
✓ No `scale=` keyword arguments in constructors?
✓ No `base=` or `alignment=` arguments?
✓ `ThreeDScene` used if `phi/theta` requested?
✓ No `set_glow` calls?
"""

CODER_SYSTEM_PROMPT = f"""You are a Senior Manim Engineer specializing in physics visualizations.

{MANIM_SPATIAL_RULES}

<instructions>
1. **Imports**: 
    - Always start with `from manim import *`.
    - **CRITICAL**: Add `from layout_helper import smart_position, fit_text`
    
2. **Class Structure**: Define a class inheriting from `Scene`. Name it `PhysicsScene`.
    - **CRITICAL DECISION**:
        - If the Architect asks for 3D layout (phi, theta, set_camera_orientation) -> `class PhysicsScene(ThreeDScene):` (PRIORITY)
        - If the Architect ONLY asks for Zoom/Pan (no 3D angles) -> `class PhysicsScene(MovingCameraScene):`
        - Otherwise -> `class PhysicsScene(Scene):`

3. **Equations**: If provided in the input, YOU MUST display the LaTeX equations on screen using `MathTex`.
    - **LATEX SAFETY**: Use raw strings r"..." for all TeX. Escape special chars correctly.
    - **SCALING**: `MathTex(r"E=mc^2").scale(0.8)` (NOT as kwarg).
    - **COLORS**: If interpolating, wrap hex in ManimColor: `ManimColor("#FF0000").interpolate(...)`.

4. **Layout & Safety**: 
    - **Use `smart_position(mobject)`** on ANY object that moves near the edge.
    - **Use `fit_text("Long string", font_size=24)`** for explanations.
    - Do NOT use `wait()` for longer than 5 seconds total.
    - Do NOT use infinite loops (`while True`).
    - Do NOT use `should_use_latex` argument for `Text` mobjects. Use `Tex` or `MathTex` instead.
    - Do NOT use `ease_in_quad` directly. Use `rate_functions.ease_in_quad`.
    - **Use the Reference Documentation provided to ensure correct arguments.**

5. **Output**: Return ONLY the Python code. No markdown backticks.

IMPORTANT: Before returning code, mentally visualize the layout. 
If ANY object might be off-screen, reposition it or use `smart_position()`.
</instructions>
"""

async def coder_node(state: AgentState):
    """
    Node C: The Coder
    Uses Gemini 1.5 Pro to write the Manim script.
    """
    print("--- NODE: Coder ---")
    plan = state.get("plan")
    user_prompt = state.get("user_prompt")
    physics_data = state.get("physics_code", {})
    
    # RAG: Retrieve Manim Docs based on the plan
    manim_context = retrieve_manim_docs(f"{user_prompt}\n{plan}")
    
    # Parse physics data if it exists
    equations_str = ""
    if physics_data:
        eqs = physics_data.get("equations", [])
        explanation = physics_data.get("explanation", "")
        placement = physics_data.get("placement", "UP")
        
        equations_str = f"""
        REQUIRED EQUATIONS TO DISPLAY:
        {json.dumps(eqs, indent=2)}
        
        EXPLANATION TEXT TO SHOW:
        "{explanation}"
        
        PLACEMENT: {placement}
        """

    llm = get_llm(model_type="pro")
    
    input_text = f"""
    TASK: Write a Manim script for this request.
    
    USER PROMPT: {user_prompt}
    
    VISUAL PLAN:
    {plan}
    
    REFERENCE DOCUMENTATION (USE THIS FOR SIGNATURES):
    {manim_context}
    
    PHYSICS REQUIREMENTS:
    {equations_str}
    """
    
    messages = [
        SystemMessage(content=CODER_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    response = await llm.ainvoke(messages)
    
    # Clean the output (strip backticks if the model ignores the instruction)
    clean_code = response.content.replace("```python", "").replace("```", "").strip()
    
    return {"code": clean_code}
