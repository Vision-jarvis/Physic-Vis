from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes.architect import architect_node
from src.graph.nodes.physicist import physicist_node
from src.graph.nodes.coder import coder_node
from src.graph.nodes.renderer import renderer_node
from src.graph.nodes.healer import healer_node

def should_retry(state: AgentState):
    """
    Conditional Edge Logic:
    - If error exists and retries < 3: Go to Healer.
    - Else: End (Success or Max Retries).
    """
    error = state.get("error")
    if error and error != "MaxRetriesExceeded":
        return "healer"
    return "visual_check"

# Add Visual Validation Node
import os
from src.execution.visual_validator import validate_video_content

def visual_node(state: AgentState):
    """
    Validates the rendered video content.
    """
    print("--- NODE: Visual Validator ---")
    video_path = state.get("video_path")
    
    if not video_path:
            # Maybe failed to create video but no error caught?
            return {"error": "VisualError", "logs": "No video file found."}
    
    if not os.path.exists(video_path):
            print("   ⚠️ No video found to validate.")
            return {"error": None} # Nothing to check

    result = validate_video_content(video_path)
    
    if not result["valid"]:
        issues_str = "\n".join(result["issues"])
        print(f"   ⚠️ Visual Issues Found:\n{issues_str}")
        return {
            "error": "VisualError",
            "logs": f"VISUAL VALIDATION FAILED:\n{issues_str}",
            "retry_count": state.get("retry_count", 0) + 1
        }
        
    print("   ✅ Video Content Validated.")
    return {"error": None}

def create_graph():
    """
    Constructs the LangGraph workflow:
    Architect -> Physicist -> Coder -> Renderer -> (Error?) -> Healer -> Renderer
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("architect", architect_node)
    workflow.add_node("physicist", physicist_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("renderer", renderer_node)
    workflow.add_node("healer", healer_node)
    
    # Define Edges
    workflow.set_entry_point("architect")
    
from src.execution.spatial_auto_fix import auto_fix_spatial_issues

def auto_fix_node(state: AgentState):
    """
    Deterministically strictly clamps coordinates and fixes text scaling.
    Replaces the infinite loop of SpatialValidator.
    """
    print("--- NODE: Spatial Auto-Fixer ---")
    code = state.get("code")
    
    result = auto_fix_spatial_issues(code)
    
    # Log what happened
    if result['issues_found'] > 0:
        print(f"   🔧 Auto-fixed {result['issues_found']} spatial issues.")
        # Optional: Add detailed logs to state if needed
    else:
        print("   ✅ No spatial issues found.")
        
    return {"code": result["fixed_code"]}

def should_retry(state: AgentState):
    """
    Recovery Path Logic (Tier 2):
    - Allow EXACTLY ONE retry via Healer. (retry_count start at 0)
    - If retry_count >= 1, we stop.
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if error and error != "MaxRetriesExceeded":
        if retry_count < 1:  # Allow 0 -> 1 (1 retry)
            return "healer"
    return "visual_check"

def create_graph():
    """
    Constructs the LangGraph Workflow V2 (Linear Pipeline):
    Architect -> Physicist -> Coder -> Auto-Fix -> Renderer -> (VisualCheck | End)
                                         ^         |
                                         |__Healer_| (Max 1 Retry)
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("architect", architect_node)
    workflow.add_node("physicist", physicist_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("auto_fix", auto_fix_node)  # NEW: Top-tier fix
    workflow.add_node("renderer", renderer_node)
    workflow.add_node("healer", healer_node)
    workflow.add_node("visual_check", visual_node)
    
    # Define Edges (The Happy Path)
    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "physicist")
    workflow.add_edge("physicist", "coder")
    workflow.add_edge("coder", "auto_fix")       # Linear flow
    workflow.add_edge("auto_fix", "renderer")    # No conditionals here
    
    # From Renderer: Success -> Visual Check, Failure -> Healer (Maybe)
    workflow.add_conditional_edges(
        "renderer",
        should_retry,
        {
            "healer": "healer",
            "visual_check": "visual_check"
        }
    )
    
    # From Healer: Always try to render again (State updated retry_count)
    workflow.add_edge("healer", "renderer")
    
    # Visual Check: Just logs for now, or could trigger Healer too?
    # For V2, let's keep visual check as a final gate.
    # If Visual fails, we might want to healer?
    
    def route_visual(state: AgentState):
        if state.get("error") == "VisualError":
             # We can try ONE healer pass for visual issues too
             retry_count = state.get("retry_count", 0)
             if retry_count < 1:
                 return "healer"
        return END

    workflow.add_conditional_edges(
        "visual_check",
        route_visual,
        {
            "healer": "healer",
            END: END
        }
    )
    
    return workflow.compile()
