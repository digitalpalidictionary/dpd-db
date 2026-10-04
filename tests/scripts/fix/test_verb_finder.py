"""Causative and passive forms must name a verb of the same kind.

Rows are modelled on dpd.db (2026-10-01), trimmed to the columns the scan reads.
Some are changed or invented to isolate one rule; the comment on each says so.
"""

from collections import Counter
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, DpdRoot
from scripts.fix.verb_finder import (
    build_pr_verb_index,
    load_all_lemmas,
    marker_chain,
    scan_derived_forms,
    verb_kind,
)


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def add(
    db: Session,
    lemma_1: str,
    pos: str,
    grammar: str,
    family_root: str,
    root_key: str,
    verb: str = "",
    root_sign: str = "",
    meaning_1: str = "x",
) -> None:
    db.add(
        DpdHeadword(
            lemma_1=lemma_1,
            pos=pos,
            grammar=grammar,
            family_root=family_root,
            root_key=root_key,
            verb=verb,
            root_sign=root_sign,
            meaning_1=meaning_1,
            meaning_lit="",
        )
    )
    db.commit()


def bucket_of(
    db: Session, lemma_1: str, cst_freq: Counter[str] | None = None
) -> tuple[str, dict]:
    pr_index, pr_lemma_map = build_pr_verb_index(db)
    buckets = scan_derived_forms(
        db, pr_index, pr_lemma_map, cst_freq or Counter(), load_all_lemmas(db)
    )
    for name, rows in buckets.items():
        if name == "grammar_derived_from_mismatch":
            continue
        for row in rows:
            if row["lemma_1"] == lemma_1:
                return name, row
    raise AssertionError(f"{lemma_1} is in no bucket")


def test_verb_kind_matches_whole_words_only() -> None:
    assert verb_kind("caus, pass") == {"caus", "pass"}
    assert verb_kind("prp of pass of roseti") == {"pass"}
    assert verb_kind("prp of passati") == frozenset()


def test_marker_chain() -> None:
    assert marker_chain("pass of roseti") == "pass of "
    assert marker_chain("caus of anu √su") == "caus of "
    assert marker_chain("passati") == ""


def test_missing_causative_attested_in_cst(db_session: Session) -> None:
    # The reported case: kāsituṃ names kāseti, which is not a headword.
    add(db_session, "kasati", "pr", "pr", "√kas", "√kas 1", root_sign="a")
    add(db_session, "kāsituṃ", "inf", "inf of kāseti", "√kas", "√kas 1", "caus")
    name, _row = bucket_of(db_session, "kāsituṃ", Counter({"kāseti": 1}))
    assert name == "verb_in_cst"


def test_missing_causative_goes_to_root(db_session: Session) -> None:
    add(db_session, "kasati", "pr", "pr", "√kas", "√kas 1", root_sign="a")
    add(db_session, "kāsituṃ", "inf", "inf of kāseti", "√kas", "√kas 1", "caus")
    name, row = bucket_of(db_session, "kāsituṃ")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "inf of caus of √kas"


def test_missing_passive_skips_the_causative(db_session: Session) -> None:
    # Invented codeti: a causative, which a passive form may not be sent to.
    add(db_session, "codeti", "pr", "pr, caus of codati", "√cud", "√cud")
    add(
        db_session,
        "codiyamāna",
        "prp",
        "prp of codiyati",
        "√cud",
        "√cud",
        "pass",
        "*e iya",
    )
    name, row = bucket_of(db_session, "codiyamāna")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "prp of pass of √cud"


def test_kind_split_across_verb_and_grammar(db_session: Session) -> None:
    # desiyati: "caus" in the verb column, "pass" in the grammar.
    add(
        db_session,
        "desiyati",
        "pr",
        "pr, pass of deseti",
        "√dis",
        "√dis 2",
        "caus",
        "*e iya",
    )
    add(
        db_session,
        "desiyamāna",
        "prp",
        "prp of desiyati",
        "√dis",
        "√dis 2",
        "caus, pass",
        "*e iya",
    )
    name, _row = bucket_of(db_session, "desiyamāna")
    assert name == "special_verbs"


