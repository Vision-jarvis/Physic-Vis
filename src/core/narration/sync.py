import os
import time
from typing import Dict, List
from src.core.narration.tts import VoiceSynthesizer
# We need mutagen or similar to get audio length, or just rely on file size/bitrate estimate if lib not avail.
# Or use ffmpeg probe.
import subprocess
import json

class SyncEngine:
    """
    Synchronizes narration script with audio files.
    Calculates exact durations for the Coder.
    """
    
    def __init__(self):
        self.tts = VoiceSynthesizer()
        
    def process_script(self, script: Dict, output_dir: str) -> Dict:
        """
        1. Generates audio for each segment.
        2. Updates segment with 'audio_path' and 'actual_duration'.
        3. Returns updated script.
        """
        updated_segments = []
        total_duration = 0.0
        
        print("   ⏱️ Sync Engine: Generating Audio & Timing...")
        
        for i, segment in enumerate(script.get("segments", [])):
            text = segment["text"]
            filename = f"segment_{i:03d}.mp3"
            path = os.path.join(output_dir, filename)
            
            # Generate Audio
            try:
                if not os.path.exists(path):
                    self.tts.synthesize(text, path)
                
                # Get Duration
                duration = self._get_audio_duration(path)
                
            except Exception as e:
                print(f"      ⚠️ Audio Gen Failed for seg {i}: {e}")
                duration = segment.get("estimated_duration", 3.0)
                path = None
                
            segment["audio_path"] = path
            segment["actual_duration"] = duration
            updated_segments.append(segment)
            total_duration += duration
            
        script["segments"] = updated_segments
        script["total_duration"] = total_duration
        
        # Save manifest
        manifest_path = os.path.join(output_dir, "audio_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(script, f, indent=2)
            
        return script
        
    def _get_audio_duration(self, file_path: str) -> float:
        """
        Get duration via ffprobe.
        """
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            file_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            # Fallback estimation (approx 150wpm)
            # This is risky but better than crashing
            return 3.0 
