from src.graph.state import AgentState
import ast

def fast_validate_node(state: AgentState):
    """
    Fast AST-based validation of generated code.
    Fails fast before expensive Docker execution.
    """
    print("--- NODE: Fast Validator (AST) ---")
    code = state.get("code", "")
    
    if not code:
        return {"error": "No code generated", "bypass_render": True}
        
    try:
        # 1. Syntax Check
        tree = ast.parse(code)
        
        # 2. Key Component Check
        has_scene = False
        has_construct = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check inheritance (rough heuristic)
                for base in node.bases:
                    if isinstance(base, ast.Name) and "Scene" in base.id:
                        has_scene = True
                
                # Check for construct method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "construct":
                        has_construct = True
                        
        if not has_scene:
            return {"error": "No Scene class defined", "bypass_render": True}
            
        if not has_construct:
            return {"error": "No construct method found", "bypass_render": True}
            
        print("   ✅ AST Validation Passed.")
        return {"bypass_render": False}
        
    except SyntaxError as e:
        print(f"   ❌ Syntax Error detected: {e}")
        return {"error": f"Syntax Error: {e}", "bypass_render": True}
    except Exception as e:
        print(f"   ⚠️ Validation Error: {e}")
        return {"error": f"Validation Error: {e}", "bypass_render": True}
