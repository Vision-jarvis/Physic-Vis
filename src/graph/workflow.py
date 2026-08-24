from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes.physicist import physicist_node
from src.graph.nodes.coder import coder_node
from src.graph.nodes.renderer import renderer_node
from src.graph.nodes.healer import healer_node
from src.graph.nodes.concept_mapper import concept_mapper_node
from src.graph.nodes.narration_v2 import narration_node_v2 as narrator_node
from src.graph.nodes.explorer import explorer_node
# New Optimized Nodes
from src.graph.nodes.parallel_creative import parallel_creative_node
from src.graph.nodes.fast_validator import fast_validate_node
from src.execution.spatial_auto_fix import auto_fix_spatial_issues
import os
from src.execution.visual_validator import validate_video_content

def visual_node(state: AgentState):
    """
    Validates the rendered video content.
    """
    print("--- NODE: Visual Validator ---")
    video_path = state.get("render_output_path")
    
    if not video_path:
            return {"error": "VisualError", "logs": "No video file found."}
    
    if not os.path.exists(video_path):
            print("   ⚠️ No video found to validate.")
            return {"error": None}

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

def auto_fix_node(state: AgentState):
    """
    Deterministically strictly clamps coordinates.
    """
    print("--- NODE: Spatial Auto-Fixer ---")
    code = state.get("code")
    result = auto_fix_spatial_issues(code)
    if result['issues_found'] > 0:
        print(f"   🔧 Auto-fixed {result['issues_found']} spatial issues.")
    else:
        print("   ✅ No spatial issues found.")
    return {"code": result["fixed_code"]}

def should_retry(state: AgentState):
    """
    Recovery Path Logic:
    - If error exists and retries < 1: Go to Healer.
    - Else: End.
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if error and error != "MaxRetriesExceeded":
        if retry_count < 1:  # Allow 1 retry
            return "healer"
    return "visual_check"

def route_fast_validator(state: AgentState):
    """
    Fast Validator Logic:
    - If bypass_render is True (Syntax Error), go to Healer immediately.
    - Else, go to Renderer.
    """
    if state.get("bypass_render"):
        print("   🛑 Fast Validator triggered fallback to Healer.")
        return "healer"
    return "renderer"

MAX_HEAL_ATTEMPTS = 3

def should_heal_or_abort(state: AgentState) -> str:
    attempts = state.get("heal_attempts", 0)
    if attempts >= MAX_HEAL_ATTEMPTS:
        print(f"[ABORT] Act failed after {attempts} heal attempts. Skipping.")
        return "abort"
    # To keep previous behavior, we heal if there's an error and limit wasn't reached
    if state.get("error"):
        return "heal"
    return "abort"

def create_graph():
    """
    Constructs the Optimized Workflow V5 (High Performance):
    ConceptMapper -> Physicist -> Parallel(Feynman, ArchitectBatch) -> Narrator -> Coder -> AutoFix -> FastCheck -> Renderer
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("concept_mapper", concept_mapper_node)
    workflow.add_node("physicist", physicist_node)
    workflow.add_node("parallel_creative", parallel_creative_node) # Optimized Parallel Block
    workflow.add_node("explorer", explorer_node) # Parameter Exploration
    workflow.add_node("narrator", narrator_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("auto_fix", auto_fix_node)
    workflow.add_node("fast_validator", fast_validate_node) # Optimized Fast Fail
    workflow.add_node("renderer", renderer_node)
    workflow.add_node("healer", healer_node)
    workflow.add_node("visual_check", visual_node)
    
    # Define Edges
    workflow.set_entry_point("concept_mapper")
    workflow.add_edge("concept_mapper", "physicist")
    
    # Fork: Physicist -> Parallel Creative AND Explorer
    workflow.add_edge("physicist", "parallel_creative")
    workflow.add_edge("physicist", "explorer")
    
    # Join: Both -> Narrator
    workflow.add_edge("parallel_creative", "narrator")
    workflow.add_edge("explorer", "narrator")
    
    workflow.add_edge("narrator", "coder")
    workflow.add_edge("coder", "auto_fix")
    workflow.add_edge("auto_fix", "fast_validator")
    
    # Conditional Edges
    workflow.add_conditional_edges(
        "fast_validator",
        route_fast_validator,
        {
            "healer": "healer",
            "renderer": "renderer"
        }
    )
    
    workflow.add_conditional_edges(
        "renderer",
        should_retry,
        {
            "healer": "healer",
            "visual_check": "visual_check"
        }
    )
    
    workflow.add_edge("healer", "renderer")
    
    workflow.add_conditional_edges(
        "visual_check",
        should_heal_or_abort,
        {
            "heal": "healer",
            "abort": END
        }
    )
    
    return workflow.compile()
