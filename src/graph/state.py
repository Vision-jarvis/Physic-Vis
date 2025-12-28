from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    """
    The memory state of the graph passed between nodes.
    """
    user_prompt: str          # Initial user request
    
    # Architect Output
    plan: Optional[str]       # Visual description of the scene
    
    # Physicist Output
    physics_code: Optional[Dict[str, Any]] # JSON with equations, explanations
    
    # Coder Output
    code: Optional[str]       # The Manim Python script
    
    # Execution Output
    logs: Optional[str]       # STDERR/STDOUT from Docker
    video_path: Optional[str] # Path to the final MP4
    
    # Metadata
    retry_count: int          # To prevent infinite loops
    error: Optional[str]      # Current error state
    
    # Healer/RAG Metadata
    original_error: Optional[str] # Error that triggered the fix
    original_code: Optional[str]  # Code that caused the error
    fix_method: Optional[str]     # 'rag', 'llm', 'manual'