def test_aya_form_never_goes_to_an_e_verb(db_session: Session) -> None:
    # padhaṃsayati is not a headword, and padhaṃseti is *e: the root family.
    add(
        db_session,
        "padhaṃseti",
        "pr",
        "pr, caus of padhaṃsati",
        "pa √dhaṃs",
        "√dhaṃs",
        root_sign="*e",
    )
    add(
        db_session,
        "padhaṃsayi",
        "aor",
        "aor of padhaṃsayati",
        "pa √dhaṃs",
        "√dhaṃs",
        "caus",
        "*aya",
    )
    name, row = bucket_of(db_session, "padhaṃsayi")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "aor of caus of pa √dhaṃs"


def test_stem_picks_one_of_three_causatives(db_session: Session) -> None:
    # kappayati is missing; only the *aya causative at the root fits.
    for lemma, sign in (
        ("kappeti 1", "*e"),
        ("kappāpeti", "*āpe"),
        ("kāpayati", "*aya"),
    ):
        add(
            db_session,
            lemma,
            "pr",
            "pr, caus of kappati",
            "√kapp",
            "√kapp 1",
            root_sign=sign,
        )
    add(
        db_session,
        "kappayanta",
        "prp",
        "prp of kappayati",
        "√kapp",
        "√kapp 1",
        "caus",
        "*aya",
    )
    name, row = bucket_of(db_session, "kappayanta")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "prp of kāpayati"


def test_double_causative_never_goes_to_single(db_session: Session) -> None:
    # sandeti is *e; sandāpetuṃ is *āpe. No *āpe verb exists, so the root.
    add(
        db_session,
        "sandeti",
        "pr",
        "pr, caus of sandati",
        "√sand",
        "√sand",
        root_sign="*e",
    )
    add(
        db_session,
        "sandāpetuṃ",
        "inf",
        "inf of sandāpeti",
        "√sand",
        "√sand",
        "caus",
        "*āpe",
    )
    name, row = bucket_of(db_session, "sandāpetuṃ")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "inf of caus of √sand"


def test_two_finished_verbs_fit(db_session: Session) -> None:
    add(db_session, "pārupati", "pr", "pr", "pa ā √var", "√var 1", root_sign="a")
    for verb in ("pārupeti", "pāvāreti"):
        add(
            db_session,
            verb,
            "pr",
            "pr, caus of pāpurati",
            "pa ā √var",
            "√var 1",
            root_sign="*e",
        )
    add(
        db_session,
        "pārupituṃ",
        "inf",
        "inf of pārupati",
        "pa ā √var",
        "√var 1",
        "caus",
        "*e",
    )
    name, row = bucket_of(db_session, "pārupituṃ")
    assert name == "ambiguous"
    assert row["candidates"] == "pārupeti|pāvāreti"


def test_draft_verb_at_root_blocks_correction(db_session: Session) -> None:
    # A draft with the same stem and no kind stated may be the causative.
    add(
        db_session,
        "padhaṃsayati",
        "pr",
        "pr",
        "pa √dhaṃs",
        "√dhaṃs",
        root_sign="*aya",
        meaning_1="",
    )
    add(
        db_session,
        "padhaṃsayi",
        "aor",
        "aor of padhaṃsāyati",
        "pa √dhaṃs",
        "√dhaṃs",
        "caus",
        "*aya",
    )
    name, row = bucket_of(db_session, "padhaṃsayi")
    assert name == "draft_verb"
    assert row["grammar_proposed"] == ""


def test_draft_with_another_stem_does_not_block(db_session: Session) -> None:
    add(
        db_session,
        "padhaṃseti",
        "pr",
        "pr",
        "pa √dhaṃs",
        "√dhaṃs",
        root_sign="*e",
        meaning_1="",
    )
    add(
        db_session,
        "padhaṃsayi",
        "aor",
        "aor of padhaṃsayati",
        "pa √dhaṃs",
        "√dhaṃs",
        "caus",
        "*aya",
    )
    name, _row = bucket_of(db_session, "padhaṃsayi")
    assert name == "would_change_to_root"


