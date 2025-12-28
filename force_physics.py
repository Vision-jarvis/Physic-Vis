import os
from manim import *

# --- THE FIX: Manually add the paths to Python's environment ---
# This tells Python exactly where to look, ignoring Windows settings.

# 1. Add the MiKTeX path you found in your screenshot:
miktex_path = r"C:\Users\asus\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ["PATH"] += os.pathsep + miktex_path

# 2. (Optional) If you know where your FFmpeg 'bin' folder is, paste it below:
# ffmpeg_path = r"C:\ffmpeg\bin" 
# os.environ["PATH"] += os.pathsep + ffmpeg_path

# ---------------------------------------------------------

class PhysicsScene(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES)
        
        # 1. Setup Axes (Using Text to avoid LaTeX errors)
        axes = ThreeDAxes(
            x_range=[-4, 4, 1], y_range=[-4, 4, 1], z_range=[0, 4, 1],
            x_length=8, y_length=8, z_length=4
        ).add_coordinates()
        
        labels = axes.get_axis_labels(
            x_label=Text("x").scale(0.5), 
            y_label=Text("y").scale(0.5), 
            z_label=Text("Energy").scale(0.5)
        )

        self.play(Create(axes), Write(labels))

        # 2. Create Potential Surface
        def potential_func(x, y):
            return 0.25 * (x**2 + y**2)

        surface = Surface(
            lambda u, v: axes.c2p(u, v, potential_func(u, v)),
            u_range=[-3, 3], v_range=[-3, 3], resolution=(20, 20),
        )
        surface.set_style(fill_opacity=0.6, stroke_color=BLUE_A, stroke_width=0.5)
        surface.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.6)
        
        self.play(Create(surface))
        self.wait(2)

        # 3. Drop a Particle
        particle = Sphere(radius=0.15, color=YELLOW)
        particle.move_to(axes.c2p(2.5, 2.5, potential_func(2.5, 2.5)))
        self.add(particle)
        
        # Simple fall animation
        self.play(particle.animate.move_to(axes.c2p(0, 0, 0)), run_time=2, rate_func=there_and_back)
        self.wait(1)