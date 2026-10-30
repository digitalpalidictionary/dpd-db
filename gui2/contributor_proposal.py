"""Which of a contributor's fields Pass2Add fills into the proposal (_add) side."""

from typing import Literal


def proposal_fields(
    entry: dict, kind: Literal["addition", "correction"]
) -> dict[str, str | int]:
    """The fields of a contributor entry to show as proposals.

    An addition gets no id proposal: the word takes the next real id on save.
    A correction with `_changed` shows only the columns the contributor
    changed. An older correction without it shows every field."""
    if kind == "addition":
        return {k: v for k, v in entry.items() if k != "id"}
    changed = entry.get("_changed")
    if changed is None:
        return dict(entry)
    return {k: v for k, v in entry.items() if k in changed}
