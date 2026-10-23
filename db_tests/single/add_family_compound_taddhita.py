"""Add missing family compounds and idioms from taddhita words."""

import json
import re
from pathlib import Path

from rich import print
from rich.markup import escape
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyIdiom
from tools.goldendict_tools import open_in_goldendict
from tools.paths import ProjectPaths
from tools.printer import printer as pr

EXCEPTIONS_PATH = Path("db_tests/single/add_family_compound_taddhita.json")


def load_exceptions() -> list[int]:
    """Load the sorted list of excepted headword ids."""
    if not EXCEPTIONS_PATH.exists():
        pr.red(f"no exceptions file found: {EXCEPTIONS_PATH}")
        return []
    with open(EXCEPTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def add_exception(headword_id: int) -> None:
    """Add a headword id to the exceptions file."""
    # another run may have saved the file since this one started
    exceptions = load_exceptions()
    if headword_id not in exceptions:
        exceptions.append(headword_id)
    with open(EXCEPTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(exceptions), f, ensure_ascii=False)


def should_process(i: DpdHeadword, exceptions: set[int]) -> bool:
    """Select taddhita words with a meaning and no family compound."""
    return bool(
        i.meaning_1
        and i.derivative == "taddhita"
        and not i.family_compound
        and int(i.id) not in exceptions
    )


def make_family_compound_and_idiom_set(db_session: Session) -> set[str]:
    """Collect every existing family compound and idiom."""
    fc_set = {i.compound_family for i in db_session.query(FamilyCompound).all()}
    fc_set |= {i.idiom for i in db_session.query(FamilyIdiom).all()}
    return fc_set


def make_family_compound(i: DpdHeadword, fc_set: set[str]) -> str:
    """Propose a family compound.

    1. it's already in family compounds
    2. name of
    3. of|from target in the grammar
    4. as is
    """
    if i.lemma_clean in fc_set:
        return i.lemma_clean
    elif i.meaning_1.startswith("name of"):
        return i.lemma_clean
    else:
        match = re.search(r"(?:of|from)\s+([^,]+)", i.grammar)
        if match:
            return match.group(1)
        else:
            return i.lemma_clean


def commit_to_db(db_session: Session, i: DpdHeadword, family_compound: str) -> None:
    """Write the family compound and idiom to the headword."""
    i.family_compound = family_compound
    i.family_idioms = family_compound
    db_session.commit()


def main() -> None:
    """Show each taddhita word with no family compound and ask what to do."""
    pr.tic()
    pr.yellow_title("find taddhita words with no family compound")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    exceptions = set(load_exceptions())
    items = [
        i for i in db_session.query(DpdHeadword).all() if should_process(i, exceptions)
    ]
    fc_set = make_family_compound_and_idiom_set(db_session)
    total = len(items)
    if not total:
        print("[green]nothing to do")

    for counter, i in enumerate(items, start=1):
        proposed = make_family_compound(i, fc_set)
        if proposed:
            open_in_goldendict(proposed)

        print()
        print("-" * 50)
        print()
        pr.summary("", f"{counter} / {total}")
        pr.summary("id", i.id)
        pr.summary("lemma", escape(i.lemma_1))
        pr.summary("pos", escape(i.pos))
        pr.summary("meaning", escape(i.meaning_1))
        pr.summary("proposed", escape(proposed))
        print()
        print(
            "[yellow]c[white]ommit [yellow]e[white]xception "
            "[yellow]p[white]ass [yellow]q[white]uit or Enter to pass: ",
            end="",
        )
        choice = input().strip()

        if choice == "q":
            break
        elif choice == "e":
            add_exception(i.id)
            print("[green]exception added")
        elif choice == "c" and proposed:
            commit_to_db(db_session, i, proposed)
            print("[green]committed")
        elif choice not in ("", "p", "c"):
            commit_to_db(db_session, i, choice)
            print("[green]committed")

    pr.toc()


if __name__ == "__main__":
    main()
