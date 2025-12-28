from src.graph.state import AgentState
from src.execution.local_runner import LocalDockerRunner
import os
from src.knowledge.error_kb import ErrorKnowledgeBase

def renderer_node(state: AgentState):
    """
    Node C: The Renderer (Execution)
    Runs the generated code in Docker and updates state with the result.
    """
    print("--- NODE: Renderer (Docker) ---")
    code = state.get("code")
    if not code:
        return {"error": "No code to render."}
    
    # Initialize Runner
    runner = LocalDockerRunner(image_name="manim-renderer:v0.18")
    
    print("   🎬 executing Manim...")
    status, logs, video_path = runner.run_code(code)
    
    if status == "SUCCESS":
        print(f"   ✅ Render Success: {video_path}")
        
        # Self-Learning: Log successful fix if this was a recovery
        if state.get("retry_count", 0) > 0 and state.get("original_error"):
            try:
                kb = ErrorKnowledgeBase()
                kb.log_successful_fix({
                    "original_error": state.get("original_error"),
                    "original_code": state.get("original_code"),
                    "fixed_code": code,
                    "fix_method": state.get("fix_method", "unknown"),
                    "attempts": state.get("retry_count"),
                    "topic": state.get("physics_code", {}).get("topic", "General")
                })
                print("   🧠 Self-Healing: Fix logged to Error Knowledge Base.")
            except Exception as e:
                print(f"   ⚠️ Failed to log fix to KB: {e}")
            
        return {
            "video_path": video_path,
            "error": None, # Clear any previous errors
            "logs": logs
        }
    else:
        print(f"   ❌ Render Failed. Logs:\n{logs[-1000:]}") # Print last 1000 chars of error
        return {
            "error": "RuntimeError", # Tag as runtime error
            "logs": logs,
            "video_path": None
        }
