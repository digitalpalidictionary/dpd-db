#!/usr/bin/env python3

"""Swap the sutta examples"""

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths


def main():
    
    print("[bright_yellow]swap examples")
    headword = None

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    while headword != "x":
        print("[green]enter the headword or x to exit: ", end="")
        headword = input()

        if headword == "x":
            break

        result = db_session \
            .query(DpdHeadwords) \
            .filter_by(lemma_1=headword) \
            .first()
        
        if result:
            if result.example_1 and result.example_2:
                print("[bright_yellow]before")
                printer(result)

                # save example 1
                example_1_source = result.source_1
                example_1_sutta = result.sutta_1
                example_1_example = result.example_1

                # move example 2 to 1
                result.source_1 = result.source_2
                result.sutta_1 = result.sutta_2
                result.example_1 = result.example_2

                # move example 1 to 2
                result.source_2 = example_1_source
                result.sutta_2 = example_1_sutta
                result.example_2 = example_1_example

                print("[bright_yellow]after")
                printer(result)

                print("[green]commit? [lightgreen]y/n ", end="")
                route = input()
                if route == "y":
                    db_session.commit()
                    print("[red]committed to db\n")
                else:
                    print("[red]NOT committed to db")

            else:
                print("[red]ERROR: there are not two examples")
        else:
            print("[red]ERROR: headword not found")


def printer(hw: DpdHeadwords) -> None:

    print(f"[chartreuse3]{hw.source_1} [sea_green3]{hw.sutta_1}")
    print(f"[aquamarine3]{hw.example_1}")
    print()
    print(f"[chartreuse3]{hw.source_2} [sea_green3]{hw.sutta_2}")
    print(f"[aquamarine3]{hw.example_2}")
    print()

if __name__ == "__main__":
    main()
