import os
import json
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.llm import get_llm

load_dotenv()

OUTPUT_FILE = "src/knowledge/data/comprehensive_physics.json"
DOMAINS = {
    "Classical Mechanics": ["Kinematics", "Newton's Laws", "Work & Energy", "Momentum", "Rotational Motion", "Gravitation", "Oscillations", "Fluid Mechanics"],
    "Electromagnetism": ["Electrostatics", "Electric Fields", "Gauss's Law", "Electric Potential", "Capacitance", "Circuits", "Magnetostatics", "Induction", "Maxwell's Equations", "EM Waves"],
    "Thermodynamics": ["Temperature & Heat", "Kinetic Theory", "First Law", "Entropy & Second Law", "Heat Engines", "Phase Transitions"],
    "Quantum Mechanics": ["Wave-Particle Duality", "Schrödinger Equation", "Quantum Harmonic Oscillator", "Hydrogen Atom", "Spin", "Uncertainty Principle"],
    "Relativity": ["Special Relativity (Time Dilation, Length Contraction)", "Lorentz Transformations", "Energy-Mass Equivalence", "General Relativity (Curvature)"],
    "Optics": ["Reflection & Refraction", "Lenses & Mirrors", "Interference", "Diffraction", "Polarization"]
}

SYSTEM_PROMPT = """You are a Physics Professor creating a database for an AI Physics Engine.
Your task is to generate valid JSON objects for physics concepts.

Output Format (List of Objects):
[
  {
    "id": "unique_id_string",
    "topic": "Domain Name",
    "concept": "Specific Concept Name",
    "latex_equations": ["eq1", "eq2"],
    "variables": {"var1": "desc1"},
    "explanation": "Concise physical explanation.",
    "manim_visual_cues": "Instructions for an animator to visualize this."
  }
]

CRITICAL RULES:
1. Return ONLY valid JSON. No markdown decoding.
2. `latex_equations`: Must be valid LaTeX string. Escape backslashes (e.g., "\\frac").
3. `manim_visual_cues`: Be creative. Describe motion, graphs, and vectors.
4. Generate at least 5 distinct concepts for the given sub-topic.
"""

async def generate_topic(domain: str, subtopic: str):
    llm = get_llm(model_type="pro") # Use Pro for high quality knowledge
    
    prompt = f"""
    Generate 5 advanced physics concepts for the Domain: '{domain}' and Sub-topic: '{subtopic}'.
    Ensure rigorous mathematical formulation.
    """
    
    print(f"🧠 Generating: {domain} - {subtopic}...")
    try:
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Failed on {subtopic}: {e}")
        return []

async def main():
    all_knowledge = []
    
    # Check if file exists to maybe append (for now we overwrite to ensure structure)
    if os.path.exists(OUTPUT_FILE):
        print("Wait... appending to existing file not supported in this script version. Overwriting.")
        
    tasks = []
    for domain, subtopics in DOMAINS.items():
        for sub in subtopics:
            tasks.append(generate_topic(domain, sub))
            
    # Run in batches of 5 to respect rate limits
    BATCH_SIZE = 5
    for i in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[i:i+BATCH_SIZE]
        results = await asyncio.gather(*batch)
        for res in results:
            if isinstance(res, list):
                all_knowledge.extend(res)
        print(f"✅ Batch {i//BATCH_SIZE + 1} complete. Total items: {len(all_knowledge)}")
        
    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_knowledge, f, indent=2)
    
    print(f"🎉 Generation Complete! Saved {len(all_knowledge)} concepts to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
