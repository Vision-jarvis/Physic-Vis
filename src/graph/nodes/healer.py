from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm
from src.graph.state import AgentState

HEALER_SYSTEM_PROMPT = """You are a Senior Python Expert and Manim Debugger.
Your task is to FIX broken Manim code based on the error traceback provided.

<instructions>
1. Analyze the Error Log carefully. Look for `AttributeError`, `TypeError`, or `UnicodeEncodeError`.
2. Fix the specific issue in the code. Do not rewrite the entire logic if not needed.
3. Ensure no deprecated methods are used (e.g. `ShowCreation` -> `Create`).
4. Return ONLY the fixed Python code. No markdown backticks.
</instructions>
"""

from src.knowledge.error_kb import ErrorKnowledgeBase

async def healer_node(state: AgentState):
    """
    Node D: The Healer (Self-Correction)
    Uses Error RAG + Gemini 3.0 Pro to fix code.
    """
    print("--- NODE: Healer (Smart Auto-Fix) ---")
    
    code = state.get("code")
    error_logs = state.get("logs", "")
    retries = state.get("retry_count", 0)
    topic = state.get("physics_code", {}).get("topic", "General")
    
    # Infinite Loop Guard
    if retries >= 3:
        print("   🛑 Max Retries Reached. Aborting.")
        return {"error": "MaxRetriesExceeded"}
    
    print(f"   🚑 Attempting Fix #{retries + 1}...")
    
    # Initialize RAG
    kb = ErrorKnowledgeBase()
    
    # 1. Log the Error
    kb.log_error({
        "error_type": "RuntimeError", # simplified
        "error_message": error_logs[-500:], # limited context
        "code": code,
        "topic": topic
    })
    
    # 2. Check for Similar Fixes
    similar_fix = kb.find_similar_fix(error_logs[-500:])
    fix_method = "llm"
    
    llm = get_llm(model_type="pro")
    
    if similar_fix:
        print(f"   🎯 Found similar error (Confidence: {similar_fix['similarity']:.2f})")
        print(f"      Strategy: {similar_fix['fix_method']}")
        
        # RAG-Assisted Prompt
        input_text = f"""
        ERROR ENCOUNTERED:
        {error_logs}
        
        SIMILAR PAST ERROR (Solved):
        {similar_fix['original_error']}
        
        SUCCESSFUL FIX STRATEGY:
        {similar_fix['fixed_code']}
        
        TASK: Apply the same fix strategy to the BROKEN CODE below.
        
        BROKEN CODE:
        ```python
        {code}
        ```
        """
        fix_method = "rag"
    else:
        print("   🤖 No similar error found. Using standard LLM reasoning.")
        input_text = f"""
        The following Manim code failed to run:
        
        ```python
        {code}
        ```
        
        Error Output:
        {error_logs}
        
        Please provide the FIXED code.
        """
    
    messages = [
        SystemMessage(content=HEALER_SYSTEM_PROMPT),
        HumanMessage(content=input_text)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        fixed_code = response.content.replace("```python", "").replace("```", "").strip()
        
        return {
            "code": fixed_code,
            "retry_count": retries + 1,
            "error": None,
            "original_error": error_logs[-1000:], # Store for RAG logging on success
            "original_code": code,
            "fix_method": fix_method
        }
        
    except Exception as e:
        print(f"   ❌ Healer Failed: {e}")
        return {"error": f"HealerError: {str(e)}"}
