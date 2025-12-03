import csv

import requests
from sqlalchemy import inspect

from db.db_helpers import create_tables, get_db_session
from db.models import SuttaInfo
from db.suttas.dv_catalogue_suttas import update_dv_fields_in_db
from tools.paths import ProjectPaths
from tools.printer import printer as pr

def download_tsv_from_sheets(pth: ProjectPaths):
    pr.green("downloading tsv from google sheets")
    try:
        url = "https://docs.google.com/spreadsheets/d/1sR8NT204STTwOoDrr9GBjhXVYEn0qqZTxgjoLKMmaaE/export?format=tsv"
        response = requests.get(url, timeout=10)
        pr.yes("ok")
    except Exception:
        pr.no("failed")
        return

    pr.green("saving to tsv")
    try:
        with open(pth.sutta_info_tsv_path, "wb") as f:
            f.write(response.content)
        pr.yes("ok")
    except Exception as e:
        pr.no(f"failed: {e}")


def update_sutta_info_table(pth: ProjectPaths):
    db_session = get_db_session(pth.dpd_db_path)
    engine = db_session.get_bind()

    pr.green("dropping old sutta_info table")
    try:
        SuttaInfo.__table__.drop(engine, checkfirst=True)
        pr.yes("ok")
    except Exception as e:
        pr.no(f"could not drop table (might be ok): {e}")

    pr.green("creating sutta_info table")
    try:
        create_tables(pth.dpd_db_path)
        pr.yes("ok")
    except Exception as e:
        pr.no(f"failed to create tables: {e}")
        db_session.close()
        return

    pr.green("preparing data")
    suttas_to_add = []
    # TODO: The source TSV has duplicate sutta names. This script currently
    # skips duplicates and only adds the first instance. The duplicates
    # should be cleaned in the source data.
    seen_dpd_suttas = set()
    duplicates = []

    try:
        with open(pth.sutta_info_tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)

            inspector = inspect(SuttaInfo)
            model_columns = {c.name for c in inspector.columns}

            for row in reader:
                row_data = dict(zip(header, row))

                dpd_sutta_key = row_data.get("dpd_sutta")

                if not dpd_sutta_key:
                    continue

                if dpd_sutta_key in seen_dpd_suttas:
                    duplicates.append(dpd_sutta_key)
                    continue

                seen_dpd_suttas.add(dpd_sutta_key)

                filtered_data = {
                    k: v for k, v in row_data.items() if k in model_columns
                }

                # Convert specified codes to uppercase
                if "cst_code" in filtered_data:
                    filtered_data["cst_code"] = filtered_data["cst_code"].upper()
                if "dpr_code" in filtered_data:
                    filtered_data["dpr_code"] = filtered_data["dpr_code"].upper()
                if "sc_code" in filtered_data:
                    filtered_data["sc_code"] = filtered_data["sc_code"].upper()

                # Format page numbers to have 4 decimal places
                for col in ["cst_m_page", "cst_v_page", "cst_p_page", "cst_t_page"]:
                    if col in filtered_data and filtered_data[col]:
                        value = filtered_data[col]
                        if "." in value:
                            book, page = value.split(".", 1)
                            filtered_data[col] = f"{book}.{page.ljust(4, '0')}"

                suttas_to_add.append(filtered_data)
        pr.yes("ok")
    except Exception as e:
        pr.no(f"failed reading tsv: {e}")
        db_session.close()
        return

    if duplicates:
        pr.red("Duplicate dpd_sutta names found:")
        for d in sorted(list(set(duplicates))):
            pr.red(d)

    pr.green(f"adding {len(suttas_to_add)} suttas to db")
    try:
        if suttas_to_add:
            db_session.bulk_insert_mappings(SuttaInfo, suttas_to_add)

        db_session.commit()
        pr.yes("ok")
    except Exception as e:
        pr.no(f"failed adding to db: {e}")
        db_session.rollback()
    finally:
        db_session.close()


def main():
    pr.tic()
    pr.title("update sutta_info table")
    pth = ProjectPaths()
    download_tsv_from_sheets(pth)
    update_sutta_info_table(pth)
    update_dv_fields_in_db(pth)
    pr.toc()


if __name__ == "__main__":
    main()
