"""Read the local GoldenDict directory from config.ini, prompting for it
if not yet configured. Used by goldendict_exporter to copy zips into place."""

from pathlib import Path
from rich import print
from rich.prompt import Prompt


from tools.configger import config_test, config_test_option, config_update, config_read


def make_goldendict_path() -> Path | None:
    """Add a Goldendict path if one doesn't exist,
    or return the path if it does."""

    if config_test("goldendict", "copy_unzip", "yes"):
        if not config_test_option("goldendict", "path"):
            goldendict_path = Prompt.ask(
                "[yellow]Enter your GoldenDict directory (or ENTER for None)"
            )
            config_update("goldendict", "path", goldendict_path)
            return Path(goldendict_path)
        else:
            path = config_read("goldendict", "path")
            return Path(path) if path else None
    return None


if __name__ == "__main__":
    print(make_goldendict_path())
