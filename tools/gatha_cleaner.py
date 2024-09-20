#!/usr/bin/env python3

"""Clean up gatha by adding fixing punctation and addings line breaks."""

import re
from tools.paths import ProjectPaths


def main():
    from rich import print
    from db.db_helpers import get_db_session
    from db.models import DpdHeadword
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 0

    for i in db:
        if i.example_2 is None:
            continue
        example = i.example_2
        if (
            "\n" in example and
            re.findall(r"(,.+\.|,.+,)", example)
        ):
            print(f"[green]{i.lemma_1}")
            example = clean_gatha(example)
            i.example_2 = example
            print(i.example_2)
            print()
            count += 1

    print(count)
    db_session.commit()
    db_session.close()


def clean_gatha(text):
    # replace fullstop newline with comma newline
    if ".\n" in text:
        text = re.sub(r"\.\n", ",\n", text)

    # replace fullstop space newline with comma newline
    if ". \n" in text:
        text = re.sub(r"\. \n", ",\n", text)

    # replace comma space newline with comma newline
    if ", \n" in text:
        text = re.sub(r", \n", ",\n", text)

    # replace commas with line breaks
    text = re.sub(", ", ",\n", text)

    return text


if __name__ == "__main__":
    main()