def test_named_draft_verb_with_same_stem_is_kept(db_session: Session) -> None:
    # pesayati has no meaning or label, but pesayi shares its *aya stem.
    # √pis is group 8, where *aya is the present stem, not a causative.
    db_session.add(DpdRoot(root="√pis 1", root_group=8))
    add(
        db_session,
        "pesayati",
        "pr",
        "pr",
        "√pis",
        "√pis 1",
        root_sign="*aya",
        meaning_1="",
    )
    add(
        db_session,
        "pesayi",
        "aor",
        "aor of pesayati",
        "√pis",
        "√pis 1",
        "caus",
        "*aya",
    )
    name, _row = bucket_of(db_session, "pesayi")
    assert name == "special_verbs"


def test_same_stem_overrides_a_missing_label(db_session: Session) -> None:
    # ghāteti carries no caus label, but ghātetāya shares its *e stem.
    db_session.add(DpdRoot(root="√ghaṭ 1", root_group=8))
    add(db_session, "ghāteti", "pr", "pr", "√ghaṭ", "√ghaṭ 1", root_sign="*e")
    add(
        db_session,
        "ghātāpeti",
        "pr",
        "pr, caus of ghāteti",
        "√ghaṭ",
        "√ghaṭ 1",
        root_sign="*āpe",
    )
    add(
        db_session,
        "ghātetāya",
        "ptp",
        "ptp of ghāteti",
        "√ghaṭ",
        "√ghaṭ 1",
        "caus",
        "*e",
    )
    name, _row = bucket_of(db_session, "ghātetāya")
    assert name == "special_verbs"


def test_plain_form_named_passati_is_not_special(db_session: Session) -> None:
    add(db_session, "passati", "pr", "pr", "√dis", "√dis 1", root_sign="a")
    add(db_session, "passamāna", "prp", "prp of passati", "√dis", "√dis 1")
    name, _row = bucket_of(db_session, "passamāna")
    assert name == "ok_verb_present"


def test_impers_is_not_part_of_the_match(db_session: Session) -> None:
    # vijjati is impers and pass; vijjare is its reflexive 3rd pl.
    for lemma in ("vijjati 1", "vijjati 2"):
        add(
            db_session,
            lemma,
            "pr",
            "pr, pass of vindati",
            "√vid",
            "√vid 2",
            "impers",
            "ya",
        )
    add(
        db_session,
        "vijjare",
        "pr",
        "pr, reflx 3rd pl of vijjati",
        "√vid",
        "√vid 2",
        "pass",
        "ya",
    )
    add(
        db_session,
        "vijjamāna 1",
        "prp",
        "prp of vijjati",
        "√vid",
        "√vid 2",
        "pass",
        "ya",
    )
    name, _row = bucket_of(db_session, "vijjamāna 1")
    assert name == "special_verbs"


def test_special_case_form_is_never_a_candidate(db_session: Session) -> None:
    # Without vijjati, the reflexive 3rd pl vijjare must not be offered.
    add(
        db_session,
        "vijjare",
        "pr",
        "pr, reflx 3rd pl of vijjati",
        "√vid",
        "√vid 2",
        "pass",
        "ya",
    )
    add(
        db_session,
        "vijjamāna 1",
        "prp",
        "prp of vijjati",
        "√vid",
        "√vid 2",
        "pass",
        "ya",
    )
    name, row = bucket_of(db_session, "vijjamāna 1")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "prp of pass of √vid"


def test_special_case_form_of_another_kind_is_kept(db_session: Session) -> None:
    # upasamati is the plain verb; upasammati is the passive, a different verb.
    add(
        db_session,
        "upasammati 1",
        "pr",
        "pr",
        "upa √sam",
        "√sam 1",
        "pass",
        "ya",
    )
    add(
        db_session,
        "upasamati",
        "pr",
        "pr, irreg form of upasammati",
        "upa √sam",
        "√sam 1",
        "pass",
        "ya",
    )
    add(
        db_session,
        "upasamamāna",
        "prp",
        "prp of upasamati",
        "upa √sam",
        "√sam 1",
        root_sign="ya",
    )
    name, _row = bucket_of(db_session, "upasamamāna")
    assert name == "ok_verb_present"


