import csv

import requests
from sqlalchemy import inspect

from db.db_helpers import create_tables, get_db_session
from db.models import SuttaInfo
from db.suttas.dv_catalogue_suttas import update_dv_fields_in_db
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def download_tsv_from_sheets(pth: ProjectPaths) -> bool:
    """Download the sutta TSV; return True if the data changed (rebuild needed),
    False if the download failed or the content is unchanged."""
    pr.green_tmr("downloading tsv from google sheets")
    url = "https://docs.google.com/spreadsheets/d/1sR8NT204STTwOoDrr9GBjhXVYEn0qqZTxgjoLKMmaaE/export?format=tsv"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        pr.yes("ok")
    except Exception:
        pr.no("failed")
        return False

    tsv_path = pth.sutta_info_tsv_path
    if tsv_path.exists() and tsv_path.read_bytes() == response.content:
        pr.green_tmr("tsv unchanged")
        pr.yes("skip")
        return False

    pr.green_tmr("saving to tsv")
    try:
        tsv_path.write_bytes(response.content)
        pr.yes("ok")
    except Exception as e:
        pr.no("failed")
        pr.red(f"save failed: {e}")
        return False

    return True


def _prepare_sutta_row(
    row_data: dict[str, str], model_columns: set[str]
) -> dict[str, str]:
    filtered_data = {k: v for k, v in row_data.items() if k in model_columns}

    # Convert specified codes to uppercase
    for col in ("cst_code", "dpr_code", "sc_code"):
        if col in filtered_data:
            filtered_data[col] = filtered_data[col].upper()

    for col in ("cst_m_page", "cst_v_page", "cst_p_page", "cst_t_page"):
        if col in filtered_data and filtered_data[col]:
            value = filtered_data[col]
            if "." in value:
                book, page = value.split(".", 1)
                filtered_data[col] = f"{book}.{page.ljust(4, '0')}"

    return filtered_data


def _sutta_info_is_populated(pth: ProjectPaths) -> bool:
    """True if the sutta_info table exists and has at least one row."""
    db_session = get_db_session(pth.dpd_db_path)
    try:
        engine = db_session.get_bind()
        if not inspect(engine).has_table(SuttaInfo.__tablename__):
            return False
        return db_session.query(SuttaInfo).first() is not None
    finally:
        db_session.close()


def update_sutta_info_table(pth: ProjectPaths) -> None:
    db_session = get_db_session(pth.dpd_db_path)
    engine = db_session.get_bind()

    pr.green_tmr("dropping old sutta_info table")
    try:
        SuttaInfo.__table__.drop(engine, checkfirst=True)  # type: ignore[attr-defined]
        pr.yes("ok")
    except Exception as e:
        pr.no("skip")
        pr.amber(f"could not drop table (might be ok): {e}")

    pr.green_tmr("creating sutta_info table")
    try:
        create_tables(pth.dpd_db_path)
        pr.yes("ok")
    except Exception as e:
        pr.no("failed")
        pr.red(f"failed to create tables: {e}")
        db_session.close()
        return

    pr.green_tmr("preparing data")
    suttas_to_add: list[dict[str, str]] = []
    # TODO: The source TSV has duplicate sutta names. This script currently
    # skips duplicates and only adds the first instance. The duplicates
    # should be cleaned in the source data.
    seen_dpd_suttas: set[str] = set()
    duplicates: list[str] = []
    model_columns = {c.name for c in SuttaInfo.__table__.columns}  # type: ignore[attr-defined]

    try:
        with pth.sutta_info_tsv_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)

            for row in reader:
                row_data = dict(zip(header, row))
                dpd_sutta_key = row_data.get("dpd_sutta")
                if not dpd_sutta_key:
                    continue
                if dpd_sutta_key in seen_dpd_suttas:
                    duplicates.append(dpd_sutta_key)
                    continue
                seen_dpd_suttas.add(dpd_sutta_key)
                suttas_to_add.append(_prepare_sutta_row(row_data, model_columns))
        pr.yes("ok")
    except Exception as e:
        pr.no("failed")
        pr.red(f"failed reading tsv: {e}")
        db_session.close()
        return

    if duplicates:
        pr.red("Duplicate dpd_sutta names found:")
        for d in sorted(set(duplicates)):
            pr.red(d)

    pr.green_tmr(f"adding {len(suttas_to_add)} suttas to db")
    try:
        if suttas_to_add:
            db_session.bulk_insert_mappings(SuttaInfo, suttas_to_add)  # type: ignore[arg-type]
        db_session.commit()
        pr.yes("ok")
    except Exception as e:
        pr.no("failed")
        pr.red(f"failed adding to db: {e}")
        db_session.rollback()
    finally:
        db_session.close()


def main() -> None:
    pr.tic()
    pr.yellow_title("update sutta_info table")
    if config_read("generate", "suttas", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return
    pth = ProjectPaths()
    data_changed = download_tsv_from_sheets(pth)
    if data_changed or not _sutta_info_is_populated(pth):
        update_sutta_info_table(pth)
    else:
        pr.green("sutta data unchanged — skipping table rebuild")
    update_dv_fields_in_db(pth)
    pr.toc()


if __name__ == "__main__":
    main()
