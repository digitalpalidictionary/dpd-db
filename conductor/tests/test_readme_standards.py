import unittest
import os


class TestReadmeStandards(unittest.TestCase):
    def test_template_exists(self):
        self.assertTrue(
            os.path.exists("conductor/templates/DIR_README_TEMPLATE.md"),
            "Template file does not exist",
        )

    def test_template_content(self):
        if not os.path.exists("conductor/templates/DIR_README_TEMPLATE.md"):
            return  # test_template_exists will handle failure

        with open("conductor/templates/DIR_README_TEMPLATE.md", "r") as f:
            content = f.read()

        self.assertIn("## Purpose/Overview", content)
        self.assertIn("## Key Components", content)
        self.assertIn("## Relationships", content)
        self.assertIn("## Usage/Commands", content)


if __name__ == "__main__":
    unittest.main()
