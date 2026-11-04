import json
from functools import cache
from pathlib import Path

from icecream import ic

HELP_PATH: Path = Path("gui2/field_help.json")
MAX_HELP_LENGTH: int = 300


def load_help_file(path: Path) -> dict[str, str]:
    """Read the help texts, or return {} so the form still opens."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    # ValueError covers both JSONDecodeError and UnicodeDecodeError.
    except (OSError, ValueError) as error:
        ic("field help not loaded", path, error)
        return {}

    if not isinstance(data, dict) or not all(
        isinstance(value, str) for value in data.values()
    ):
        ic("field help not loaded: expected an object of strings", path)
        return {}
    return data


def validate_field_help(help_texts: dict[str, object], names: list[str]) -> list[str]:
    """One message per problem. An empty list means the texts are good."""
    problems: list[str] = []
    for name in names:
        if name not in help_texts:
            problems.append(f"{name}: no help text")
    for key, value in help_texts.items():
        if key not in names:
            problems.append(f"{key}: not a field name")
        if not isinstance(value, str):
            problems.append(f"{key}: text is not a string")
        elif not value.strip():
            problems.append(f"{key}: text is empty")
        elif len(value) > MAX_HELP_LENGTH:
            problems.append(f"{key}: text is {len(value)} characters, over the limit")
    return problems


# The form is rebuilt on every clear, so the file is read once per process.
@cache
def _cached_help() -> dict[str, str]:
    return load_help_file(HELP_PATH)


def get_field_help(name: str) -> str | None:
    return _cached_help().get(name)
