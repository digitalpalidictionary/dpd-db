#!/usr/bin/env python3

"""Push DPD note type templates (front, back, styling) into Anki.

Reads from exporter/anki/templates/ and writes to each note type's Card 1
template. Backs up the existing template + css to a timestamped JSON file
before overwriting. Anki must be closed before running.
"""

import json
from datetime import datetime
from pathlib import Path

from anki.collection import Collection
from anki.errors import DBError

from tools.configger import config_read
from tools.printer import printer as pr


TEMPLATES_DIR = Path("exporter/anki/templates")
BACKUP_DIR = TEMPLATES_DIR / ".backups"
CARD_INDEX = 0

NOTE_TYPE_FILES = {
    "DPD": ("front.html", "back.html", "styling.html"),
    "DPD Root Matrix": (
        "root_matrix_front.html",
        "root_matrix_back.html",
        "root_matrix_styling.html",
    ),
}


def push_note_type(
    col: Collection, note_type: str, front_file: str, back_file: str, css_file: str
) -> None:
    pr.yellow_title(f"pushing templates to '{note_type}'")

    pr.green_tmr("read template files")
    front = (TEMPLATES_DIR / front_file).read_text(encoding="utf-8")
    back = (TEMPLATES_DIR / back_file).read_text(encoding="utf-8")
    styling = (TEMPLATES_DIR / css_file).read_text(encoding="utf-8")
    pr.yes("ok")

    pr.green_tmr(f"find note type '{note_type}'")
    model = col.models.by_name(note_type)
    if model is None:
        pr.no("no")
        pr.red(f"Note type '{note_type}' not found")
        return
    pr.yes("ok")

    pr.green_tmr("backup current template")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{note_type}.json"
    backup_path.write_text(
        json.dumps(
            {
                "qfmt": model["tmpls"][CARD_INDEX]["qfmt"],
                "afmt": model["tmpls"][CARD_INDEX]["afmt"],
                "css": model["css"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    pr.yes("ok")
    pr.white(backup_path.name)

    pr.green_tmr("write new template")
    model["tmpls"][CARD_INDEX]["qfmt"] = front
    model["tmpls"][CARD_INDEX]["afmt"] = back
    model["css"] = styling
    col.models.update_dict(model)
    pr.yes("ok")


def main() -> None:
    pr.tic()

    pr.green_tmr("open anki collection")
    anki_db_path = config_read("anki", "db_path")
    if not anki_db_path:
        pr.no("no")
        pr.red("No anki db_path configured in config.ini [anki].")
        return
    if not Path(anki_db_path).exists():
        pr.no("no")
        pr.red(f"Anki collection not found at: {anki_db_path}")
        pr.red("Check the profile name in config.ini [anki] db_path/backup_path.")
        return
    try:
        col = Collection(anki_db_path)  # type: ignore[arg-type]
    except DBError:
        pr.no("no")
        pr.red("Anki is currently open, close and try again.")
        return
    pr.yes("ok")

    for note_type, (front_file, back_file, css_file) in NOTE_TYPE_FILES.items():
        push_note_type(col, note_type, front_file, back_file, css_file)

    col.close()
    pr.toc()


if __name__ == "__main__":
    main()
