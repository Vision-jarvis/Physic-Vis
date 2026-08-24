from src.graph.state import AgentState
from src.core.batch import BatchLLMProcessor
from src.utils.llm_helpers import extract_text_content, strip_code_fences
from src.prompts.architect_prompt import ARCHITECT_SYSTEM, ARCHITECT_USER
from src.prompts.cinematographer_prompt import CINEMATOGRAPHER_SYSTEM, CINEMATOGRAPHER_USER
import json

async def architect_batch_node(state: AgentState):
    """
    Batched Node: Runs Architect (Plan) AND Cinematographer (Camera) in a single parallel batch.
    Optimization: Saves ~3-5 seconds of latency.
    """
    print("--- NODE: Architect & Cinematographer (Batch) ---")
    
    user_prompt = state.get("user_prompt")
    concept_graph = state.get("concept_graph", {})
    concept_sequence = json.dumps(concept_graph.get("concept_sequence", []), indent=2)
    
    processor = BatchLLMProcessor()
    
    # Define Requests
    requests = [
        # 1. Architect (Visual Plan)
        {
            "messages": [
                {"role": "system", "content": ARCHITECT_SYSTEM},
                {"role": "user", "content": ARCHITECT_USER.format(
                    user_prompt=user_prompt,
                    concept_sequence=concept_sequence
                )}
            ],
            "temperature": 0.9 # Creative
        },
        # 2. Cinematographer (Camera Plan) - Using initial prompt for now
        # Note: Ideally Cinematographer should see the Architect's plan, 
        # but for speed we can let it plan based on the user prompt + concepts
        {
            "messages": [
                {"role": "system", "content": CINEMATOGRAPHER_SYSTEM},
                {"role": "user", "content": f"User Prompt: {user_prompt}\nConcepts: {concept_sequence}"}
            ],
            "temperature": 0.5 # Precise
        }
    ]
    
    print("   🚀 Launching Batch: Architect + Cinematographer...")    # Async Launch
    results = await processor.batch_invoke_async(requests)
    
    # Process Results
    
    # 1. Architect Output
    architect_raw = results[0]
    # print(f"DEBUG ARCHITECT RAW: {str(architect_raw)[:200]}...") # Debug log removed
    architect_content = extract_text_content(architect_raw)
    architect_json = strip_code_fences(architect_content)
    try:
        plan = json.loads(architect_json)
        print("   ✅ Architect Plan Generated.")
    except Exception as e:
        print(f"   ⚠️ Architect Parse Error: {e}")
        plan = {"visual_plan": str(architect_raw)} # Fallback
        
    # 2. Cinematographer Output
    cinema_raw = results[1]
    cinema_content = extract_text_content(cinema_raw)
    cinema_json = strip_code_fences(cinema_content)
    try:
        cinema_data = json.loads(cinema_json)
        camera_actions = cinema_data.get("camera_actions", [])
        pacing = cinema_data.get("pacing", {})
        print("   ✅ Camera Instructions Generated.")
    except Exception as e:
        print(f"   ⚠️ Cinematographer Parse Error: {e}")
        camera_actions = []
        pacing = {}

    return {
        "plan": plan,
        "camera_instructions": {
            "actions": camera_actions,
            "pacing": pacing
        }
    }