def test_same_stem_proves_the_named_verb(db_session: Session) -> None:
    # kappayati is unlabelled and at √kapp 2; kappayi is caus *aya at √kapp 1.
    add(
        db_session,
        "kappayati",
        "pr",
        "pr",
        "√kapp",
        "√kapp 2",
        root_sign="*aya",
    )
    db_session.add(DpdRoot(root="√kapp 2", root_group=8))
    add(
        db_session,
        "kappeti 1",
        "pr",
        "pr, caus of kappati",
        "√kapp",
        "√kapp 1",
        root_sign="*e",
    )
    add(
        db_session,
        "kappayi",
        "aor",
        "aor of kappayati",
        "√kapp",
        "√kapp 1",
        "caus",
        "*aya",
    )
    name, _row = bucket_of(db_session, "kappayi")
    assert name == "special_verbs"


def test_exact_stem_wins_over_partner_stem(db_session: Session) -> None:
    add(
        db_session,
        "ujjalayati",
        "pr",
        "pr, caus of ujjalati",
        "ud √jal",
        "√jal 1",
        root_sign="*aya",
    )
    add(
        db_session,
        "ujjaleti",
        "pr",
        "pr, caus of ujjalati",
        "ud √jal",
        "√jal 1",
        root_sign="*e",
    )
    add(
        db_session,
        "ujjāletuṃ",
        "inf",
        "inf of ujjāleti",
        "ud √jal",
        "√jal 1",
        "caus",
        "*e",
    )
    name, row = bucket_of(db_session, "ujjāletuṃ")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "inf of ujjaleti"


def test_draft_with_stated_kind_is_trusted(db_session: Session) -> None:
    # padhaṃseti has no meaning yet, but its grammar says caus.
    add(
        db_session,
        "padhaṃseti",
        "pr",
        "pr, caus of padhaṃsati",
        "pa √dhaṃs",
        "√dhaṃs",
        root_sign="*e",
        meaning_1="",
    )
    add(
        db_session,
        "padhaṃsetvā",
        "abs",
        "abs of padhaṃsāpeti",
        "pa √dhaṃs",
        "√dhaṃs",
        "caus",
        "*e",
    )
    name, row = bucket_of(db_session, "padhaṃsetvā")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "abs of padhaṃseti"


def test_finished_entries_that_disagree(db_session: Session) -> None:
    # Real desiyati also has caus in its verb column; dropped here to make the
    # labels disagree on the same *e iya stem.
    add(
        db_session,
        "desiyati",
        "pr",
        "pr, pass of deseti",
        "√dis",
        "√dis 2",
        root_sign="*e iya",
    )
    add(
        db_session,
        "desiyamāna",
        "prp",
        "prp of desiyati",
        "√dis",
        "√dis 2",
        "caus, pass",
        "*e iya",
    )
    name, row = bucket_of(db_session, "desiyamāna")
    assert name == "kind_mismatch"
    assert row["grammar_proposed"] == ""


def test_negative_verb_is_never_a_candidate(db_session: Session) -> None:
    # nappadūseti says "caus of na" but not "from na"; only the neg column
    # marks it.
    add(
        db_session,
        "padūseti",
        "pr",
        "pr, caus of padussati",
        "pa √dus",
        "√dus 1",
        root_sign="*e",
    )
    db_session.add(
        DpdHeadword(
            lemma_1="nappadūseti",
            pos="pr",
            grammar="pr, caus of na padussati",
            family_root="pa √dus",
            root_key="√dus 1",
            root_sign="*e",
            neg="neg",
            meaning_1="x",
        )
    )
    db_session.commit()
    add(
        db_session,
        "padosetvā",
        "abs",
        "abs of padoseti",
        "pa √dus",
        "√dus 1",
        "caus",
        "*e",
    )
    name, row = bucket_of(db_session, "padosetvā")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "abs of padūseti"


def test_caus_pass_form_may_not_name_a_caus_verb(db_session: Session) -> None:
    # rosiyamāna is caus, pass *e iya; roseti is caus *e. The root family,
    # written by hand because it carries two kinds.
    add(
        db_session,
        "roseti",
        "pr",
        "pr, caus of rosati",
        "√rus",
        "√rus",
        root_sign="*e",
    )
    add(
        db_session,
        "rosiyamāna",
        "prp",
        "prp of pass of roseti",
        "√rus",
        "√rus",
        "caus",
        "*e iya",
    )
    name, row = bucket_of(db_session, "rosiyamāna")
    assert name == "root_by_hand"
    assert row["candidates"] == "√rus"


