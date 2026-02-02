import unittest
import os
import shutil
from conductor.tracks.readme_improvements_20251221.generate_readme_draft import (
    generate_draft,
)


class TestGenerateDraft(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_gen_test"
        os.makedirs(self.test_dir, exist_ok=True)
        # Create some dummy files
        with open(os.path.join(self.test_dir, "script.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(self.test_dir, "data.txt"), "w") as f:
            f.write("data")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_draft_creation(self):
        readme_path = os.path.join(self.test_dir, "README.md")
        generate_draft(self.test_dir)

        self.assertTrue(os.path.exists(readme_path))

        with open(readme_path, "r") as f:
            content = f.read()

        self.assertIn("# temp_gen_test", content)
        self.assertIn("## Purpose/Overview", content)
        self.assertIn("## Key Components", content)
        # Check if it listed the script
        self.assertIn("- **script.py**", content)


if __name__ == "__main__":
    unittest.main()
