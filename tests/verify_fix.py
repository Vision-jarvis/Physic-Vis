
import os
import shutil
import sys
# Try importing static_ffmpeg
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    print("✅ static_ffmpeg imported and paths added.")
except ImportError:
    print("❌ static_ffmpeg not installed.")

# Check for ffmpeg in PATH
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    print(f"✅ ffmpeg found at: {ffmpeg_path}")
else:
    print("❌ ffmpeg NOT found in PATH.")

# Check for Act 1 Video (scene_8feff308)
act1_dir = r"C:\Users\asus\Desktop\python\Physics Engine\output\media\videos\scene_8feff308\480p15"
video_path = os.path.join(act1_dir, "PhysicsScene.mp4")

if os.path.exists(video_path):
    print(f"✅ Act 1 Video Found: {video_path}")
else:
    print(f"❌ Act 1 Video NOT Found in {act1_dir}")
