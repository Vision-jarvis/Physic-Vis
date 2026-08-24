def extract_text_content(response) -> str:
    """
    Safely extract string content from any LangChain/LLM response.
    Handles: str, list of dicts, list of AIMessageChunk, AIMessage objects.
    """
    content = response.content if hasattr(response, 'content') else response

    # Already a string — fast path
    if isinstance(content, str):
        return content.strip()

    # List of content blocks (Gemini tool-use format)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()

    # Fallback — coerce to string
    return str(content).strip()


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM-generated code."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        lines = lines[:-1] if lines[-1].strip() == "```" else lines
        return "\n".join(lines).strip()
    return text
