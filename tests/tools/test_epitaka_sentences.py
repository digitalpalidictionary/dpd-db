import json
import sqlite3
from pathlib import Path

from tools.epitaka_sentences import _load_peu, epitaka_word_dict, peu_entries

# Real rows copied from ePitaka's epitaka.db / epitaka_en.db (2026-11-04).
BOOKS = [(28, "s0506m.mul", "Vv"), (29, "s0507m.mul", "Pv")]
ROWS = [
    (
        "Vv",
        15,
        1,
        "Kenāsi evaṃ jalitānubhāvā, vaṇṇo ca te sabbadisā pabhāsatī ’’ ti.",
        "Because of what do you have such blazing power, and your color shines in all directions?”",
    ),
    (
        "Vv",
        66,
        1,
        "19. ‘‘ Appassa kammassa phalaṃ mamedaṃ [mametaṃ (ka.)], yenamhi [tenamhi (ka.)] evaṃ jalitānubhāvā;",
        "19. ‘The fruit of a small amount of kamma is this for me, by which I am so blazing with power;",
    ),
    (
        "Pv",
        7,
        1,
        "1. ‘‘ Khettūpamā arahanto, dāyakā kassakūpamā;",
        "1. “Arahants are like fields, and donors are like farmers;",
    ),
]

# Real entries copied from PEU peu_dump.json (2026-11-04), trimmed.
PEU = {
    "jalita": "[Jala+ta] (ti) CL=8 (1) Bright and shining. Shiny. (2) burning (or) be aflame.",
    "jalitānubhāva": "[Jalita+ānubhāva] (pu) CL=8 (1) bright radiant power and glory.",
    "abaddhamukha": "[Abaddha+mukha] (ti) CL=9 Having a mouth that doesn't close, Rough in speech",
    "sa2": "The letter 's' is of three kinds",
}


def make_epitaka(tmp_path: Path) -> tuple[Path, Path]:
    pali_db = tmp_path / "epitaka.db"
    en_db = tmp_path / "epitaka_en.db"
    conn = sqlite3.connect(pali_db)
    conn.execute("CREATE TABLE books (id INTEGER, vri_id TEXT, book_id TEXT)")
    conn.execute(
        "CREATE TABLE sentences (book_id TEXT, para_id INTEGER, line_id INTEGER, pali TEXT)"
    )
    conn.executemany("INSERT INTO books VALUES (?, ?, ?)", BOOKS)
    conn.executemany("INSERT INTO sentences VALUES (?, ?, ?, ?)", [r[:4] for r in ROWS])
    conn.commit()
    conn.close()
    conn = sqlite3.connect(en_db)
    conn.execute(
        "CREATE TABLE sentences (book_id TEXT, para_id INTEGER, line_id INTEGER, translation TEXT)"
    )
    conn.executemany(
        "INSERT INTO sentences VALUES (?, ?, ?, ?)", [r[:3] + r[4:] for r in ROWS]
    )
    conn.commit()
    conn.close()
    return pali_db, en_db


def make_peu(tmp_path: Path) -> Path:
    path = tmp_path / "peu_dump.json"
    path.write_text(json.dumps(PEU, ensure_ascii=False), encoding="utf-8")
    _load_peu.cache_clear()
    return path


def test_epitaka_missing_files_give_empty_dict(tmp_path: Path) -> None:
    assert (
        epitaka_word_dict(["s0506m.mul"], tmp_path / "no.db", tmp_path / "no.db") == {}
    )


def test_epitaka_word_dict_maps_words_to_sentence_pairs(tmp_path: Path) -> None:
    pali_db, en_db = make_epitaka(tmp_path)
    d = epitaka_word_dict(["s0506m.mul"], pali_db, en_db)

    assert [p for p, _ in d["jalitānubhāvā"]] == [ROWS[0][3], ROWS[1][3]]
    assert d["jalitānubhāvā"][0][1] == ROWS[0][4]
    # Variant readings in square brackets are indexed, as in make_cst_text_list.
    assert d["mametaṃ"] == [(ROWS[1][3], ROWS[1][4])]
    # The source sigla in round brackets are not words.
    assert "ka" not in d
    # Only the requested CST file.
    assert "khettūpamā" not in d


def test_epitaka_word_dict_one_sentence_listed_once(tmp_path: Path) -> None:
    pali_db, en_db = make_epitaka(tmp_path)
    d = epitaka_word_dict(["s0506m.mul", "s0507m.mul"], pali_db, en_db)
    assert len(d["evaṃ"]) == 2
    assert d["khettūpamā"] == [(ROWS[2][3], ROWS[2][4])]


def test_peu_missing_file_gives_empty_list(tmp_path: Path) -> None:
    _load_peu.cache_clear()
    assert peu_entries("jalita", path=tmp_path / "no.json") == []


def test_peu_file_installed_later_is_found(tmp_path: Path) -> None:
    _load_peu.cache_clear()
    missing = tmp_path / "peu_dump.json"
    assert peu_entries("jalita", path=missing) == []

    # no cache_clear here: the lookup itself must not have cached the absence
    missing.write_text(json.dumps(PEU, ensure_ascii=False), encoding="utf-8")
    assert peu_entries("jalita", path=missing) != []


def test_peu_exact_match_wins(tmp_path: Path) -> None:
    path = make_peu(tmp_path)
    assert peu_entries("jalita", path=path) == [
        "jalita: [Jala+ta] (ti) (1) Bright and shining. Shiny. (2) burning (or) be aflame."
    ]


def test_peu_cut_ending_then_prefix(tmp_path: Path) -> None:
    path = make_peu(tmp_path)
    # cut 1 -> "jalitānubhāv" -> jalitānubhāva
    assert peu_entries("jalitānubhāvā", path=path) == [
        "jalitānubhāva: [Jalita+ānubhāva] (pu) (1) bright radiant power and glory."
    ]
    # cut 3 -> "abaddhamukh" -> abaddhamukha
    assert peu_entries("abaddhamukhassa", path=path)[0].startswith("abaddhamukha: ")


def test_peu_homonym_keys_match_clean_word(tmp_path: Path) -> None:
    path = make_peu(tmp_path)
    assert peu_entries("sa", path=path) == ["sa2: The letter 's' is of three kinds"]


def test_peu_trims_long_entries(tmp_path: Path) -> None:
    path = make_peu(tmp_path)
    result = peu_entries("abaddhamukha", max_chars=30, path=path)[0]
    assert result == "abaddhamukha: [Abaddha+mukha] (ti) Having a …"


def test_peu_no_hit(tmp_path: Path) -> None:
    path = make_peu(tmp_path)
    assert peu_entries("xyz", path=path) == []
