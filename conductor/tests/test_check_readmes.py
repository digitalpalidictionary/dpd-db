import unittest
import os
import sys

# Add the track folder to sys.path
track_dir = os.path.abspath("conductor/tracks/readme_improvements_20251221")
if track_dir not in sys.path:
    sys.path.append(track_dir)

from check_readmes import check_readme_compliance


class TestCheckReadmes(unittest.TestCase):
    def setUp(self):
        # Create a dummy directory with a valid README
        os.makedirs("temp_test_dir/valid", exist_ok=True)
        with open("temp_test_dir/valid/README.md", "w") as f:
            f.write(
                "# Valid\n## Purpose/Overview\n## Key Components\n## Relationships\n## Usage/Commands\n"
            )

        # Create a dummy directory with an invalid README
        os.makedirs("temp_test_dir/invalid", exist_ok=True)
        with open("temp_test_dir/invalid/README.md", "w") as f:
            f.write("# Invalid\n")

        # Create a dummy directory with no README
        os.makedirs("temp_test_dir/none", exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree("temp_test_dir")

    def test_compliance_checker(self):
        results = check_readme_compliance("temp_test_dir")

        # Valid should pass
        self.assertTrue(results["temp_test_dir/valid"]["exists"])
        self.assertTrue(results["temp_test_dir/valid"]["compliant"])

        # Invalid should exist but not be compliant
        self.assertTrue(results["temp_test_dir/invalid"]["exists"])
        self.assertFalse(results["temp_test_dir/invalid"]["compliant"])

        # None should not exist
        self.assertFalse(results["temp_test_dir/none"]["exists"])


if __name__ == "__main__":
    unittest.main()
