from types import SimpleNamespace


from gui2.dpd_fields import DpdFields


def _fields(all_lemma_1: set[str], bar: SimpleNamespace) -> DpdFields:
    fields = object.__new__(DpdFields)
    fields.flags = SimpleNamespace(loaded_from_db=False)  # type: ignore[assignment]
    fields.fields = {"lemma_1": SimpleNamespace(value="", error_text=None)}  # type: ignore[assignment]
    fields.db = SimpleNamespace(all_lemma_1=all_lemma_1)  # type: ignore[assignment]
    fields.ui = SimpleNamespace(  # type: ignore[assignment]
        page=SimpleNamespace(update=lambda: None),
        message_field=bar,
        update_message=lambda text: setattr(bar, "value", text),
    )
    return fields


def _event(value: str) -> SimpleNamespace:
    control = SimpleNamespace(value=value, error_text=None)
    return SimpleNamespace(control=control, name="blur")


def test_duplicate_lemma_1_goes_red_then_clears_when_changed() -> None:
    bar = SimpleNamespace(value="")
    fields = _fields({"karoti 1"}, bar)
    fields.validate_no_duplicates(None, "karoti 1")
    assert bar.value == "karoti 1 already in db"
    event = _event("karoti 1")
    fields.lemma_1_change(event)  # type: ignore[arg-type]
    assert event.control.error_text == "karoti 1 already in db"

    event.control.value = "karoti 2"
    fields.lemma_1_change(event)  # type: ignore[arg-type]
    assert event.control.error_text is None
    assert bar.value == ""


def test_a_newer_message_in_the_bar_is_kept() -> None:
    bar = SimpleNamespace(value="")
    fields = _fields({"karoti 1"}, bar)
    fields.validate_no_duplicates(None, "karoti 1")
    bar.value = "All tests passed"
    event = _event("karoti 2")
    fields.lemma_1_change(event)  # type: ignore[arg-type]
    assert bar.value == "All tests passed"
