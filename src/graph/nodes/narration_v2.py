from src.graph.state import AgentState
from src.graph.nodes.script_writer import script_writer_node
from src.core.narration.sync import SyncEngine
import os

async def narration_node_v2(state: AgentState):
    """
    Orchestrates the full narration pipeline:
    1. Write Script (LLM)
    2. Generate Audio & Sync (TTS + FFmpeg)
    3. Update State with 'audio_plan' for Coder.
    """
    print("--- NODE: Narration V2 (Typesetting & Audio) ---")
    
    # 1. Generate Script
    script_result = await script_writer_node(state)
    script = script_result.get("voiceover_script")
    
    if not script:
        return {"error": "ScriptGenerationFailed"}
        
    # 2. Sync & Audio Gen
    # 2. Sync & Audio Gen
    
    # Check if TTS is enabled (via key presence or flag)
    from src.core.config import settings
    
    if not settings.eleven_labs_api_key:
        print("   ⚠️ No ElevenLabs Key found. Skipping TTS (Silent Mode).")
        return {"voiceover_script": script}

    # Safe topic name generation
    import re
    raw_topic = state.get("user_prompt", "default")
    # Take first line only, strip special chars
    safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', raw_topic.split('\n')[0])[:30]
    
    output_dir = os.path.join("output", "audio", safe_topic)
    os.makedirs(output_dir, exist_ok=True)
    
    sync_engine = SyncEngine()
    try:
        updated_script = sync_engine.process_script(script, output_dir)
        print(f"   ✅ Audio Generated. Total Duration: {updated_script['total_duration']:.2f}s")
        return {
            "voiceover_script": updated_script,
            "audio_dir": output_dir
        }
    except Exception as e:
        print(f"   ⚠️ Audio Generation Failed: {e}")
        # Return script without audio paths -> Coder handles as silent or estimated
        return {"voiceover_script": script}
