import unittest
import os
import sys

# Add the track folder to sys.path
track_dir = os.path.abspath("conductor/tracks/readme_improvements_20251221")
if track_dir not in sys.path:
    sys.path.append(track_dir)

from list_dirs import list_project_dirs

class TestListDirs(unittest.TestCase):
    def test_list_dirs_excludes_ignored(self):
        dirs = list_project_dirs()
        # Common ignored directories
        self.assertNotIn(".git", dirs)
        self.assertNotIn("__pycache__", dirs)
        self.assertNotIn(".venv", dirs)
        
        # Root directories that should be included
        self.assertIn("db", dirs)
        self.assertIn("exporter", dirs)
        self.assertIn("tools", dirs)

    def test_list_dirs_returns_relative_paths(self):
        dirs = list_project_dirs()
        for d in dirs:
            self.assertFalse(os.path.isabs(d), f"Path {d} should be relative")

if __name__ == '__main__':
    unittest.main()
