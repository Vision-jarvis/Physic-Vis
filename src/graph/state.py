from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict, total=False):
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
    render_output_path: Optional[str] # Path to the final MP4
    
    # 3.0 Upgrades (Pedagogical)
    concept_graph: Optional[Dict[str, Any]] # Prerequisites from ConceptMapper
    color_scheme: Optional[Dict[str, str]]  # Semantic color mapping
    camera_instructions: Optional[Dict[str, Any]] # Camera & Pacing directives
    analogy: Optional[Dict[str, str]]       # Feynman's simplifications
    voiceover_script: Optional[Dict[str, Any]]         # Final TTS script (timestamped)
    parameter_sweep: Optional[Dict[str, Any]] # For Logic Explorer
    
    # Metadata
    retry_count: int          # To prevent infinite loops
    error: Optional[str]      # Current error state
    
    # Healer/RAG Metadata
    original_error: Optional[str] # Error that triggered the fix
    original_code: Optional[str]  # Code that caused the error
    fix_method: Optional[str]     # 'rag', 'llm', 'manual'
