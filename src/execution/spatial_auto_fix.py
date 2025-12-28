import re
import ast
from typing import Dict, List, Tuple

class SpatialAutoFix:
    """
    Acts as a Static Code Validator & Sanitizer.
    Fixes spatial issues, deprecated API usage, and common anti-patterns.
    """
    
    SCREEN_BOUNDS = {'x': (-7, 7), 'y': (-4, 4), 'z': (-5, 5)}
    SAFE_BOUNDS = {'x': (-6, 6), 'y': (-3.5, 3.5), 'z': (-5, 5)}
    
    def __init__(self):
        self.fixes_applied = []
    
    def fix_code(self, code: str) -> Dict:
        """
        Automatically fix all issues in code.
        """
        self.fixes_applied = []
        fixed_code = code
        
        # --- PHASE 1: API & Syntax Fixes ---
        # Fix 0: Camera Frame API (MovingCameraScene vs Scene)
        fixed_code, camera_fixes = self._fix_camera_api(fixed_code)
        self.fixes_applied.extend(camera_fixes)

        # Fix 0.5: Deprecated Methods
        fixed_code, deprecation_fixes = self._fix_deprecated_methods(fixed_code)
        self.fixes_applied.extend(deprecation_fixes)

        # --- PHASE 2: Spatial Fixes ---
        # Fix 1: Replace off-screen move_to() coordinates
        fixed_code, move_to_fixes = self._fix_move_to_coordinates(fixed_code)
        self.fixes_applied.extend(move_to_fixes)
        
        # Fix 2: Add scale to text objects without it
        fixed_code, scale_fixes = self._add_missing_scales(fixed_code)
        self.fixes_applied.extend(scale_fixes)
        
        # Fix 3: Clamp all numeric coordinates
        fixed_code = self._clamp_all_coordinates(fixed_code)
        
        return {
            'fixed_code': fixed_code,
            'fixes_applied': self.fixes_applied,
            'issues_found': len(self.fixes_applied)
        }

    def _fix_camera_api(self, code: str) -> Tuple[str, List[str]]:
        """
        Fixes use of self.camera.frame in non-MovingCameraScene classes.
        """
        fixes = []
        
        # Check if 'MovingCameraScene' is inherited
        is_moving_camera = 'class PhysicsScene(MovingCameraScene):' in code
        
        if not is_moving_camera:
            # Pattern: self.camera.frame.anything
            if 'self.camera.frame' in code:
                # Naive fix: Change class inheritance
                # Better than trying to rewrite the logic to use camera.animate.zoom
                code = code.replace('class PhysicsScene(Scene):', 'class PhysicsScene(MovingCameraScene):')
                fixes.append("Upgraded Scene to MovingCameraScene to support self.camera.frame")
                
            # Pattern: self.camera.animate.set_focal_distance (3D camera issue)
            # ThreeDCamera does not support .animate
            if 'self.camera.animate.set_focal_distance' in code:
                 # Remove .animate
                 code = code.replace('self.camera.animate.set_focal_distance', 'self.camera.set_focal_distance')
                 fixes.append("Removed .animate from ThreeDCamera method")

        return code, fixes

    def _fix_deprecated_methods(self, code: str) -> Tuple[str, List[str]]:
        """
        Removes or replaces deprecated/invalid methods.
        """
        fixes = []
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 1. set_glow() / add_glow_effect() - Not in v0.18 Community
            if '.set_glow(' in line or '.add_glow_effect(' in line:
                # Comment it out
                line = "# " + line + " # [AutoFix] Method not available in v0.18"
                fixes.append("Removed invalid glow effect method")
            
            # 2. numpy rotate (AttributeError: 'numpy.ndarray' object has no attribute 'rotate')
            # Fix: Manim's Rotate is a class, numpy doesn't have .rotate method on array
            if 'np.array' in line and '.rotate(' in line:
                 # Very hard to fix safely with regex, just comment out execution to prevent crash
                 line = "# " + line + " # [AutoFix] numpy arrays do not have .rotate()"
                 fixes.append("Disabled invalid numpy.rotate call")
            
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines), fixes
    
    def _fix_move_to_coordinates(self, code: str) -> Tuple[str, List[str]]:
        """
        Find and fix all move_to() calls with off-screen coordinates.
        """
        fixes = []
        # Pattern: .move_to([x, y, z]) or .move_to([x, y])
        pattern = r'\.move_to\(\[([-\d.]+),\s*([-\d.]+)(?:,\s*([-\d.]+))?\]\)'
        
        def replace_coords(match):
            x, y, z = match.groups()
            x, y = float(x), float(y)
            z = float(z) if z else 0.0
            
            off_screen = (
                x < self.SCREEN_BOUNDS['x'][0] or x > self.SCREEN_BOUNDS['x'][1] or
                y < self.SCREEN_BOUNDS['y'][0] or y > self.SCREEN_BOUNDS['y'][1]
            )
            
            if off_screen:
                new_x = max(self.SAFE_BOUNDS['x'][0], min(x, self.SAFE_BOUNDS['x'][1]))
                new_y = max(self.SAFE_BOUNDS['y'][0], min(y, self.SAFE_BOUNDS['y'][1]))
                fixes.append(f"Clamped coordinates from [{x}, {y}] to [{new_x}, {new_y}]")
                return f'.move_to([{new_x}, {new_y}, {z}])'
            return match.group(0)
        
        fixed_code = re.sub(pattern, replace_coords, code)
        return fixed_code, fixes
    
    def _add_missing_scales(self, code: str) -> Tuple[str, List[str]]:
        """
        Add scale parameter to Text/MathTex objects that don't have one.
        """
        fixes = []
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if any(obj in line for obj in ['Text(', 'MathTex(', 'Tex(']):
                if '.scale(' not in line and 'scale=' not in line:
                    if len(line) > 80: scale = 0.5
                    elif len(line) > 50: scale = 0.6
                    else: scale = 0.7
                    
                    if '.move_to(' in line:
                        line = line.replace('.move_to(', f'.scale({scale}).move_to(')
                    elif line.strip().endswith(')'):
                        line = line.rstrip() + f'.scale({scale})'
                    fixes.append(f"Added scale={scale} to text object")
            fixed_lines.append(line)
        return '\n'.join(fixed_lines), fixes
    
    def _clamp_all_coordinates(self, code: str) -> str:
        """
        Clamp ALL numeric coordinates in the code to safe bounds.
        """
        def clamp_number(match):
            num = float(match.group(0))
            if abs(num) > 10:
                clamped = max(-6, min(num, 6))
                return str(clamped)
            return match.group(0)
        
        pattern = r'\b([-]?\d{2,}\.?\d*)\b'
        lines = code.split('\n')
        fixed_lines = []
        for line in lines:
            if any(method in line for method in ['move_to', 'shift', 'next_to']):
                line = re.sub(pattern, clamp_number, line)
            fixed_lines.append(line)
        return '\n'.join(fixed_lines)

def auto_fix_spatial_issues(code: str) -> Dict:
    """
    Convenience function for workflow integration.
    """
    fixer = SpatialAutoFix()
    return fixer.fix_code(code)
