import os
import json
import asyncio
import random
import shutil
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
from src.graph.workflow import create_graph

load_dotenv()

# Configuration
INPUT_FILE = "src/knowledge/data/comprehensive_physics.json"
OUTPUT_DIR = "batch_output"
STATS_FILE = "batch_statistics.json"
BATCH_SIZE = 55
NUM_RUNS = 2

class BatchStatistics:
    def __init__(self):
        self.stats = {
            "timestamp": datetime.now().isoformat(),
            "runs": []
        }
    
    def start_run(self, run_index: int):
        self.current_run = {
            "run_index": run_index,
            "total_items": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "first_attempt_success": 0,
            "healed_success": 0,
            "rag_fixes_used": 0,
            "unique_errors": {}, # error_msg -> count
            "details": [] # List of per-item results
        }
        self.stats["runs"].append(self.current_run)
    
    def log_item(self, concept: str, result: Dict[str, Any]):
        item_stats = {
            "concept": concept,
            "status": "SUCCESS" if result.get("video_path") else "FAILED",
            "retry_count": result.get("retry_count", 0),
            "fix_method": result.get("fix_method"),
            "original_error": result.get("original_error"),
            "final_error": result.get("error") if not result.get("video_path") else None
        }
        
        # Update Counters
        self.current_run["total_items"] += 1
        self.current_run["processed"] += 1
        
        if item_stats["status"] == "SUCCESS":
            self.current_run["success"] += 1
            if item_stats["retry_count"] == 0:
                self.current_run["first_attempt_success"] += 1
            else:
                self.current_run["healed_success"] += 1
                
            if item_stats["fix_method"] == "rag":
                self.current_run["rag_fixes_used"] += 1
        else:
            self.current_run["failed"] += 1
            error_msg = str(item_stats["final_error"])
            # Simplify error for aggregation (first line)
            error_key = error_msg.split('\n')[-1] if error_msg else "Unknown Error"
            self.current_run["unique_errors"][error_key] = self.current_run["unique_errors"].get(error_key, 0) + 1
            
        self.current_run["details"].append(item_stats)
        
    def end_run(self):
        self.save()
        
    def save(self):
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)
        print(f"\n📊 Statistics saved to {STATS_FILE}")

async def run_batch():
    # 1. Setup
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    input_path = os.path.join(os.path.dirname(__file__), '..', '..', INPUT_FILE)
    if not os.path.exists(input_path): # Fallback if CWD is different
        input_path = INPUT_FILE
        
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Shuffle once, use same list for both runs to compare apple-to-apples
    candidates = [item for item in data if item.get('concept')]
    random.seed(42)
    random.shuffle(candidates)
    selected_concepts = candidates[:BATCH_SIZE]
    
    stats_tracker = BatchStatistics()
    
    # 2. Execution Loop (Structure: Run 1 -> Run 2)
    for run_idx in range(1, NUM_RUNS + 1):
        print(f"\n\n{'='*50}")
        print(f"🏃 STARTING RUN {run_idx}/{NUM_RUNS}")
        print(f"{'='*50}\n")
        
        stats_tracker.start_run(run_idx)
        app = create_graph() # Re-create graph to ensure fresh state if needed, though usually stateless
        
        for i, concept in enumerate(selected_concepts):
            topic = concept.get('topic', 'Unknown')
            name = concept.get('concept', 'Unknown')
            safe_name = f"{topic}_{name}".replace(" ", "_").replace("/", "-").replace("\\", "")
            
            # For Run 2, we force re-generation even if file exists?
            # User wants to see "Self Ragging Work", so yes, we should probably output to a run-specific folder 
            # OR just overwrite. Overwriting is cleaner for "Improving" the video, 
            # but logging stats is what matters.
            # Let's use run-specific output filenames if we want to compare videos, 
            # but user just wants stats. Let's overwrite to keep it simple, 
            # but we need to prevent "Skipping (Already exists)" logic for Run 2.
            
            print(f"\n[{run_idx}/{NUM_RUNS}][{i+1}/{BATCH_SIZE}] 🎬 Processing: {topic} - {name}")
            
            try:
                inputs = {
                    "user_prompt": f"Create a detailed, cinematic animation explaining {name} in the context of {topic}. {concept.get('manim_visual_cues', '')}",
                    "retry_count": 0
                }
                
                # Run Graph
                result = await app.ainvoke(inputs, {"recursion_limit": 50})
                
                # Process Result
                video_file = result.get("video_path")
                if video_file and os.path.exists(video_file):
                    final_path = os.path.join(OUTPUT_DIR, f"{safe_name}_run{run_idx}.mp4")
                    shutil.copy(video_file, final_path)
                    print(f"   ✅ SUCCESS -> {final_path}")
                    if result.get("retry_count", 0) > 0:
                        print(f"   💊 Healed! (Attempts: {result['retry_count']}, Method: {result.get('fix_method')})")
                else:
                    print(f"   ❌ FAILED -> {result.get('error')}")
                    # Log full error for user inspection
                    err_log_path = os.path.join(OUTPUT_DIR, f"{safe_name}_run{run_idx}_error.log")
                    with open(err_log_path, "w", encoding='utf-8') as logf:
                        logf.write(f"Error: {result.get('error')}\n")
                        logf.write(f"Logs: {result.get('logs')}")
                
                # Log Statistics
                stats_tracker.log_item(f"{topic} - {name}", result)
                stats_tracker.save() # Save incrementally
                
            except Exception as e:
                print(f"   💥 CRASH: {e}")
                stats_tracker.log_item(f"{topic} - {name}", {"error": str(e)})
            
            # Rate limit
            await asyncio.sleep(2)
            
        stats_tracker.end_run()

if __name__ == "__main__":
    asyncio.run(run_batch())

