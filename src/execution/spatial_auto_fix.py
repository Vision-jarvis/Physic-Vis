import re
import ast
import astor
from typing import Dict, List, Tuple

MANIM_X_RANGE = (-7.0, 7.0)
MANIM_Y_RANGE = (-4.0, 4.0)

class CoordinateClamper(ast.NodeTransformer):
    """
    Walks the AST and clamps numeric literals inside move_to() / shift()
    calls to safe Manim coordinate ranges.
    """
    SPATIAL_METHODS = {"move_to", "shift", "next_to", "align_to"}
    DEPRECATED = {"set_color_by_gradient", "set_background_stroke", "set_glow", "add_glow_effect"}

    def __init__(self):
        self.fixes_applied = []

    def visit_Call(self, node):
        self.generic_visit(node)  # recurse first

        func_name = self._get_func_name(node)

        if func_name in self.DEPRECATED:
            self.fixes_applied.append(f"Removed deprecated {func_name}")
            return ast.Constant(value="None")  # strip call entirely

        if func_name in self.SPATIAL_METHODS and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.List):
                elts = first_arg.elts
                if len(elts) >= 2:
                    old_x = self._get_value(elts[0])
                    old_y = self._get_value(elts[1])
                    elts[0] = self._clamp_node(elts[0], *MANIM_X_RANGE)
                    elts[1] = self._clamp_node(elts[1], *MANIM_Y_RANGE)
                    
                    new_x = self._get_value(elts[0])
                    new_y = self._get_value(elts[1])
                    if old_x != new_x or old_y != new_y:
                        self.fixes_applied.append(f"Clamped {func_name} coordinates from [{old_x}, {old_y}] to [{new_x}, {new_y}]")
        return node

    def _clamp_node(self, node, lo, hi):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            node.value = max(lo, min(hi, node.value))
        return node
        
    def _get_value(self, node):
        return node.value if isinstance(node, ast.Constant) else "var"

    def _get_func_name(self, node):
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        if isinstance(node.func, ast.Name):
            return node.func.id
        return ""


def apply_spatial_fixes(code: str) -> Tuple[str, List[str]]:
    try:
        tree = ast.parse(code)
        clamper = CoordinateClamper()
        fixed_tree = clamper.visit(tree)
        ast.fix_missing_locations(fixed_tree)
        return astor.to_source(fixed_tree), clamper.fixes_applied
    except SyntaxError:
        # Code is broken — return as-is, let validator catch it
        return code, ["SyntaxError: Unable to parse AST"]


class SpatialAutoFix:
    def fix_code(self, code: str) -> Dict:
        # The scale fix is still useful via regex since it's hard to inject neatly without a deeper AST refactor
        code, scale_fixes = self._add_missing_scales(code)
        
        fixed_code, ast_fixes = apply_spatial_fixes(code)
        
        all_fixes = scale_fixes + ast_fixes
        return {
            'fixed_code': fixed_code,
            'fixes_applied': all_fixes,
            'issues_found': len(all_fixes)
        }
        
    def _add_missing_scales(self, code: str) -> Tuple[str, List[str]]:
        fixes = []
        lines = code.split('\n')
        fixed_lines = []
        for line in lines:
            if any(obj in line for obj in ['Text(', 'MathTex(', 'Tex(']):
                if '.scale(' not in line and 'scale=' not in line:
                    scale = 0.6 if len(line) > 50 else 0.7
                    if '.move_to(' in line:
                        line = line.replace('.move_to(', f'.scale({scale}).move_to(')
                    elif line.strip().endswith(')'):
                        line = line.rstrip() + f'.scale({scale})'
                    fixes.append(f"Added scale={scale} to text")
            fixed_lines.append(line)
        return '\n'.join(fixed_lines), fixes

def auto_fix_spatial_issues(code: str) -> Dict:
    fixer = SpatialAutoFix()
    return fixer.fix_code(code)
