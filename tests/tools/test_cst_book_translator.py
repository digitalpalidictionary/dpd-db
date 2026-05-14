from tools.cst_book_translator import (
    BookInfo,
    all_books,
    from_cst_book_name,
    from_cst_filename,
    from_dpd_code,
    from_gui_code,
    translate,
)


def test_all_books_loaded():
    books = all_books()
    assert len(books) > 100
    assert all(isinstance(b, BookInfo) for b in books)


def test_anchor_dn1_round_trip():
    b = from_cst_filename("s0101m.mul")
    assert b is not None
    assert b.gui_book_code == "dn1"
    assert b.dpd_book_code == "DN"
    assert b.cst_book_name == "Dīghanikāya, Sīlakkhandhavaggapāḷi"


def test_anchor_dna_commentary():
    b = from_cst_filename("s0101a.att")
    assert b is not None
    assert b.dpd_book_code == "DNa"


def test_gui_code_fan_out_kn14():
    rows = from_gui_code("kn14")
    stems = sorted(r.cst_filename for r in rows)
    assert stems == ["s0513m.mul", "s0514m.mul"]


def test_dpd_code_fan_out_vina():
    rows = from_dpd_code("VINa")
    assert len(rows) == 5
    assert all(r.dpd_book_code == "VINa" for r in rows)


def test_dpd_code_dn_returns_three_mul_files():
    rows = from_dpd_code("DN")
    stems = sorted(r.cst_filename for r in rows)
    assert stems == ["s0101m.mul", "s0102m.mul", "s0103m.mul"]


def test_lookup_is_case_insensitive():
    assert from_gui_code("KN14") == from_gui_code("kn14")
    assert from_dpd_code("dn") == from_dpd_code("DN")


def test_from_cst_book_name_exact():
    rows = from_cst_book_name("Dīghanikāya, Sīlakkhandhavaggapāḷi")
    assert len(rows) == 1
    assert rows[0].cst_filename == "s0101m.mul"


def test_from_cst_book_name_case_insensitive():
    rows = from_cst_book_name("dīghanikāya, sīlakkhandhavaggapāḷi")
    assert len(rows) == 1


def test_unknown_filename_returns_none():
    assert from_cst_filename("does_not_exist.mul") is None


def test_unknown_codes_return_empty():
    assert from_gui_code("zzz999") == []
    assert from_dpd_code("zzz999") == []
    assert from_cst_book_name("nothing here") == []


def test_translate_dispatches_filename():
    rows = translate("s0101m.mul")
    assert len(rows) == 1
    assert rows[0].gui_book_code == "dn1"


def test_translate_dispatches_gui_code():
    rows = translate("dn1")
    assert [r.cst_filename for r in rows] == ["s0101m.mul"]


def test_translate_dispatches_dpd_code():
    rows = translate("DN")
    assert len(rows) == 3


def test_translate_dispatches_book_name():
    rows = translate("Dīghanikāya, Sīlakkhandhavaggapāḷi")
    assert len(rows) == 1
    assert rows[0].cst_filename == "s0101m.mul"


def test_translate_empty_and_unknown():
    assert translate("") == []
    assert translate("zzz999") == []


def test_cst_xml_path_exists_for_anchor():
    b = from_cst_filename("s0101m.mul")
    assert b is not None
    assert b.cst_xml_path.exists()
    assert b.cst_xml_path.name == "s0101m.mul.xml"
