"""The missing-words dialog must offer the parts of a freshly saved compound."""

from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, DpdHeadword, Lookup
from gui2.pass2_add_view import Pass2AddView
from gui2.pass2x.in_commentary_exceptions import InCommentaryExceptions


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    db_session.add_all(
        [
            # a finished part
            DpdHeadword(id=1, lemma_1="jappī", meaning_1="whispering", example_1="eg"),
            # a part with a meaning but no example
            DpdHeadword(id=2, lemma_1="upakaṇṇaka", meaning_1="near the ear"),
            # two homonyms: one bare, one finished — counts as finished
            DpdHeadword(id=3, lemma_1="ka 1"),
            DpdHeadword(id=4, lemma_1="ka 2", meaning_1="suffix", example_1="eg"),
        ]
    )
    db_session.commit()
    yield db_session
    db_session.close()


def _view(session: Session, tmp_path: Path, queued: list[str] | None = None):
    view = object.__new__(Pass2AddView)
    view._db = SimpleNamespace(db_session=session)  # pyright: ignore[reportAttributeAccessIssue]
    view._component_ignore = InCommentaryExceptions(tmp_path / "ignore.txt")  # pyright: ignore[reportAttributeAccessIssue]
    view.pass2_eg_manager = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        eg_words_dict={w: {} for w in queued or []}
    )
    return view


def _word(
    construction: str, grammar: str = "adj, comp", pos: str = "adj"
) -> SimpleNamespace:
    return SimpleNamespace(
        lemma_1="upakaṇṇakajappī",
        pos=pos,
        grammar=grammar,
        construction=construction,
        source_1="AN5.111",
        sutta_1="sutta one",
        example_1="eg <b>one</b>",
        source_2="AN5.112",
        sutta_2="sutta two",
        example_2="eg <b>two</b>",
        commentary="",
    )


class TestConstructionParts:
    @pytest.mark.parametrize(
        ("construction", "expected"),
        [
            ("upakaṇṇaka + jappī", ["upakaṇṇaka", "jappī"]),
            ("na > an + acceka + cīvara", ["na", "acceka", "cīvara"]),
            ("ti > te + dasa + *a\ntidasa + *a > telasa", ["ti", "dasa", "tidasa"]),
            ("saṃ + ā + √dhā > (da)h + ita", ["saṃ", "ā", "ita"]),
            ("dhamma + dhamma", ["dhamma"]),
            ("ā + √khā + [y] + ikā", ["ā", "ikā"]),
            ("(n)a + agga + ?? + ka", ["agga", "ka"]),
            ("aḍḍha aḍḍhakāsiya + sīla", ["sīla"]),
            ("", []),
        ],
    )
    def test_parts(self, construction: str, expected: list[str]) -> None:
        assert Pass2AddView._construction_parts(construction) == expected


class TestFindMissingComponentWords:
    def test_part_without_example_is_found_and_finished_part_is_not(
        self, session: Session, tmp_path: Path
    ) -> None:
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(_word("upakaṇṇaka + jappī"))  # pyright: ignore[reportArgumentType]

        assert found == ["upakaṇṇaka"]

    def test_part_missing_from_the_dictionary_is_found(
        self, session: Session, tmp_path: Path
    ) -> None:
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(_word("nonexistent + jappī"))  # pyright: ignore[reportArgumentType]

        assert found == ["nonexistent"]

    def test_bare_numbered_part_is_queued_under_its_numbered_lemma(
        self, session: Session, tmp_path: Path
    ) -> None:
        session.add(DpdHeadword(id=5, lemma_1="dala 1"))
        session.commit()
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(_word("dala + jappī"))  # pyright: ignore[reportArgumentType]

        assert found == ["dala 1"]

    def test_inflected_part_queues_the_bare_headword_behind_it(
        self, session: Session, tmp_path: Path
    ) -> None:
        session.add_all(
            [
                DpdHeadword(id=6, lemma_1="vutta 1", meaning_1="said"),
                DpdHeadword(id=7, lemma_1="vutta 2", meaning_1="x", example_1="eg"),
                Lookup(lookup_key="vuttaṃ", headwords="[6, 7]"),
                Lookup(lookup_key="jappiṃ", headwords="[1]"),
            ]
        )
        session.commit()
        view = _view(session, tmp_path)

        assert view._find_missing_component_words(_word("vuttaṃ + x")) == [  # pyright: ignore[reportArgumentType]
            "vutta 1",
            "x",
        ]
        # every headword behind the form is finished, so nothing is queued
        assert view._find_missing_component_words(_word("jappiṃ + jappī")) == []  # pyright: ignore[reportArgumentType]

    def test_every_bare_homonym_is_queued_even_if_another_is_finished(
        self, session: Session, tmp_path: Path
    ) -> None:
        session.add(DpdHeadword(id=8, lemma_1="ka 3"))
        session.commit()
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(_word("ka + jappī"))  # pyright: ignore[reportArgumentType]

        assert found == ["ka 1", "ka 3"]

    def test_word_that_is_not_a_compound_is_not_checked(
        self, session: Session, tmp_path: Path
    ) -> None:
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(  # pyright: ignore[reportArgumentType]
            _word("upakaṇṇaka + jappī", grammar="adj, in comps")
        )

        assert found == []

    @pytest.mark.parametrize(
        ("pos", "grammar"),
        [("sandhi", "sandhi, pron + ind"), ("idiom", "idiom, masc + pr")],
    )
    def test_sandhi_and_idiom_are_checked_without_comp_in_grammar(
        self, session: Session, tmp_path: Path, pos: str, grammar: str
    ) -> None:
        view = _view(session, tmp_path)

        found = view._find_missing_component_words(  # pyright: ignore[reportArgumentType]
            _word("upakaṇṇaka + [d] + jappī", grammar=grammar, pos=pos)
        )

        assert found == ["upakaṇṇaka"]

    def test_ignored_and_queued_parts_are_skipped(
        self, session: Session, tmp_path: Path
    ) -> None:
        (tmp_path / "ignore.txt").write_text("upakaṇṇaka\n", encoding="utf-8")
        view = _view(session, tmp_path)
        assert view._find_missing_component_words(_word("upakaṇṇaka + x")) == ["x"]  # pyright: ignore[reportArgumentType]

        queued_view = _view(session, tmp_path, queued=["x 1"])
        assert queued_view._find_missing_component_words(_word("upakaṇṇaka + x")) == []  # pyright: ignore[reportArgumentType]


class TestPartsSection:
    def test_parts_are_the_first_section_with_both_examples(
        self, session: Session, tmp_path: Path
    ) -> None:
        view = _view(session, tmp_path)

        sections = view._find_missing_eg_words(_word("upakaṇṇaka + jappī"))  # pyright: ignore[reportArgumentType]

        label, words = sections[0]
        assert label == "PARTS: upakaṇṇaka + jappī"
        assert list(words) == ["upakaṇṇaka"]
        assert words["upakaṇṇaka"] == {
            "source_1": "AN5.111",
            "sutta_1": "sutta one",
            "example_1": "eg one",
            "source_2": "AN5.112",
            "sutta_2": "sutta two",
            "example_2": "eg two",
        }
