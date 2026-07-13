#!/usr/bin/env python3

"""Find sandhi contraction errors in speech_marks.json.

A clean word with more than one apostrophe-containing contraction
variant has inconsistent apostrophe placement, e.g. aham'pi / ahamp'i,
n'eva / ne'va. The fix is editing the 's in the db.
"""

import json

import pyperclip
from rich import print

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager


def load_exceptions(pth: ProjectPaths) -> list[str]:
    """Load the clean words with legitimate multiple contractions."""
    with open(pth.sandhi_errors_exceptions_path, encoding="utf-8") as f:
        return json.load(f)


def save_exceptions(pth: ProjectPaths, exceptions: list[str]) -> None:
    """Save the exceptions list."""
    with open(pth.sandhi_errors_exceptions_path, "w", encoding="utf-8") as f:
        json.dump(exceptions, f, ensure_ascii=False, indent=2)


def find_sandhi_errors(
    speech_marks: dict[str, list[str]],
    exceptions: list[str],
) -> dict[str, list[str]]:
    """Find clean words whose contraction variants disagree on apostrophe
    placement. Variants differing only by hyphens are not errors."""

    flagged: dict[str, list[str]] = {}
    for key, values in speech_marks.items():
        contractions = [v for v in values if "'" in v]
        if (
            len(contractions) > 1
            and key not in exceptions
            and len({c.replace("-", "") for c in contractions}) > 1
        ):
            flagged[key] = contractions
    return flagged


def prompt_errors(
    pth: ProjectPaths,
    exceptions: list[str],
    flagged: dict[str, list[str]],
) -> None:
    """Show each flagged word and its variants, clean word on the clipboard."""

    for counter, (key, contractions) in enumerate(flagged.items(), start=1):
        print()
        print(f"{counter:>4} / {len(flagged):<4}[cyan]{key}")
        for contraction in contractions:
            print(f"{'':<11}{contraction}")
        pyperclip.copy(key)
        print(
            "[yellow]e[white]xception, [yellow]q[white]uit or Enter to continue: ",
            end="",
        )
        choice = input()
        if choice == "e":
            exceptions.append(key)
            save_exceptions(pth, exceptions)
        elif choice == "q":
            break


def main() -> None:
    """Find and review inconsistent sandhi contractions in speech_marks.json."""
    pr.yellow_title("test sandhi contraction errors")
    pth = ProjectPaths()
    exceptions = load_exceptions(pth)

    pr.green_tmr("regenerating speech marks from db")
    manager = SpeechMarkManager()
    manager.regenerate_from_db()
    speech_marks = manager.get_speech_marks()
    pr.yes(len(speech_marks))

    flagged = find_sandhi_errors(speech_marks, exceptions)
    pr.green_title(f"found {len(flagged)} words with inconsistent contractions")
    prompt_errors(pth, exceptions, flagged)


if __name__ == "__main__":
    main()
