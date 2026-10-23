"""Add missing antonyms from existing words with antonyms."""

from json import dump, load

from rich import print
from rich.markup import escape
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def load_antonym_exceptions_dict(pth: ProjectPaths) -> dict[str, list[int]]:
    """Load the source_id -> [excepted dest_id] map."""
    if pth.add_antonyms_sync_dict.exists():
        with open(pth.add_antonyms_sync_dict, encoding="utf-8") as file:
            return load(file)
    else:
        pr.red("error opening antonym dict")
        return {}


def save_antonym_exceptions_dict(
    pth: ProjectPaths, antonym_exceptions_dict: dict[str, list[int]]
) -> None:
    """Save the source_id -> [excepted dest_id] map."""
    with open(pth.add_antonyms_sync_dict, "w", encoding="utf-8") as file:
        dump(antonym_exceptions_dict, file, ensure_ascii=False, indent=2)


def update_exceptions(
    pth: ProjectPaths,
    antonym_exceptions_dict: dict[str, list[int]],
    source_id: int,
    dest_id: int,
) -> None:
    """Except dest_id from being re-flagged as a sync candidate for source_id."""
    # json keys are strings
    source_id_key: str = str(source_id)

    if not antonym_exceptions_dict.get(source_id_key, []):
        antonym_exceptions_dict.update({source_id_key: []})

    if dest_id not in antonym_exceptions_dict[source_id_key]:
        antonym_exceptions_dict[source_id_key].append(dest_id)
        save_antonym_exceptions_dict(pth, antonym_exceptions_dict)


def commit_to_db(dest: DpdHeadword, dest_antonyms: str, db_session: Session) -> None:
    """Write the confirmed antonym string to the destination headword."""
    dest.antonym = dest_antonyms
    db_session.commit()


def antonyms_of(headword: DpdHeadword) -> list[str]:
    """Split the antonym string. Not antonym_list: that cached_property
    keeps its old value after the antonym is changed and committed."""
    return headword.antonym.split(", ") if headword.antonym else []


def make_dest_antonyms(source: DpdHeadword, dest: DpdHeadword) -> list[str]:
    """Build the destination's proposed antonym list, adding the source."""
    dest_antonyms = set(antonyms_of(dest))
    dest_antonyms.add(source.lemma_clean)
    return pali_list_sorter(dest_antonyms)


def main() -> None:
    """Show each antonym linked on one side only and ask what to do."""
    pr.tic()
    pr.yellow_title("find antonyms linked on one side only")

    pth = ProjectPaths()
    antonym_exceptions_dict = load_antonym_exceptions_dict(pth)
    db_session = get_db_session(pth.dpd_db_path)

    sources = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.antonym != "")
        .filter(DpdHeadword.meaning_1 != "")
        .all()
    )
    sources = sorted(sources, key=lambda x: pali_sort_key(x.lemma_1))
    dests = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()
    dests = sorted(dests, key=lambda x: pali_sort_key(x.lemma_1))

    # a dict makes the twin lookup fast
    dest_dict: dict[tuple[str, str], list[DpdHeadword]] = {}
    for dest in dests:
        dest_dict.setdefault((dest.lemma_clean, dest.pos), []).append(dest)

    total = len(sources)

    for counter, source in enumerate(sources, start=1):
        for antonym in antonyms_of(source):
            for dest in dest_dict.get((antonym, source.pos), []):
                if source.lemma_clean in antonyms_of(
                    dest
                ) or dest.id in antonym_exceptions_dict.get(str(source.id), []):
                    continue

                dest_antonyms = make_dest_antonyms(source, dest)
                proposed = ", ".join(dest_antonyms)

                print()
                print("-" * 50)
                print()
                pr.summary("", f"{counter} / {total}")
                pr.summary("dest id", dest.id)
                pr.summary("dest lemma", escape(dest.lemma_1))
                pr.summary("dest pos", escape(dest.pos))
                print(
                    f"[green]dest meaning        [/green][bold magenta]{escape(dest.meaning_combo)}"
                )
                pr.summary("dest root", escape(f"{dest.root_key} {dest.family_root}"))
                print()
                pr.summary("source id", source.id)
                pr.summary("source lemma", escape(source.lemma_1))
                pr.summary("source pos", escape(source.pos))
                print(
                    f"[green]source meaning      [/green][bold magenta]{escape(source.meaning_combo)}"
                )
                pr.summary(
                    "source root", escape(f"{source.root_key} {source.family_root}")
                )
                print()
                print(f"[bold cyan]proposed antonyms:  {escape(proposed)}")
                print()
                print(
                    "[yellow]c[white]ommit [yellow]e[white]xception "
                    "[yellow]p[white]ass [yellow]q[white]uit or Enter to pass: ",
                    end="",
                )
                choice = input().strip()

                if choice == "q":
                    pr.toc()
                    return
                elif choice == "e":
                    update_exceptions(pth, antonym_exceptions_dict, source.id, dest.id)
                    print("[green]exception added")
                elif choice == "c":
                    commit_to_db(dest, proposed, db_session)
                    print("[green]committed")
                elif choice not in ("", "p"):
                    commit_to_db(dest, choice, db_session)
                    print("[green]committed")

    pr.toc()


if __name__ == "__main__":
    main()
