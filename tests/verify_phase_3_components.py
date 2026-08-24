import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph.nodes.feynman import feynman_node
from src.graph.nodes.cinematographer import cinematographer_node
from src.graph.nodes.narrator import narrator_node
from src.graph.state import AgentState

async def verify_phase_3_components():
    print("\n🧪 Verifying Phase 3 Components (Logic Only)...")
    
    # 1. Setup Input
    state: AgentState = {
        "user_prompt": "Explain Voltage.",
        "plan": "1. Introduction. 2. Visual Metaphor. 3. Conclusion.",
        "physics_data": {
            "equations": ["V = IR"],
            "explanation": "Voltage is potential difference.",
            "core_concept": "Voltage"
        }
    }
    
    # 2. Test FEYNMAN Node
    print("\n--- 1. Testing Feynman Node ---")
    state = await feynman_node(state)
    analogy = state.get("analogy", {})
    print(f"✅ Analogy: {analogy.get('analogy_text')[:50]}...")
    assert analogy.get("analogy_text"), "Feynman failed to generate analogy text"
    assert analogy.get("visual_metaphor"), "Feynman failed to generate visual metaphor"

    # 3. Test CINEMATOGRAPHER Node (Prerequisite for Narrator)
    print("\n--- 2. Testing Cinematographer Node ---")
    state = await cinematographer_node(state)
    camera = state.get("camera_instructions", {})
    print(f"✅ Pacing: {camera.get('pacing')}")
    assert camera.get("pacing"), "Cinematographer failed to generate pacing"

    # 4. Test NARRATOR Node
    print("\n--- 3. Testing Narrator Node ---")
    state = await narrator_node(state)
    script = state.get("voiceover_script", "")
    print(f"✅ Script: {script[:50]}...")
    
    assert script, "Narrator failed to generate script"
    assert len(script) > 10, "Script is suspiciously short"
    
    # Verify Script respects Analogy
    if analogy.get("visual_metaphor").lower() in script.lower() or \
       "like" in script.lower() or "imagine" in script.lower():
         print("✅ Script incorporates analogy elements.")
    else:
         print("⚠️ Script might be missing the analogy.")
         
    print("\n🎉 Phase 3 Logic Verified successfully!")

if __name__ == "__main__":
    asyncio.run(verify_phase_3_components())
