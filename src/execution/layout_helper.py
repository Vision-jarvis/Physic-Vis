from manim import *

# Standard 16:9 Frame Boundaries (with padding)
# Manim's default frame height is 8.0, width is 14.22
FRAME_WIDTH = 13.5  # Slightly less than 14.22 for safety
FRAME_HEIGHT = 7.5  # Slightly less than 8.0 for safety

def smart_position(mobject, direction=ORIGIN, buff=0.5):
    """
    Ensures an object stays inside the camera frame.
    Usage: smart_position(my_text)
    """
    # 1. Auto-Scale if too big
    if mobject.width > FRAME_WIDTH:
        mobject.scale_to_fit_width(FRAME_WIDTH)
    if mobject.height > FRAME_HEIGHT:
        mobject.scale_to_fit_height(FRAME_HEIGHT)
    
    # 2. Check strict bounds
    # If the object's edge is outside bounds, pull it back.
    
    # Right edge
    if mobject.get_right()[0] > FRAME_WIDTH / 2:
        mobject.to_edge(RIGHT, buff=buff)
    # Left edge
    if mobject.get_left()[0] < -FRAME_WIDTH / 2:
        mobject.to_edge(LEFT, buff=buff)
    # Top edge
    if mobject.get_top()[1] > FRAME_HEIGHT / 2:
        mobject.to_edge(UP, buff=buff)
    # Bottom edge
    if mobject.get_bottom()[1] < -FRAME_HEIGHT / 2:
        mobject.to_edge(DOWN, buff=buff)
        
    return mobject

def fit_text(text_str, max_width=12, font_size=24, **kwargs):
    """
    Creates a Text object that automatically wraps.
    Usage: title = fit_text("Long title...", font_size=36)
    """
    # Paragraph class in Manim handles wrapping automatically? 
    # Actually Paragraph expects separate strings for lines.
    # We can use Tex with parbox for robust wrapping.
    
    # Option A: Use Tex with parbox (Robust for math + text)
    # Convert pixels/units rough estimate: 1 unit ~ 100 pixels?
    # 12 units -> ~12cm in LaTeX parbox logic roughly.
    
    return Tex(
        f"\\parbox{{{max_width}cm}}{{{text_str}}}", 
        font_size=font_size,
        **kwargs
    )

def safe_vgroup(objects, direction=DOWN, buff=0.3):
    """
    Groups objects and ensures they don't overflow screen.
    """
    group = VGroup(*objects).arrange(direction, buff=buff)
    smart_position(group)
    return group
