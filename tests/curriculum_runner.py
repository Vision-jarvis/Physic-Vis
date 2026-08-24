import asyncio
import sys
import os
import time
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.workflow import create_graph

# Initialize App
app = create_graph()

CURRICULUM = [
    {
        "topic": "Mechanics",
        "prompt": "Simulate the chaotic motion of a Double Pendulum.",
        "complexity": "High (Chaos)"
    },
    {
        "topic": "Electromagnetism",
        "prompt": "Visualize Maxwell's Equations and the propagation of an electromagnetic wave.",
        "complexity": "Medium (Vector Fields)"
    },
    {
        "topic": "Quantum Mechanics",
        "prompt": "Explain Schrödinger's Cat and the concept of Superposition.",
        "complexity": "High (Abstract)"
    },
    {
        "topic": "Thermodynamics",
        "prompt": "Demonstrate the Second Law of Thermodynamics using particle entropy and diffusion.",
        "complexity": "Medium (Particles)"
    },
    {
        "topic": "Relativity",
        "prompt": "Visualize Time Dilation near a massive object like a Black Hole.",
        "complexity": "High (Spacetime Grid)"
    }
]

# FULL CURRICULUM ENABLED
CURRICULUM = CURRICULUM[4:] # Run Relativity only

async def run_visual_curriculum():
    print("\n📚 Starting Phase 5 Curriculum: 5-Topic Stress Test")
    print("==================================================")
    
    results = []
    
    for i, item in enumerate(CURRICULUM):
        topic = item["topic"]
        prompt = item["prompt"]
        print(f"\n🎓 [{i+1}/5] Topic: {topic}")
        print(f"   📝 Prompt: {prompt}")
        
        start_time = time.time()
        status = "FAILED"
        video_path = None
        error_log = None
        
        try:
            inputs = {"user_prompt": prompt}
            # Run the graph
            final_state = await app.ainvoke(inputs)
            
            # Check Result
            video_path = final_state.get("video_path")
            error = final_state.get("error")
            
            if video_path and os.path.exists(video_path):
                status = "PASS"
            else:
                status = "FAIL"
                error_log = error or "Video path incomplete/missing"
                
        except Exception as e:
            status = "ERROR"
            error_log = str(e)
            
        duration = time.time() - start_time
        print(f"   🚩 Result: {status} ({duration:.1f}s)")
        if video_path:
            print(f"   🎥 Video: {video_path}")
        
        results.append({
            "topic": topic,
            "status": status,
            "duration": duration,
            "error": error_log
        })
        
    print("\n📊 Curriculum Report Card")
    print("========================")
    print(f"{'TOPIC':<20} | {'STATUS':<6} | {'TIME':<8} | {'NOTES'}")
    print("-" * 60)
    
    success_count = 0
    for r in results:
        notes = "" if r["status"] == "PASS" else str(r["error"])[:30] + "..."
        print(f"{r['topic']:<20} | {r['status']:<6} | {r['duration']:.1f}s   | {notes}")
        if r["status"] == "PASS": success_count += 1
        
    print(f"\n🏆 Score: {success_count}/{len(CURRICULUM)}")

if __name__ == "__main__":
    asyncio.run(run_visual_curriculum())
