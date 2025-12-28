import ast
import re

class SpatialValidator:
    """
    Statically analyzes Manim code for spatial issues.
    """
    
    @staticmethod
    def validate(code: str) -> dict:
        issues = []
        suggestions = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"valid": False, "issues": [f"Syntax Error: {e}"], "suggestions": []}

        # 1. Check for Hardcoded Coordinates
        for node in ast.walk(tree):
            # looking for lists/tuples [x, y, z]
            if isinstance(node, (ast.List, ast.Tuple)):
                if len(node.elts) == 3 and all(isinstance(e, (ast.Constant, ast.Num, ast.UnaryOp)) for e in node.elts):
                    try:
                        coords = []
                        for e in node.elts:
                            val = SpatialValidator._get_value(e)
                            if val is not None:
                                coords.append(val)
                        
                        if len(coords) == 3:
                            x, y, z = coords
                            if abs(x) > 7.1:
                                issues.append(f"CRITICAL: X-coordinate {x} is OFF-SCREEN (Bounds: ±7.0).")
                            if abs(y) > 4.1:
                                issues.append(f"CRITICAL: Y-coordinate {y} is OFF-SCREEN (Bounds: ±4.0).")
                                
                    except Exception:
                        pass # Complex expression, skip

            # Check calls to move_to, shift with large values
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr'):
                if node.func.attr in ['move_to', 'shift', 'next_to']:
                    # Heuristic check for arguments? 
                    # Simpler to rely on the coordinate list check above which catches [10, 0, 0] passed to these functions.
                    pass

        # 2. Check for Text Wrapping presence
        # Heuristic: If Text() is called with a long string (>50 chars) and no font_size reduction or layout helper
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'Text':
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    text_content = node.args[0].value
                    if isinstance(text_content, str) and len(text_content) > 60:
                        issues.append(f"WARNING: Long text detected ({len(text_content)} chars). Use fit_text() or paragraph.")

        # 3. Check for Layout Helper Usage
        has_helper = "layout_helper" in code
        if not has_helper:
             suggestions.append("Import `layout_helper` for safer positioning.")

        valid = len([i for i in issues if "CRITICAL" in i]) == 0
        
        if not valid:
            suggestions.append("Use smart_position(obj) to auto-fix.")
            
        return {
            "valid": valid,
            "issues": issues,
            "suggestions": suggestions
        }

    @staticmethod
    def _get_value(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num): # Python < 3.8
            return node.n
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            val = SpatialValidator._get_value(node.operand)
            return -val if val is not None else None
        return None
