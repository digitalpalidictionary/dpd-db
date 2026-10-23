"""Add missing antonyms to negative Pāḷi words."""

import json
from pathlib import Path

from rich import print
from rich.markup import escape
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.negative_to_positive import make_positive
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

EXCEPTIONS_PATH = Path("db_tests/single/add_antonyms.json")


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
    """Select negative headwords with a meaning and no antonym."""
    return bool(i.meaning_1 and i.neg and not i.antonym and int(i.id) not in exceptions)


def make_all_words_set(pth: ProjectPaths) -> set[str]:
    """Collect the words of the CST, BJT, SC and SYA word lists."""
    all_words: set[str] = set()
    for wordlist in [
        pth.cst_wordlist,
        pth.bjt_wordlist,
        pth.sc_wordlist,
        pth.sya_wordlist,
    ]:
        with open(wordlist, encoding="utf-8") as f:
            all_words.update(json.load(f))
    return all_words


def matching_words(all_words: set[str], start: str) -> str:
    """List the 20 shortest words that start with the proposed antonym."""
    words = sorted((w for w in all_words if w.startswith(start)), key=len)[:20]
    return ", ".join(words) if words else "-"


def commit_to_db(db_session: Session, i: DpdHeadword, antonym: str) -> None:
    """Write the antonym to the headword."""
    i.antonym = antonym
    db_session.commit()


def main() -> None:
    """Show each negative word with no antonym and ask what to do."""
    pr.tic()
    pr.yellow_title("find negative words with no antonym")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = sorted(
        db_session.query(DpdHeadword).all(), key=lambda x: pali_sort_key(x.lemma_1)
    )
    exceptions = set(load_exceptions())
    items = [i for i in db if should_process(i, exceptions)]
    all_words = make_all_words_set(pth)
    total = len(items)
    if not total:
        print("[green]nothing to do")

    for counter, i in enumerate(items, start=1):
        proposed = make_positive(i)
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
        pr.summary("words", escape(matching_words(all_words, proposed)))
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
