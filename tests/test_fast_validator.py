import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.nodes.fast_validator import fast_validate_node

class TestFastValidator(unittest.TestCase):
    
    def test_valid_code(self):
        code = """
from manim import *
class MyScene(Scene):
    def construct(self):
        self.play(Create(Circle()))
"""
        result = fast_validate_node({"code": code})
        self.assertFalse(result["bypass_render"])

    def test_invalid_syntax(self):
        code = """
class MyScene(Scene)
    def construct(self):
        pass
""" # Missing colon
        result = fast_validate_node({"code": code})
        self.assertTrue(result["bypass_render"])
        self.assertIn("Syntax Error", result["error"])

    def test_missing_scene_class(self):
        code = """
def construct():
    pass
"""
        result = fast_validate_node({"code": code})
        self.assertTrue(result["bypass_render"])
        self.assertIn("No Scene class", result["error"])

    def test_missing_construct(self):
        code = """
from manim import *
class MyScene(Scene):
    def nothing(self):
        pass
"""
        result = fast_validate_node({"code": code})
        self.assertTrue(result["bypass_render"])
        self.assertIn("No construct method", result["error"])

if __name__ == '__main__':
    unittest.main()
