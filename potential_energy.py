from manim import *
import numpy as np

class PotentialEnergyField(ThreeDScene):
    def construct(self):
        # --- Configuration ---
        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES)
        
        # Define the Potential Function V(x, y)
        # Using a simple harmonic oscillator well: V = 0.5 * (x^2 + y^2)
        def potential_func(x, y):
            return 0.25 * (x**2 + y**2)

        # Define the Force (Negative Gradient) F = - grad(V)
        # Fx = -dV/dx = -0.5*x, Fy = -dV/dy = -0.5*y
        def force_func(pos):
            x, y = pos[0], pos[1]
            return np.array([-0.5 * x, -0.5 * y, 0])

        # --- 1. Setup Axes ---
        axes = ThreeDAxes(
            x_range=[-4, 4, 1],
            y_range=[-4, 4, 1],
            z_range=[0, 4, 1],
            x_length=8,
            y_length=8,
            z_length=4
        ).add_coordinates()
        
        labels = axes.get_axis_labels(
            x_label=MathTex("x"), 
            y_label=MathTex("y"), 
            z_label=MathTex("V(x,y)")
        )

        self.play(Create(axes), Write(labels))
        self.wait(1)

        # --- 2. Create the Scalar Field (Surface) ---
        surface = Surface(
            lambda u, v: axes.c2p(u, v, potential_func(u, v)),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(30, 30),
            should_make_jagged=False
        )
        
        surface.set_style(fill_opacity=0.6, stroke_color=BLUE_A, stroke_width=0.5)
        surface.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.6)

        title_text = MathTex(r"V(\vec{r}) = \text{Scalar Field}").to_corner(UL)
        self.add_fixed_in_frame_mobjects(title_text)
        
        self.play(Create(surface), Write(title_text))
        self.begin_ambient_camera_rotation(rate=0.1)
        self.wait(2)

        # --- 3. Create the Force Vector Field (-Grad V) ---
        # We project these onto the XY plane (z=0) to show the "push"
        vector_field = ArrowVectorField(
            force_func,
            x_range=[-3, 3],
            y_range=[-3, 3],
            length_func=lambda x: x * 0.5,  # Scale arrows for visibility
            colors=[RED_A, RED_D]
        )
        
        force_text = MathTex(r"\vec{F} = -\nabla V").next_to(title_text, DOWN)
        self.add_fixed_in_frame_mobjects(force_text)

        self.play(Create(vector_field), Write(force_text))
        self.wait(2)

        # --- 4. Particle Physics Simulation ---
        # Initial conditions
        x0, y0 = 2.5, 2.5
        particle = Sphere(radius=0.15, color=YELLOW)
        particle.move_to(axes.c2p(x0, y0, potential_func(x0, y0)))
        
        # Trail to visualize the path
        trail = TracedPath(particle.get_center, stroke_color=YELLOW, stroke_width=2, dissipating_time=1)
        self.add(particle, trail)

        # Physics variables
        velocity = np.array([0.0, 0.0, 0.0])
        dt = 1 / 60  # Simulation time step

        # Updater function for the particle
        def update_particle(mob, dt):
            nonlocal velocity, x0, y0
            
            # 1. Calculate Force (Acceleration, assuming m=1) based on current 2D pos
            # We look at the position on the XY plane to determine force
            force = force_func([x0, y0, 0])
            
            # 2. Update Velocity (Euler integration)
            # Adding a bit of friction (damping) so it settles at the bottom
            friction = -0.5 * velocity 
            acceleration = force + friction
            velocity += acceleration * dt
            
            # 3. Update Position
            x0 += velocity[0] * dt
            y0 += velocity[1] * dt
            
            # 4. Snap visual sphere to the surface height at new (x, y)
            z_val = potential_func(x0, y0)
            mob.move_to(axes.c2p(x0, y0, z_val))

        particle.add_updater(update_particle)
        
        self.wait(6) # Let the simulation run
        
        particle.remove_updater(update_particle)
        self.stop_ambient_camera_rotation()
        self.wait(1)