@pytest.mark.parametrize(
    ("form", "grammar", "verb", "family_root", "root_key", "root_sign", "verb_sign"),
    [
        # The two reported cases: a causative root form with only a plain
        # verb at the root stays on the root.
        (
            "nimmathesi",
            "aor of caus of nī √math",
            "nimmathati",
            "nī √math",
            "√math",
            "*e",
            "a",
        ),
        (
            "paṭisaṅkhayanta",
            "prp of caus of pati saṃ √khā",
            "paṭisaṅkhāti",
            "pati saṃ √khā",
            "√khā",
            "*aya",
            "ā",
        ),
    ],
)
def test_caus_root_form_never_names_a_plain_verb(
    db_session: Session,
    form: str,
    grammar: str,
    verb: str,
    family_root: str,
    root_key: str,
    root_sign: str,
    verb_sign: str,
) -> None:
    add(db_session, verb, "pr", "pr", family_root, root_key, root_sign=verb_sign)
    pos = grammar.split()[0]
    add(db_session, form, pos, grammar, family_root, root_key, root_sign=root_sign)
    name, row = bucket_of(db_session, form)
    assert name == "special_verbs"
    assert row["grammar_proposed"] == ""


def test_caus_root_form_names_the_causative(db_session: Session) -> None:
    # A causative at the root replaces "caus of <root>" outright.
    add(db_session, "nimmathati", "pr", "pr", "nī √math", "√math", root_sign="a")
    add(
        db_session,
        "nimmatheti",
        "pr",
        "pr, caus of nimmathati",
        "nī √math",
        "√math",
        root_sign="*e",
    )
    add(
        db_session,
        "nimmathesi",
        "aor",
        "aor of caus of nī √math",
        "nī √math",
        "√math",
        root_sign="*e",
    )
    name, row = bucket_of(db_session, "nimmathesi")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "aor of nimmatheti"


def test_root_form_without_its_kind_is_corrected(db_session: Session) -> None:
    # Written by an earlier run: caus in the verb column, not in the grammar.
    add(
        db_session,
        "abhidhārayi",
        "aor",
        "aor of abhi √dhar",
        "abhi √dhar",
        "√dhar",
        "caus",
        "*aya",
    )
    name, row = bucket_of(db_session, "abhidhārayi")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "aor of caus of abhi √dhar"


def test_two_kinds_on_a_root_go_to_the_editor(db_session: Session) -> None:
    add(
        db_session,
        "kāriyamāna",
        "prp",
        "prp of kāriyati",
        "√kar",
        "√kar",
        "caus, pass",
        "*e iya",
    )
    name, row = bucket_of(db_session, "kāriyamāna")
    assert name == "root_by_hand"
    assert row["grammar_proposed"] == ""


def test_negative_on_a_root_goes_to_the_editor(db_session: Session) -> None:
    add(
        db_session,
        "acodiyamāna",
        "prp",
        "prp of na codiyati",
        "√cud",
        "√cud",
        "pass",
        "*e iya",
    )
    name, _row = bucket_of(db_session, "acodiyamāna")
    assert name == "root_by_hand"


def test_deno_form_is_skipped(db_session: Session) -> None:
    # Real: a denominative is built from a noun, so naming sadha is fine.
    add(
        db_session,
        "sadhāyamāna",
        "prp",
        "prp of sadhāyati, deno of sadha",
        "√sadh",
        "√sadh",
        root_sign="āya",
    )
    name, _row = bucket_of(db_session, "sadhāyamāna")
    assert name == "special_verbs"


def test_malformed_special_grammar_is_reported(db_session: Session) -> None:
    # Real: "prp, caus of pharati" has no "<pos> of" head, so it is unparsed.
    add(
        db_session,
        "pharāpenta",
        "prp",
        "prp, caus of pharati",
        "√phar",
        "√phar",
        root_sign="*āpe",
    )
    name, _row = bucket_of(db_session, "pharāpenta")
    assert name == "unparsed"


def add_neg(db: Session, lemma_1: str, grammar: str, root_sign: str) -> None:
    db.add(
        DpdHeadword(
            lemma_1=lemma_1,
            pos="pr",
            grammar=grammar,
            family_root="pa √dus",
            root_key="√dus 1",
            root_sign=root_sign,
            neg="neg",
            meaning_1="x",
        )
    )
    db.commit()


