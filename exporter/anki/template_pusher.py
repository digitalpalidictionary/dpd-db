#!/usr/bin/env python3

"""Push DPD note type templates (front, back, styling) into Anki.

Reads from exporter/anki/templates/ and writes to the DPD note type's
Card 1 template. Backs up the existing template + css to a timestamped
JSON file before overwriting. Anki must be closed before running.
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
NOTE_TYPE = "DPD"
CARD_INDEX = 0


def main() -> None:
    pr.tic()
    pr.yellow_title(f"pushing templates to '{NOTE_TYPE}'")

    pr.green_tmr("read template files")
    front = (TEMPLATES_DIR / "front.html").read_text(encoding="utf-8")
    back = (TEMPLATES_DIR / "back.html").read_text(encoding="utf-8")
    styling = (TEMPLATES_DIR / "styling.html").read_text(encoding="utf-8")
    pr.yes("ok")

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

    pr.green_tmr(f"find note type '{NOTE_TYPE}'")
    model = col.models.by_name(NOTE_TYPE)
    if model is None:
        pr.no("no")
        pr.red(f"Note type '{NOTE_TYPE}' not found")
        col.close()
        return
    pr.yes("ok")

    pr.green_tmr("backup current template")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{NOTE_TYPE}.json"
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
    col.close()
    pr.yes("ok")

    pr.toc()


if __name__ == "__main__":
    main()
