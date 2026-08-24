import re
import ast
import json

def extract_code_block(content: str) -> str:
    """
    Extracts the first Python code block from the string.
    If no block is found, returns the raw content (cleaned).
    """
    # 1. Look for specific language blocks first (Cleaner)
    for lang in ["python", "json", "bash"]:
        match = re.search(f"```{lang}(.*?)```", content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 2. Look for generic ``` ... ```
    match = re.search(r"```(.*?)```", content, re.DOTALL)
    if match:
        block = match.group(1).strip()
        # Heuristic: Remove language tag if it was captured in the generic group
        # e.g. "json\n{...}" -> "{...}"
        first_line_end = block.find('\n')
        if first_line_end != -1:
            first_line = block[:first_line_end].lower().strip()
            if first_line in ["python", "json", "bash", "html", "css"]:
                return block[first_line_end:].strip()
        return block
        
    # 3. Fallback: Return as is (assuming it's just code)
    return content.strip()

def extract_text_from_response(content):
    """
    Robustly extracts text from LangChain/Gemini response content.
    Handles:
    1. Plain string.
    2. List of strings (Gemini multi-part).
    3. List of dictionaries (Gemini structured text).
    4. Stringified dictionaries (fallback).
    """
    print(f"DEBUG: Extracting text from type: {type(content)}")
    
    # Case 1: List (Common with Gemini 3.0 / Flash)
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                # Extract 'text' key if present
                if 'text' in part:
                    text_parts.append(part['text'])
                else:
                    text_parts.append(str(part)) # Fallback
            else:
                text_parts.append(str(part))
        return "".join(text_parts)
        
    # Case 2: String (Normal)
    if isinstance(content, str):
        # Check if it looks like a stringified dict/list (from previous bad joins or weird LLM output)
        cleaned = content.strip()
        if (cleaned.startswith("{") and "type" in cleaned and "text" in cleaned) or \
           (cleaned.startswith("[") and "{'type':" in cleaned):
            try:
                # Try to parse it back
                try:
                    parsed = json.loads(cleaned)
                except:
                    parsed = ast.literal_eval(cleaned)
                
                return extract_text_from_response(parsed) # Recurse
            except:
                pass # Just return the string if parsing fails
                
        return content

    # Case 3: Dict (Direct object)
    if isinstance(content, dict):
         return content.get("text", str(content))
         
    return str(content)

def repair_json(json_str: str) -> str:
    """
    Attempts to repair common JSON errors from LLMs.
    1. Escapes backslashes in LaTeX strings (e.g. \frac -> \\frac)
    """
    if not json_str: return "{}"
    
    # naive pass: find backslashes that are NOT escaped
    # But this is hard with regex. 
    # Simpler: use the 'dirty-json' approach or just try to be lenient with newlines.
    
    # Fix: "key": "value \text{...}" -> "key": "value \\text{...}"
    # We look for \ followed by non-control chars that isn't already escaped.
    # This is risky. 
    
    # Actually, simpler usage:
    # 1. Strip Common Markdown garbage
    # Smart fix for LaTeX backslashes:
    # We want to turn "\alpha" into "\\alpha", but leave "\n", "\"", "\\" alone.
    # Regex: backslash not followed by valid escape char.
    # Valid JSON escapes: " \ / b f n r t u
    
    # 1. Strip common markdown
    clean = json_str.strip()
    
    # 2. Escape invalid backslashes
    # Pattern: \ followed by something that IS NOT [" \ / b f n r t u]
    # We use negative lookahead.
    # However, Python regex and JSON escaping is tricky.
    # Let's try a specific fix for LaTeX-like patterns: \ + letter
    # But exclude \n, \r, \t, \b, \f, \u
    
    def escape_latex(match):
        char = match.group(1)
        if char in '"\\/bfnrtu':
            return "\\" + char # Keep existing escape
        return "\\\\" + char # Escape the backslash
        
    cleaned = re.sub(r'\\(.)', escape_latex, clean)
    return cleaned

