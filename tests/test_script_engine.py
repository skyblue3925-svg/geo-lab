
import sys
import os
import unittest
import numpy as np

# Add path
sys.path.insert(0, os.getcwd())

from engine.grid import WorldGrid
from engine.script_engine import ScriptExecutor

class TestScriptEngine(unittest.TestCase):
    def setUp(self):
        self.grid = WorldGrid(10, 10, 10.0)
        self.engine = ScriptExecutor(self.grid)

    def test_basic_arithmetic(self):
        # Script that modifies bedrock
        script = """
bedrock += 5.0
"""
        success, msg = self.engine.execute(script)
        self.assertTrue(success, msg)
        self.assertEqual(self.grid.bedrock[0,0], 5.0, "Bedrock modification failed")

    def test_numpy_usage(self):
        # Script using numpy
        script = """
bedrock[:] = np.ones((10,10)) * 10.0
"""
        success, msg = self.engine.execute(script)
        self.assertTrue(success, msg)
        self.assertEqual(self.grid.bedrock[5,5], 10.0)

    def test_security_check(self):
        # Script with forbidden import
        script = """
import os
os.system('echo hacked')
"""
        with self.assertRaises(ValueError) as cm:
            self.engine.execute(script)
        self.assertIn("보안 경고", str(cm.exception))

    def test_elevation_sync(self):
        # Modifying bedrock should update elevation after execution
        script = "bedrock += 2.0"
        self.engine.execute(script)
        self.assertEqual(self.grid.elevation[0,0], 2.0, "Elevation check failed (assuming sediment=0)")

if __name__ == '__main__':
    # unittest.main()
    import sys
    with open('test_result.txt', 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        unittest.main(testRunner=runner, exit=False)
