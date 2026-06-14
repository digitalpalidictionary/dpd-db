"""Unit tests for the pure helpers in ``tools.cst_source.text_utils``.

These were verified byte-for-byte against the original module during the
refactor; the old module has since retired to ``archive/tools/``, so the
expected values below are asserted as literals.
"""

from tools.cst_source import text_utils as tu


def test_get_text_and_number() -> None:
    assert tu.get_text_and_number("2. Appamādavaggo") == ("Appamādavaggo", "2")


def test_brackets1() -> None:
    assert tu.get_text_and_number_with_brackets1("(1) Mahāvaggo") == ("Mahāvaggo", "1")


def test_brackets2() -> None:
    assert tu.get_text_and_number_with_brackets2("(7) 2. Sukhavaggo") == (
        "Sukhavaggo",
        "2",
    )


def test_brackets3() -> None:
    assert tu.get_text_and_number_with_brackets3("(12) 3. Kaṅkhākathā") == (
        "Kaṅkhākathā",
        "12",
    )


def test_brackets_end() -> None:
    assert tu.get_text_and_number_with_brackets_end("153. Sūkarajātakaṃ (2-1-3)") == (
        "Sūkarajātakaṃ",
        "153",
    )


def test_brackets_abhidhamma() -> None:
    assert tu.get_text_and_number_with_brackets_abhidhamma("(26. Ka) dovacassatā") == (
        "dovacassatā",
        "26",
    )


def test_square_brackets() -> None:
    assert tu.get_text_and_number_with_sqaure_brackets(
        "[111] 1. Gadrabhapañhajātakavaṇṇanā"
    ) == ("Gadrabhapañhajātakavaṇṇanā", "111")


def test_clean_subtitle() -> None:
    assert (
        tu.clean_subtitle("(7-8) Karacaraṇamudujālatālakkhaṇāni")
        == "Karacaraṇamudujālatālakkhaṇāni"
    )


def test_clean_example() -> None:
    assert tu.clean_example("Foo; Bar.") == "foo, bar."


def test_clean_gatha() -> None:
    assert tu.clean_gatha("Foo Bar, Baz.") == "foo bar,\nbaz."


def test_is_int() -> None:
    assert tu.is_int("5") is True
    assert tu.is_int("notanumber") is False


def test_assert_type_int() -> None:
    assert tu.assert_type_int("5") == "5"
    assert tu.assert_type_int("x") == ""


def test_assert_no_space() -> None:
    assert tu.assert_no_space("Pattavaggo") == "Pattavaggo"
    assert tu.assert_no_space("has space") == ""


def test_split_sutta_number() -> None:
    assert tu.split_sutta_number("1-4") == (1, 4, 4)


def test_module_imports_clean() -> None:
    """All package submodules import without error."""
    import tools.cst_source.examples  # noqa: F401
    import tools.cst_source.extractor  # noqa: F401
    import tools.cst_source.loader  # noqa: F401
    import tools.cst_source.models  # noqa: F401
    import tools.cst_source.parsers.registry  # noqa: F401
    import tools.cst_source.peyyala_data  # noqa: F401
    import tools.cst_source.text_utils  # noqa: F401


def test_peyyala_data() -> None:
    from tools.cst_source import peyyala_data

    assert peyyala_data.sn_peyyalas[0] == (12, "2-11. Jātisuttādidasakaṃ", 72, 81)
    assert peyyala_data.sn_collapsed_vagga_counts[(49, "appamādavaggo")] == 10


def test_models_namedtuple_fields() -> None:
    from tools.cst_source.models import CstSourceSuttaExample

    t = CstSourceSuttaExample(source="A", sutta="b", example="c")
    assert t._fields == ("source", "sutta", "example")
    assert (t.source, t.sutta, t.example) == ("A", "b", "c")