def test_plain_form_never_goes_to_a_negative_verb(db_session: Session) -> None:
    # Invented: the only plain verb at the root is negative.
    add_neg(db_session, "nappadussati", "pr, of na padussati", "ya")
    add(
        db_session,
        "padussanta",
        "prp",
        "prp of padūsati",
        "pa √dus",
        "√dus 1",
        root_sign="ya",
    )
    name, row = bucket_of(db_session, "padussanta")
    assert name == "would_change_to_root"
    assert row["grammar_proposed"] == "prp of pa √dus"


def test_plain_form_never_goes_to_a_special_case_form(db_session: Session) -> None:
    # Invented: the only verb at the root is a reflexive 3rd sg.
    add(
        db_session,
        "padussate",
        "pr",
        "pr, reflx 3rd sg of padussati",
        "pa √dus",
        "√dus 1",
        root_sign="ya",
    )
    add(
        db_session,
        "padussanta",
        "prp",
        "prp of padūsati",
        "pa √dus",
        "√dus 1",
        root_sign="ya",
    )
    name, _row = bucket_of(db_session, "padussanta")
    assert name == "would_change_to_root"


def test_special_form_naming_a_variant_goes_to_its_verb(db_session: Session) -> None:
    # Real sajjatī is "irreg form of sajjati"; sajjati is invented here.
    add(db_session, "sajjati", "pr", "pr", "√saj", "√saj 1", "pass", "ya")
    add(
        db_session,
        "sajjatī",
        "pr",
        "pr, irreg form of sajjati",
        "√saj",
        "√saj 1",
        "pass",
        "ya",
    )
    add(
        db_session,
        "sajjamāna",
        "prp",
        "prp of sajjatī",
        "√saj",
        "√saj 1",
        "pass",
        "ya",
    )
    name, row = bucket_of(db_session, "sajjamāna")
    assert name == "would_change_to_verb"
    assert row["grammar_proposed"] == "prp of sajjati"


def test_variant_base_with_another_stem_is_not_used(db_session: Session) -> None:
    add(db_session, "sajjati", "pr", "pr", "√saj", "√saj 1", "pass", "iya")
    add(
        db_session,
        "sajjatī",
        "pr",
        "pr, irreg form of sajjati",
        "√saj",
        "√saj 1",
        "pass",
        "ya",
    )
    add(
        db_session,
        "sajjamāna",
        "prp",
        "prp of sajjatī",
        "√saj",
        "√saj 1",
        "pass",
        "ya",
    )
    name, _row = bucket_of(db_session, "sajjamāna")
    assert name != "would_change_to_verb"


def test_plain_variant_with_another_stem_is_kept(db_session: Session) -> None:
    # Real: nimmīlati (a) is listed as an irregular form of nimmīleti (*e).
    # √mīl is group 8, so nimmīleti is a plain verb.
    db_session.add(DpdRoot(root="√mīl", root_group=8))
    add(db_session, "nimmīleti", "pr", "pr", "ni √mīl", "√mīl", root_sign="*e")
    add(
        db_session,
        "nimmīlati",
        "pr",
        "pr, irreg form of nimmīleti",
        "ni √mīl",
        "√mīl",
        root_sign="a",
    )
    add(
        db_session,
        "nimmīlanta",
        "prp",
        "prp of nimmīlati",
        "ni √mīl",
        "√mīl",
        root_sign="a",
    )
    name, _row = bucket_of(db_session, "nimmīlanta")
    assert name == "ok_verb_present"


def test_label_disagreement_wins_over_another_candidate(db_session: Session) -> None:
    # Real bhāviyamāna and bhāviyati; bhāvīyati is invented as a second fit.
    add(
        db_session,
        "bhāviyati",
        "pr",
        "pr, pass of bhāveti",
        "√bhū",
        "√bhū",
        root_sign="*e iya",
    )
    add(
        db_session,
        "bhāvīyati",
        "pr",
        "pr, caus, pass of bhavati",
        "√bhū",
        "√bhū",
        root_sign="*e iya",
    )
    add(
        db_session,
        "bhāviyamāna",
        "prp",
        "prp of bhāviyati",
        "√bhū",
        "√bhū",
        "caus, pass",
        "*e iya",
    )
    name, _row = bucket_of(db_session, "bhāviyamāna")
    assert name == "kind_mismatch"
