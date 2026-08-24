# 3Blue1Brown Source-Accurate Color Palette
# Reference: https://github.com/3b1b/manim/blob/master/manim/utils/color.py

# Reference: https://github.com/3b1b/manim/blob/master/manim/utils/color.py

# Standalone definition to avoid Manim dependency in core graph logic
WHITE = "#FFFFFF"

# Background
DARK_BG = "#1e1e1e" # Standard 3B1B background

# Primary Colors
BLUE_E = "#1C758A"
BLUE_D = "#29ABCA"
BLUE_C = "#58C4DD"
BLUE_B = "#9CDCEB"
BLUE_A = "#C7E9F1"

TEAL_E = "#49A88F"
TEAL_D = "#55C1A7"
TEAL_C = "#5CD0B3"
TEAL_B = "#76DDC0"
TEAL_A = "#ACEAD7"

GREEN_E = "#699C52"
GREEN_D = "#77B05D"
GREEN_C = "#83C167"
GREEN_B = "#A6CF8C"
GREEN_A = "#C9E2AE"

YELLOW_E = "#E8C11C"
YELLOW_D = "#F4D345"
YELLOW_C = "#FFFF00"
YELLOW_B = "#FFEA94"
YELLOW_A = "#FFF1B6"

GOLD_E = "#C78D46"
GOLD_D = "#E1A158"
GOLD_C = "#F0AC5F"
GOLD_B = "#F9B775"
GOLD_A = "#F7C797"

RED_E = "#CF5044"
RED_D = "#E65A4C"
RED_C = "#FC6255"
RED_B = "#FF8080"
RED_A = "#F7A1A3"

MAROON_E = "#94424F"
MAROON_D = "#A24D61"
MAROON_C = "#C55F73"
MAROON_B = "#EC92AB"
MAROON_A = "#FFB3CD"

PURPLE_E = "#644172"
PURPLE_D = "#715582"
PURPLE_C = "#9A72AC"
PURPLE_B = "#B189C6"
PURPLE_A = "#CAA3E8"

GREY_BROWN = "#736357"

# Semantic Mapping (The "Style Guide")
STYLE_MAP = {
    "background": DARK_BG,
    "text": WHITE,
    "variable": BLUE_C,
    "constant": YELLOW_C,
    "vector": RED_C,
    "graph": BLUE_E,
    "geometry": TEAL_C,
    "highlight": YELLOW_D,
    "subtle": GREY_BROWN
}

def get_style_prompt():
    """Returns the CSS/Style rules for the LLM."""
    return f"""
    ### 🎨 3B1B STYLE GUIDELINES (STRICT ENFORCEMENT):
    1. **Background**: Always `config.background_color = "{DARK_BG}"`.
    2. **Text**: White by default. Use `MathTex` for equations.
    3. **Colors**:
       - Variables: {BLUE_C} (BLUE_C)
       - Constants: {YELLOW_C} (YELLOW_C)
       - Vectors: {RED_C} (RED_C)
       - Geometry: {TEAL_C} (TEAL_C)
    4. **Hierarchy**: Use `VGroup` to organize elements.
    """.strip()
