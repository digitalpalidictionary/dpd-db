"""History load in Pass1Add must clear suggestions but keep the helper flags."""

from types import SimpleNamespace

import pytest

from gui2.dpd_fields_flags import Flags
from gui2.pass1_add_view import Pass1AddView

FIELD_NAMES = ["lemma_1", "lemma_2", "stem", "pattern"]


class FakeDpdFields:
    """Mirrors the parts of DpdFields the history handler touches."""

    def __init__(self) -> None:
        self.field_configs = [SimpleNamespace(name=name) for name in FIELD_NAMES]
        self.fields = {name: SimpleNamespace(value=None) for name in FIELD_NAMES}
        for name in FIELD_NAMES:
            self.fields[f"{name}_add"] = SimpleNamespace(value=f"ai {name}")
        self.flags = Flags()

    def update_add_fields(self, data: dict[str, str]) -> None:
        for name, value in data.items():
            self.fields[f"{name}_add"].value = value

    def clear_fields(self, target: str = "all") -> None:
        for name, field in self.fields.items():
            if target == "all" or (target == "add") == name.endswith("_add"):
                field.value = None
        self.flags.reset()


@pytest.fixture
def dpd_fields(monkeypatch: pytest.MonkeyPatch) -> FakeDpdFields:
    """Pick one word from History in a fake view and return its fields."""
    monkeypatch.setattr(
        Pass1AddView, "page", SimpleNamespace(update=lambda: None), raising=False
    )
    headword = SimpleNamespace(
        lemma_1="nara 1",
        lemma_2="nara",
        stem="nar",
        pattern="a masc",
        lemma_clean="nara",
    )
    fake_fields = FakeDpdFields()
    fake_fields.flags.stem_pattern_done = True
    fake_fields.flags.lemma_2_done = True

    view = object.__new__(Pass1AddView)
    view.db = SimpleNamespace(get_headword_by_id=lambda _: headword)  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields = fake_fields  # pyright: ignore[reportAttributeAccessIssue]
    view._history_dropdown = SimpleNamespace(value="1")  # pyright: ignore[reportAttributeAccessIssue]
    view.update_message = lambda _: None  # pyright: ignore[reportAttributeAccessIssue]
    view._handle_history_selection(SimpleNamespace(control=SimpleNamespace(value="1")))  # pyright: ignore[reportArgumentType]
    return fake_fields


def test_history_load_clears_suggestions(dpd_fields: FakeDpdFields) -> None:
    for name in FIELD_NAMES:
        assert not dpd_fields.fields[f"{name}_add"].value
    assert dpd_fields.fields["stem"].value == "nar"


def test_history_load_keeps_helper_flags(dpd_fields: FakeDpdFields) -> None:
    assert dpd_fields.flags.stem_pattern_done
    assert dpd_fields.flags.lemma_2_done
