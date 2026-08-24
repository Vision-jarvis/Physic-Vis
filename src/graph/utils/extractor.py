from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.llm import get_llm
import json

# Use Flash for speed
llm = get_llm(model_type="flash")

extractor_prompt = ChatPromptTemplate.from_template("""
You are a Manim Translation Engine.
Map the user's description to specific Manim Class names (v0.19.0+).

User Description: {plan}

RULES:
1. Identify visual objects (e.g., "Ball" -> `Circle`, "Equation" -> `MathTex`, "Graph" -> `Axes`, "Text" -> `Text`).
2. Identify animations (e.g., "Fade in" -> `FadeIn`, "Draw" -> `Create`, "Morph" -> `ReplacementTransform`, "Wait" -> `Wait`, "Write" -> `Write`).
3. Return ONLY a JSON list of strings.

Example:
Input: "A square turns into a circle while text appears."
Output: ["Square", "Circle", "ReplacementTransform", "Text", "Write"]

JSON Output:
""")

def extract_manim_keywords(plan_text: str):
    """
    Returns a list of likely Manim class names from a natural language plan.
    """
    chain = extractor_prompt | llm | JsonOutputParser()
    try:
        keywords = chain.invoke({"plan": plan_text})
        # Deduplicate and clean
        if isinstance(keywords, list):
             return list(set(k.strip() for k in keywords if isinstance(k, str)))
        return []
    except Exception as e:
        print(f"⚠️ Extraction failed: {e}")
        return []
