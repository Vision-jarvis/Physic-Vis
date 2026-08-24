from typing import Dict, List
import subprocess
import os
from src.core.config import settings
from concurrent.futures import ThreadPoolExecutor

class ParallelRenderer:
    """Render multiple scenes simultaneously."""
    
    def __init__(self, max_parallel: int = 5):
        """
        Args:
            max_parallel: Max concurrent renders (limited by GPU memory)
        """
        self.max_parallel = max_parallel
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
        except ImportError:
            print("Warning: static_ffmpeg not found in ParallelRenderer environment")
    
    def render_all_scenes(self, scene_codes: Dict[str, str]) -> Dict[str, Dict]:
        """
        Render all scenes in parallel.
        
        Returns:
            {"HookScene": {"success": True, "render_output_path": "..."}, ...}
        """
        results = {}
        
        # Write all code files first
        code_files = {}
        for scene_name, code in scene_codes.items():
            code_path = os.path.join(settings.output_dir, f"{scene_name}.py")
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(code)
            code_files[scene_name] = code_path
        
        # Render in batches of max_parallel
        scene_names = list(scene_codes.keys())
        
        # We can use ThreadPoolExecutor to manage the subprocesses
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            future_to_scene = {
                executor.submit(self._render_single, scene_name, code_files[scene_name]): scene_name
                for scene_name in scene_names
            }
            
            for future in future_to_scene:
                scene_name = future_to_scene[future]
                try:
                    result = future.result()
                    results[scene_name] = result
                    if result["success"]:
                        print(f"  ✓ {scene_name} rendered")
                    else:
                        print(f"  ✗ {scene_name} failed: {result.get('error')}")
                except Exception as exc:
                    results[scene_name] = {"success": False, "error": str(exc)}
                    print(f"  ✗ {scene_name} generated an exception: {exc}")
        
        return results

    def _render_single(self, scene_name: str, code_path: str) -> Dict:
        """Render a single scene using subprocess."""
        # Using the same command structure as local_runner but simplified
        # Assuming 'manim' is in path or using docker command
        
        # For this environment, we use local manim command as per previous logs
        # or docker if configured. Let's assume local 'manim' command for now based on 'test_multi_act.py' usage
        # which uses 'manim -ql ...' locally.
        
        # NOTE: Using -ql (Low Quality) for speed during dev/optimization phase
        # Can be parameterized later.
        media_dir = os.path.join(settings.output_dir, "media")
        cmd = [
            "manim", 
            "-qh", 
            code_path, 
            scene_name, 
            "--media_dir", media_dir  # Explicit media dir helps finding output
        ]
        
        try:
            # Run with timeout to prevent hangs
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300 # 5 minutes max per scene for high quality
            )
            
            if proc.returncode == 0:
                # Find video file logic
                # Default manim structure: media/videos/{scene_py_name}/480p15/{SceneName}.mp4
                # We need to reconstruct where it went.
                # Since we passed code_path like output/HookScene.py, module name is HookScene
                module_name = os.path.splitext(os.path.basename(code_path))[0]
                video_dir = os.path.join(
                    media_dir, "videos", module_name, "1080p60"
                )
                
                # Search for mp4
                if os.path.exists(video_dir):
                    videos = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
                    if videos:
                        return {
                            "success": True,
                            "render_output_path": os.path.join(video_dir, videos[0])
                        }
                return {"success": False, "error": "Video file not found after successful render"}
            else:
                return {
                    "success": False, 
                    "error": proc.stderr if proc.stderr else proc.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Render timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
