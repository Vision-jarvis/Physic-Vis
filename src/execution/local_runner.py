import subprocess
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

class ManimExecutor:
    """
    Executes the generated Manim code inside a local Docker container.
    Replaces LocalDockerRunner with robust UTF-8 handling.
    """
    def __init__(self, image_name: str = "manim-renderer:v0.18", output_dir: str = "output", timeout: int = 180):
        self.output_dir = Path(output_dir).resolve()
        self.timeout = timeout
        self.container_name = image_name
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_code(self, code: str) -> Tuple[str, str, Optional[str]]:
        """
        Backward-compatible run_code method for the workflow.
        Returns: (status, logs, video_path)
        """
        # 1. Write code to a file
        import uuid
        run_id = str(uuid.uuid4())[:8]
        filename = f"scene_{run_id}.py"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
            
        print(f"--- EXECUTOR: Writing code to {filepath} ---")

        # 1.5 DEPLOY LAYOUT HELPER (Preserved from old runner)
        import shutil
        source_helper = Path("src/execution/layout_helper.py").resolve()
        dest_helper = self.output_dir / "layout_helper.py"
        if source_helper.exists():
            shutil.copy(source_helper, dest_helper)
            
        # 2. Execute
        result = self.execute(filename, "PhysicsScene")
        
        # 3. Format Output for Workflow
        status = "SUCCESS" if result['success'] else "FAILURE"
        logs = result['stdout'] + "\n" + result['stderr']
        video_path = result['video_path']
        
        return status, logs, video_path

    def execute(self, scene_file: str, scene_name: str = "PhysicsScene") -> Dict:
        """
        Execute Manim code in Docker with proper UTF-8 handling.
        """
        # Build Docker command
        # Build command with explicit 'manim' executable
        cmd = [
            "docker", "run",
            "--rm",
            "--stop-timeout", "10",
            "-v", f"{self.output_dir}:/app",
            self.container_name,
            "manim",  # Explicitly call manim
            "-qm",
            f"/app/{scene_file}", # Start with /app/ to avoid path issues
            scene_name
        ]
        
        print(f"--- EXECUTOR: Running Command: {cmd} ---")

        # CRITICAL FIX: Force UTF-8 everywhere
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'  # PEP 540 - Force UTF-8 mode
        
        # Windows-specific: Set console code page
        if sys.platform == 'win32':
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
        
        try:
            # THE FIX: Use encoding='utf-8' AND errors='replace'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',        # ← Force UTF-8 decoding
                errors='replace',        # ← Replace invalid chars with 
                timeout=self.timeout,
                env=env,
                cwd=str(self.output_dir)
            )
            
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
            
            # Check for success
            if exit_code == 0:
                # Find the video file
                video_path = self._find_video_file(scene_file, scene_name)
                
                if video_path:
                    return {
                        'success': True,
                        'stdout': stdout,
                        'stderr': stderr,
                        'exit_code': 0,
                        'video_path': str(video_path),
                        'error_type': None
                    }
                else:
                    return {
                        'success': False,
                        'stdout': stdout,
                        'stderr': stderr + "\nVideo file not found despite exit code 0",
                        'exit_code': 1,
                        'video_path': None,
                        'error_type': 'missing_output'
                    }
            else:
                # Execution failed
                error_type = self._classify_error(stderr, exit_code)
                return {
                    'success': False,
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': exit_code,
                    'video_path': None,
                    'error_type': error_type
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Rendering timed out after {self.timeout} seconds',
                'exit_code': 124,
                'video_path': None,
                'error_type': 'timeout'
            }
        
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Executor error: {str(e)}',
                'exit_code': 1,
                'video_path': None,
                'error_type': 'executor_error'
            }
    
    def _find_video_file(self, scene_file: str, scene_name: str) -> Optional[Path]:
        """
        Locate the rendered video file.
        Manim outputs to: media/videos/{scene_file_without_ext}/720p30/{scene_name}.mp4
        """
        scene_id = Path(scene_file).stem
        
        # Expected path
        video_path = self.output_dir / "media" / "videos" / scene_id / "720p30" / f"{scene_name}.mp4"
        
        if video_path.exists():
            return video_path
        
        # Fallback: Search for any .mp4 in the scene folder
        search_dir = self.output_dir / "media" / "videos" / scene_id
        if search_dir.exists():
            for mp4_file in search_dir.rglob("*.mp4"):
                if "partial_movie_files" not in str(mp4_file):
                    return mp4_file
        
        return None
    
    def _classify_error(self, stderr: str, exit_code: int) -> str:
        """
        Classify error type for smart routing.
        """
        stderr_lower = stderr.lower()
        
        # Timeout
        if exit_code == 124:
            return 'timeout'
        
        # LaTeX errors
        if 'latex error' in stderr_lower or 'undefined control sequence' in stderr_lower:
            return 'latex_error'
        
        # Python syntax errors
        if 'syntaxerror' in stderr_lower:
            return 'syntax_error'
        
        # Attribute errors (wrong method names)
        if 'attributeerror' in stderr_lower:
            return 'attribute_error'
        
        # Import errors
        if 'importerror' in stderr_lower or 'modulenotfounderror' in stderr_lower:
            return 'import_error'
        
        # Memory issues
        if 'memoryerror' in stderr_lower or 'killed' in stderr_lower:
            return 'memory_error'
        
        # Docker Daemon Crash
        if 'internal server error' in stderr_lower or 'docker: request returned' in stderr_lower:
            return 'docker_daemon_error'
            
        # Partial render (started but crashed)
        if 'partial movie file' in stderr_lower:
            return 'partial_render'
        
        # Generic crash
        if 'traceback' in stderr_lower:
            return 'runtime_error'
        
        return 'unknown'

# For backward compatibility if needed, though we should update imports
LocalDockerRunner = ManimExecutor
