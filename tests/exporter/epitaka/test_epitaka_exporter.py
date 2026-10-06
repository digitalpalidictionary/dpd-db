"""Tests for the ePitaka exporter.

Input fields are copied from the 2026-05-01 DPD data, and expected strings
from the upstream dpd-dictionary.db built from that same data.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

from db.models import DpdHeadword, DpdRoot, FamilyRoot, Lookup
from exporter.epitaka import epitaka_exporter
from exporter.epitaka.epitaka_exporter import (
    close_app,
    install,
    make_headword_html,
    make_lookup_row,
    make_root_html,
    make_root_ids,
)

ROOT_KAM_1 = DpdRoot(root="√kam 1", root_sign="a", root_meaning="go")
ROOT_DHAR_1 = DpdRoot(root="√dhar 1", root_sign="a", root_meaning="hold, carry, endure")


def make_headword(rt: DpdRoot | None = None, **fields: str | int) -> DpdHeadword:
    defaults: dict[str, str] = {
        k: ""
        for k in [
            "pos",
            "grammar",
            "meaning_1",
            "meaning_lit",
            "meaning_2",
            "root_key",
            "root_sign",
            "root_base",
            "suffix",
            "construction",
            "compound_type",
            "compound_construction",
            "sanskrit",
            "example_1",
        ]
    }
    i = DpdHeadword(**{**defaults, **fields})
    if rt is not None:
        i.rt = rt
    return i


def dhamma_1_01(root_sign: str = "a") -> DpdHeadword:
    return make_headword(
        rt=ROOT_DHAR_1,
        id=34626,
        lemma_1="dhamma 1.01",
        pos="masc",
        grammar="masc, from dharati",
        meaning_1="nature; character",
        meaning_2="nature",
        root_key="√dhar 1",
        root_sign=root_sign,
        suffix="ma",
        construction="√dhar + ma",
        sanskrit="dharma [dhṛ]",
        example_1="atthi nu kho bhante kiñci rūpaṃ yaṃ rūpaṃ niccaṃ dhuvaṃ sassataṃ "
        "avipariṇāma<b>dhammaṃ</b> sassatisamaṃ tath'eva ṭhassati",
    )


DHAMMA_1_01_HTML = (
    "<details class='dpd-meaning'><summary><i>masc</i> <b>nature; character</b> "
    "nature [√dhar 1 + ma: hold, carry, endure]</summary>"
    "<div class='dpd-meaning-detail'>"
    "<div class='dpd-grammar'><b>Grammar:</b> masc, from dharati</div>"
    "<div class='dpd-sanskrit'><b>Sanskrit:</b> dharma [dhṛ]</div>"
    "<div class='dpd-root'><b>Root:</b> √dhar 1 a - √dhar + ma</div>"
    "<div class='dpd-example'><b>Example:</b> atthi nu kho bhante kiñci rūpaṃ yaṃ "
    "rūpaṃ niccaṃ dhuvaṃ sassataṃ avipariṇāma<b>dhammaṃ</b> sassatisamaṃ "
    "tath'eva ṭhassati</div></div></details>"
)


def test_headword_root_and_example() -> None:
    assert make_headword_html(dhamma_1_01()) == DHAMMA_1_01_HTML


def test_headword_empty_root_sign_uses_the_roots_sign() -> None:
    assert make_headword_html(dhamma_1_01(root_sign="")) == DHAMMA_1_01_HTML


def test_headword_meaning_2_and_lit() -> None:
    i = make_headword(
        rt=ROOT_KAM_1,
        id=7553,
        lemma_1="abhikkanta 1",
        pos="pp",
        grammar="pp of abhikkamati",
        meaning_1="superb; surpassing; excellent",
        meaning_lit="gone forward",
        meaning_2="most pleasant",
        root_key="√kam 1",
        root_sign="a",
        suffix="ta",
        construction="abhi + √kam + ta",
        sanskrit="atikrānta [abhikram]",
        example_1="evaṃ <b>abhikkanta</b>dassāviṃ,\natthi pañhena āgamaṃ,\n"
        "kathaṃ lokaṃ avekkhantaṃ,\nmaccurājā na passati.",
    )
    assert make_headword_html(i) == (
        "<details class='dpd-meaning'><summary><i>pp</i> "
        "<b>superb; surpassing; excellent</b> most pleasant (lit. gone forward) "
        "[√kam 1 + ta: go]</summary><div class='dpd-meaning-detail'>"
        "<div class='dpd-grammar'><b>Grammar:</b> pp of abhikkamati</div>"
        "<div class='dpd-sanskrit'><b>Sanskrit:</b> atikrānta [abhikram]</div>"
        "<div class='dpd-root'><b>Root:</b> √kam 1 a - abhi + √kam + ta</div>"
        "<div class='dpd-example'><b>Example:</b> evaṃ <b>abhikkanta</b>dassāviṃ,\n"
        "atthi pañhena āgamaṃ,\nkathaṃ lokaṃ avekkhantaṃ,\nmaccurājā na passati."
        "</div></div></details>"
    )


def test_headword_compound_no_root() -> None:
    i = make_headword(
        id=7,
        lemma_1="akakkasa",
        pos="adj",
        grammar="adj, from na kakkasa",
        meaning_1="smooth; tender; not harsh; not rough",
        construction="na > a + kakkasa",
        compound_type="kammadhāraya",
        compound_construction="na + kakkasa",
        sanskrit="akarkaśa (na + karkaśa)",
        example_1="<b>akakkasaṃ</b> viññāpaniṃ,\ngiraṃ saccam'udīraye,\n"
        "yāya n'ābhisaje kañci,\ntam'ahaṃ brūmi brāhmaṇaṃ.",
    )
    assert make_headword_html(i) == (
        "<details class='dpd-meaning'><summary><i>adj</i> "
        "<b>smooth; tender; not harsh; not rough</b></summary>"
        "<div class='dpd-meaning-detail'>"
        "<div class='dpd-grammar'><b>Grammar:</b> adj, from na kakkasa</div>"
        "<div class='dpd-sanskrit'><b>Sanskrit:</b> akarkaśa (na + karkaśa)</div>"
        "<div class='dpd-compound'><b>Compound:</b> kammadhāraya (na + kakkasa)</div>"
        "<div class='dpd-example'><b>Example:</b> <b>akakkasaṃ</b> viññāpaniṃ,\n"
        "giraṃ saccam'udīraye,\nyāya n'ābhisaje kañci,\ntam'ahaṃ brūmi brāhmaṇaṃ."
        "</div></div></details>"
    )


def test_headword_meaning_2_only() -> None:
    i = make_headword(
        id=220,
        lemma_1="akukkukata",
        pos="adj",
        grammar="adj",
        meaning_2="(what is) not temporary; give for an unlimited time",
    )
    assert make_headword_html(i) == (
        "<details class='dpd-meaning'><summary><i>adj</i> (what is) not temporary; "
        "give for an unlimited time</summary><div class='dpd-meaning-detail'>"
        "<div class='dpd-grammar'><b>Grammar:</b> adj</div></div></details>"
    )


def test_headword_no_root_no_compound() -> None:
    i = make_headword(
        id=22620,
        lemma_1="kusala 1",
        pos="adj",
        grammar="adj",
        meaning_1="healthy; beneficial; useful; good; wholesome; karmically profitable",
        sanskrit="kuśala",
        example_1="ime kho cunda dasa <b>kusala</b>kammapathā",
    )
    assert make_headword_html(i) == (
        "<details class='dpd-meaning'><summary><i>adj</i> <b>healthy; beneficial; "
        "useful; good; wholesome; karmically profitable</b></summary>"
        "<div class='dpd-meaning-detail'>"
        "<div class='dpd-grammar'><b>Grammar:</b> adj</div>"
        "<div class='dpd-sanskrit'><b>Sanskrit:</b> kuśala</div>"
        "<div class='dpd-example'><b>Example:</b> ime kho cunda dasa "
        "<b>kusala</b>kammapathā</div></div></details>"
    )


def test_root_with_family_table() -> None:
    r = DpdRoot(
        root="√kiñc",
        root_group=1,
        root_sign="a",
        root_meaning="crush",
        sanskrit_root="",
        sanskrit_root_meaning="",
        root_example="kiñcati",
        dhatupatha_pali="maddane",
        dhatupatha_english="crushing",
        dhatumanjusa_pali="avamaddane",
        dhatumanjusa_english="breaking up, destroying",
        note="",
    )
    family = (
        "<p class='heading underlined'><b>2</b> words belong to the root family "
        "<b>√kiñc</b> (crush)</p><table class='family'><tr><th>kiñcati</th>"
        "<td><b>pr</b></td><td>crushes; tramples</td>"
        '<td><span class="gray">✔</span></td></tr><tr><th>kiñceti</th>'
        "<td><b>pr</b></td><td>crushes; tramples; lit. causes to crush</td>"
        '<td><span class="gray">✔</span></td></tr></table>'
    )
    assert make_root_html(r, 2, [FamilyRoot(html=family)]) == (
        "<details class='dpd-root-meaning'><summary><b>√kiñc</b> crush</summary>"
        "<div class='dpd-meaning-detail'>"
        "<div class='dpd-root-group'><b>Group:</b> 1a</div>"
        "<div class='dpd-root-example'><b>Example:</b> kiñcati</div>"
        "<div class='dpd-dhatupatha'><b>Dhātupāṭha:</b> maddane - crushing</div>"
        "<div class='dpd-dhatumanjusa'><b>Dhātumañjūsā:</b> avamaddane - "
        "breaking up, destroying</div>"
        "<div class='dpd-root-count'><b>Word count:</b> 2</div>"
        f"{family}</div></details>"
    )


def test_root_sanskrit_bracket() -> None:
    r = DpdRoot(
        root="√acc 1",
        root_group=1,
        root_sign="a",
        root_meaning="shine, praise",
        sanskrit_root="√arc",
        sanskrit_root_meaning="shine, praise",
        root_example="accha, acci, accī",
        dhatupatha_pali="pūjāyaṃ",
        dhatupatha_english="worshipping",
        dhatumanjusa_pali="accane",
        dhatumanjusa_english="respecting",
        note="",
    )
    assert make_root_html(r, 10, []).startswith(
        "<details class='dpd-root-meaning'><summary><b>√acc 1</b> shine, praise "
        "[skt. √arc (shine, praise)]</summary>"
    )


def test_root_ids_follow_last_headword_in_plain_order() -> None:
    roots = [DpdRoot(root=r) for r in ["√ad", "√acc 2", "√add", "√acc 1"]]
    assert make_root_ids(roots, 89412) == {
        "√acc 1": 89413,
        "√acc 2": 89414,
        "√ad": 89415,
        "√add": 89416,
    }


def test_lookup_row_adds_root_ids_after_headword_ids() -> None:
    lookup = Lookup(
        lookup_key="acc",
        headwords=json.dumps([927]),
        roots=json.dumps(["√acc 1", "√acc 2"], ensure_ascii=False),
        deconstructor="",
    )
    root_ids = {"√acc 1": 89413, "√acc 2": 89414}
    assert make_lookup_row(lookup, root_ids) == ("acc", "[927, 89413, 89414]", None)


def test_lookup_row_empty_columns_are_null() -> None:
    lookup = Lookup(lookup_key="x", headwords="", roots="", deconstructor="")
    assert make_lookup_row(lookup, {}) == ("x", None, None)


def test_lookup_row_deconstructor_keeps_diacritics() -> None:
    lookup = Lookup(
        lookup_key="anudā",
        headwords="",
        roots="",
        deconstructor=json.dumps(["na + udā"], ensure_ascii=False),
    )
    assert make_lookup_row(lookup, {}) == ("anudā", None, '["na + udā"]')


@pytest.mark.parametrize(
    ("flag", "db_path"),
    [
        ("no", "/tmp/dpd-dictionary.db"),
        ("yes", ""),
        ("yes", "/no/such/folder/dpd-dictionary.db"),
    ],
)
def test_main_exits_before_opening_the_db(
    monkeypatch: pytest.MonkeyPatch, flag: str, db_path: str
) -> None:
    config = {("exporter", "make_epitaka"): flag, ("epitaka", "db_path"): db_path}
    monkeypatch.setattr(
        epitaka_exporter,
        "config_test",
        lambda section, option, value: config[(section, option)] == value,
    )
    monkeypatch.setattr(
        epitaka_exporter,
        "config_read",
        lambda section, option: config.get((section, option), ""),
    )

    def fail(*args: object) -> None:
        raise AssertionError("dpd.db was opened")

    monkeypatch.setattr(epitaka_exporter, "get_db_session", fail)
    epitaka_exporter.main()


def make_db(path: Path, table: str, wal: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    if wal:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute(f"CREATE TABLE {table} (x TEXT)")
    conn.executemany(f"INSERT INTO {table} VALUES (?)", [(table,)] * 1000)
    conn.commit()
    return conn


def test_install_replaces_wal_destination(tmp_path: Path) -> None:
    out = tmp_path / "out.db"
    dest = tmp_path / "dest.db"
    baseline = tmp_path / "baseline.db"
    baseline.touch()
    make_db(out, "new_table").close()
    # The app keeps its connection open, so the old content sits in the WAL.
    app = make_db(dest, "old_table", wal=True)
    assert (tmp_path / "dest.db-wal").stat().st_size > 0

    assert install(out, dest, baseline)
    app.close()

    conn = sqlite3.connect(dest)
    tables = [n for (n,) in conn.execute("SELECT name FROM sqlite_master")]
    assert tables == ["new_table"]
    assert conn.execute("SELECT COUNT(*) FROM new_table").fetchone() == (1000,)
    assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    conn.close()


def test_install_refuses_without_baseline(tmp_path: Path) -> None:
    out = tmp_path / "out.db"
    dest = tmp_path / "dest.db"
    make_db(out, "new_table").close()
    make_db(dest, "old_table").close()

    assert not install(out, dest, tmp_path / "baseline.db")

    conn = sqlite3.connect(dest)
    tables = [n for (n,) in conn.execute("SELECT name FROM sqlite_master")]
    assert tables == ["old_table"]
    conn.close()


def test_close_app_waits_for_exit() -> None:
    child = subprocess.Popen(["sleep", "60"])
    try:
        assert close_app([psutil.Process(child.pid)], timeout=10)
        assert child.wait(timeout=1) is not None
    finally:
        child.kill()


def test_close_app_reports_a_process_that_ignores_quit() -> None:
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "print('ready', flush=True); time.sleep(60)",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        child.stdout.readline()
        assert not close_app([psutil.Process(child.pid)], timeout=0.5)
    finally:
        child.kill()
        child.wait()


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    running: bool,
    closes: bool = True,
) -> list[str]:
    calls: list[str] = []
    config = {
        ("exporter", "make_epitaka"): "yes",
        ("epitaka", "db_path"): str(tmp_path / "dpd-dictionary.db"),
    }
    monkeypatch.setattr(
        epitaka_exporter,
        "config_test",
        lambda section, option, value: config[(section, option)] == value,
    )
    monkeypatch.setattr(
        epitaka_exporter,
        "config_read",
        lambda section, option: config.get((section, option), ""),
    )
    monkeypatch.setattr(epitaka_exporter, "get_db_session", lambda path: None)
    monkeypatch.setattr(
        epitaka_exporter, "build_db", lambda *args: calls.append("build")
    )
    monkeypatch.setattr(
        epitaka_exporter, "prebuild_norm_table", lambda *args: calls.append("norm")
    )
    monkeypatch.setattr(
        epitaka_exporter, "app_processes", lambda: ["app"] if running else []
    )

    def close(procs: list[object]) -> bool:
        calls.append("close")
        return closes

    monkeypatch.setattr(epitaka_exporter, "close_app", close)
    monkeypatch.setattr(
        epitaka_exporter, "install", lambda *args: calls.append("install")
    )
    monkeypatch.setattr(epitaka_exporter, "open_app", lambda: calls.append("open"))
    epitaka_exporter.main()
    return calls


def test_main_closes_and_reopens_a_running_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=True) == [
        "build",
        "norm",
        "close",
        "install",
        "open",
    ]


def test_main_does_not_open_an_app_that_was_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=False) == [
        "build",
        "norm",
        "install",
    ]


def test_main_skips_install_when_app_will_not_close(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=True, closes=False) == [
        "build",
        "norm",
        "close",
    ]
