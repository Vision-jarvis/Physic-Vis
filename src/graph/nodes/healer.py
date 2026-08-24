from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState
from src.knowledge.error_kb import ErrorKnowledgeBase
from src.knowledge.retriever import retrieve_docs
from src.graph.utils.extractor import extract_manim_keywords
from src.utils.llm_helpers import extract_text_content, strip_code_fences
import re

HEALER_SYSTEM_PROMPT = """You are a Senior Python Expert and Manim Debugger.
Your task is to FIX broken Manim code based on the error traceback provided.

<strategies>
1. If `LaTeX Error`: Simplify the LaTeX string. Remove unsupported commands or complex nesting. Use raw strings `r""`.
2. If `TimeOut`: Simplify the scene. Reduce particle counts or simulation steps.
3. If `AttributeError`: Check if the object is correctly instantiated or if the method exists in v0.19.1.
4. If `AttributeError: ... has no attribute 'fix_in_frame'`: Do NOT use `fix_in_frame`. Use `self.add_fixed_in_frame_mobjects(mob)` instead.
5. If `Exception: Trying to restore without having saved`: Remove the `Restore()` animation or ensure `save_state()` was called.
6. If `UFuncTypeError` (string vs float): Check `move_to`, `shift`, or `smart_position`. Ensure you are NOT passing strings (like "top_right") to geometric methods. Use `to_corner(UR)` instead.
7. If `TypeError: ... unexpected keyword argument 'opacity'`: Replace `opacity` with `fill_opacity` or `stroke_opacity` (e.g. for Dot, Rectangle).
8. If `NameError: name 'ease_out_sine' is not defined`: Use `rate_func=rate_functions.ease_out_sine` or import it.
9. If `AttributeError: ... has no attribute 'revert_to_original_size'`: Use `self.wait()` or manually reset frame height/width if needed.
</strategies>
"""

async def healer_node(state: AgentState):
    """
    Node D: The Healer (Self-Correction) with Doc RAG
    """
    print("--- NODE: Healer (RAG-Enhanced) ---")
    
    code = state.get("code")
    error_logs = state.get("logs", "")
    attempts = state.get("heal_attempts", 0)
    if attempts >= 3:
        print("   🛑 Max Retries Reached. Aborting.")
        return {"error": "MaxRetriesExceeded"}
    
    print(f"   🚑 Attempting Fix #{attempts + 1}...")

    state["heal_attempts"] = attempts + 1
    
    # 1. Error RAG (Historical Fixes)
    kb = ErrorKnowledgeBase()
    kb.log_error({
        "error_type": "RuntimeError", 
        "error_message": error_logs[-500:], 
        "code": code,
        "topic": state.get("user_prompt", "General")
    })
    similar_fix = kb.find_similar_fix(error_logs[-500:])
    
    # 2. Doc RAG (Official Docs for failing components)
    # Strategy: Extract Manim keywords from the code lines that likely caused the error
    # Or just run the extractor on the error message (might work if error contains class names)
    
    # Simple heuristic: look for "AttributeError: 'X' object" -> X
    doc_keywords = []
    
    # Try extracting from error message first
    # e.g. "NameError: name 'FadeInFrom' is not defined" -> FadeInFrom
    # e.g. "AttributeError: 'Circle' object" -> Circle
    
    # Regex for quoted words in error (often class/method names)
    quoted_words = re.findall(r"'([^']*)'", error_logs[-500:])
    # Also simple alphanumeric words in the last line
    last_line = error_logs.strip().split('\n')[-1]
    
    # Combine potential keywords
    potential_keywords = quoted_words + extract_manim_keywords(last_line)
    # Deduplicate
    doc_keywords = list(set(k for k in potential_keywords if k and k[0].isupper())) # Primitive filter for Classes
    
    doc_context = ""
    if doc_keywords:
        print(f"   🩺 Healer identifying docs for: {doc_keywords}")
        doc_context = retrieve_docs(doc_keywords[:3])
        
    
    # Construct Inputs
    llm = get_llm(model_type="pro")
    
    input_text = f"""
    ERROR ENCOUNTERED:
    {error_logs}
    
    BROKEN CODE:
    ```python
    {code}
    ```
    
    OFFICIAL DOCUMENTATION (RELEVANT TO ERROR):
    {doc_context[:3000]}
    """
    
    if similar_fix:
        print(f"   🎯 Found similar past error (Confidence: {similar_fix['similarity']:.2f})")
        input_text += f"""
        
        SIMILAR PAST FIX:
        {similar_fix['fixed_code']}
        """

    input_text += "\nTASK: Fix the code. Return ONLY the fixed Python code."

    messages = [
        SystemMessage(content=HEALER_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = extract_text_content(response)
        fixed_code = strip_code_fences(content)
        
        return {
            "code": fixed_code,
            "retry_count": state.get("retry_count", 0) + 1,
            "heal_attempts": state.get("heal_attempts", 0) + 1,
            "error": None,
            "original_error": error_logs[-1000:], 
            "original_code": code,
            "fix_method": "rag_hybrid"
        }
        
    except Exception as e:
        print(f"   ❌ Healer Failed: {e}")
        return {"error": f"HealerError: {str(e)}"}
