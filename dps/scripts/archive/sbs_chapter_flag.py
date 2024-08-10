#!/usr/bin/env python3

"""making sbs_chapter_flag 1 if any of sbs_chapter is not empty"""

from rich.console import Console

from db.db_helpers import get_db_session
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths

from sqlalchemy import text

console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]making sbs_chapter_flag")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)


    # SQL query to update sbs_chapter_flag based on sbs_chapter_{i} columns
    update_query = text("""
        UPDATE sbs
        SET sbs_chapter_flag =
            CASE
                WHEN sbs_chapter_1 IS NOT NULL AND TRIM(sbs_chapter_1) <> '' THEN 1
                WHEN sbs_chapter_2 IS NOT NULL AND TRIM(sbs_chapter_2) <> '' THEN 1
                WHEN sbs_chapter_3 IS NOT NULL AND TRIM(sbs_chapter_3) <> '' THEN 1
                WHEN sbs_chapter_4 IS NOT NULL AND TRIM(sbs_chapter_4) <> '' THEN 1
                ELSE ""
            END
    """)

    # Execute the update query
    db_session.execute(update_query)

    # Commit the changes
    db_session.commit()

    # Count the total number of sbs_chapter_flag values that are equal to 1
    count_query = text("""
        SELECT COUNT(*) FROM sbs WHERE sbs_chapter_flag = 1
    """)
    result = db_session.execute(count_query)
    total_count = result.scalar()

    # Print the total count
    console.print(f"[bold blue]Total number with sbs_chapter_flag: {total_count}")

    # Close the session
    db_session.close()

    toc()


if __name__ == "__main__":
    main()
