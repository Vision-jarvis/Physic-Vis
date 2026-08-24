import subprocess
import os
from typing import List, Dict

class VideoStitcher:
    """
    Stitches multiple video files into a single cohesive video using ffmpeg.
    """
    
    def stitch_acts(self, act_results: List[Dict], output_path: str) -> str:
        """
        Combine multiple videos with transitions.
        
        Args:
            act_results: List of act result dicts with 'video_path' key.
            output_path: Path for final stitched video.
        
        Returns:
            Path to final video or raises Error.
        """
        # Filter successful acts
        successful_acts = [act for act in act_results if act.get("success") and act.get("video_path")]
        
        if not successful_acts:
            print("   ⚠️ Stitching Skipped: No successful acts found.")
            return None

        # Check for FFMPEG
        import shutil
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
        except ImportError:
            pass
            
        if not shutil.which("ffmpeg"):
            print("   ⚠️ Stitching Skipped: 'ffmpeg' not found in PATH.")
            print(f"   ℹ️ Returning Act {successful_acts[-1]['act_number']} video as result.")
            return successful_acts[-1]['video_path']

        
        # Create file list for ffmpeg
        # ffmpeg requires a text file with "file '/path/to/vid.mp4'"
        # We'll put this in the output dir to avoid temp permissions issues
        output_dir = os.path.dirname(output_path) or "."
        filelist_path = os.path.join(output_dir, "stitch_list.txt")
        
        with open(filelist_path, 'w', encoding='utf-8') as f:
            for act in successful_acts:
                # Use forward slashes for ffmpeg compatibility on Windows
                path = act['video_path'].replace("\\", "/")
                f.write(f"file '{path}'\n")
        
        print(f"   🎞️ Stitching {len(successful_acts)} acts...")
        
        # Try Copy Mode first (Fastest, usually works if encoding is identical)
        cmd_copy = [
            "ffmpeg",
            "-y",               # Overwrite
            "-f", "concat",
            "-safe", "0",
            "-i", filelist_path,
            "-c", "copy",       # Copy stream (no re-encode)
            output_path
        ]
        
        try:
            result = subprocess.run(cmd_copy, capture_output=True, text=True, check=True)
            print(f"   ✅ Stitched Video (Copy Mode): {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Copy Stitch Failed: {e.stderr[:200]}...")
            print("   ⚠️ Falling back to Re-encode Mode (Slower)...")
            
            # Fallback: Re-encode (Reliable but slow)
            # Normalize to 30fps, 720p to be safe
            cmd_encode = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", filelist_path,
                "-c:v", "libx264",
                "-preset", "ultrafast", # Speed over compression
                "-crf", "23",
                "-c:a", "aac",
                output_path
            ]
            
            try:
                subprocess.run(cmd_encode, capture_output=True, text=True, check=True)
                print(f"   ✅ Stitched Video (Re-encode Mode): {output_path}")
                return output_path
            except subprocess.CalledProcessError as e2:
                raise RuntimeError(f"Stitch Failed completely: {e2.stderr}")
