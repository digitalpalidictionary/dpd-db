"""Write DN sutta numbers and their DPD headwords to dn.tsv."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def dn_extractor() -> None:
    """Find headwords whose meaning_1 cites each DN number and write them to dn.tsv."""
    file_path = pth.suttas_dpd_dir / "dn.tsv"
    file_path.write_text("")

    with open(file_path, "a", encoding="utf-8") as f:
        for sutta_no in range(35):
            search_string = rf"\(DN{sutta_no}\b\)"
            db = (
                db_session.query(DpdHeadword)
                .filter(DpdHeadword.meaning_1.regexp_match(search_string))
                .all()
            )
            if db:
                for i in db:
                    print(sutta_no, i.lemma_1)
                    f.write(f"{sutta_no}\t{i.lemma_1}\n")


if __name__ == "__main__":
    dn_extractor()
