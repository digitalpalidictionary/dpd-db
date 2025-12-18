from pathlib import Path
import requests
import pandas as pd

from db.db_helpers import get_db_session
from db.models import SuttaInfo
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def download_dv_catalogue(filepath: Path) -> bool:
    """Download DV Catalogue TSV file from GitHub."""
    url = "https://raw.githubusercontent.com/dhammavinaya-tools/dhamma-vinaya-catalogue/main/DV_Catalogue5_suttas.tsv"
    try:
        pr.green("downloading dv catalogue")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content = response.content.replace(b"\r\n", b"\n")
        with open(filepath, "wb") as f:
            f.write(content)
        pr.yes("ok")
        return True
    except Exception as e:
        pr.no("failed")
        pr.red(str(e))
        return False


def read_dv_catalogue(pth: ProjectPaths) -> dict[str, dict[str, str]]:
    """Read DV Catalogue TSV file and convert to dict with SUTTACODE as key.

    Always attempts to download fresh file first.
    Falls back to local file if download fails.
    """
    tsv_path = pth.dv_catalogue_suttas_tsv_path

    # Always try to download fresh
    if not download_dv_catalogue(tsv_path):
        pr.red("using local file if available")

    if not tsv_path.exists():
        pr.red("no local file available")
        return {}

    # Read TSV file
    try:
        pr.green("reading dv sutta catalogue")
        df = pd.read_csv(tsv_path, sep="\t")

    except Exception as e:
        pr.no("failed")
        pr.red(str(e))
        return {}

    # Convert column names to lowercase
    df.columns = [str(col).lower() for col in df.columns]

    # Remove duplicates by keeping first occurrence of each SUTTACODE
    if "suttacode" in df.columns:
        df = df.drop_duplicates(subset=["suttacode"], keep="first")

        # Set SUTTACODE as index and convert to dict
        df.set_index("suttacode", inplace=True)
        catalogue_dict = df.to_dict("index")
        pr.yes(len(catalogue_dict))
        return catalogue_dict  # type: ignore[return-value]
    else:
        pr.red("suttacode column not found in TSV")
        return {}


def get_dv_column_mapping() -> dict[str, str]:
    """Map Excel column names to database dv_ field names."""
    return {
        "pts": "dv_pts",
        "main_theme": "dv_main_theme",
        "subtopic": "dv_subtopic",
        "summary": "dv_summary",
        "key_excerpt1": "dv_key_excerpt1",
        "key_excerpt2": "dv_key_excerpt2",
        "similes": "dv_similes",
        "stage": "dv_stage",
        "training": "dv_training",
        "aspect": "dv_aspect",
        "teacher": "dv_teacher",
        "audience": "dv_audience",
        "method": "dv_method",
        "length": "dv_length",
        "prominence": "dv_prominence",
        "nikayas_parallels": "dv_nikayas_parallels",
        "āgamas_parallels": "dv_āgamas_parallels",
        "taisho_parallels": "dv_taisho_parallels",
        "sanskrit_parallels": "dv_sanskrit_parallels",
        "vinaya_parallels": "dv_vinaya_parallels",
        "others_parallels": "dv_others_parallels",
        "partial_parallels_nā": "dv_partial_parallels_nā",
        "partial_parallels_all": "dv_partial_parallels_all",
        "suggested_suttas": "dv_suggested_suttas",
    }


def update_dv_fields_in_db(pth: ProjectPaths):
    """Update DV catalogue fields in existing SuttaInfo records."""
    db_session = get_db_session(pth.dpd_db_path)

    try:
        dv_catalogue = read_dv_catalogue(pth)
    except Exception as e:
        pr.no(f"failed to read DV catalogue: {e}")
        db_session.close()
        return

    pr.green("updating dv sutta in db")
    try:
        dv_mapping = get_dv_column_mapping()
        updated_count = 0
        not_found_count = 0

        # Get all SuttaInfo records that have an sc_code
        all_sutta_records = (
            db_session.query(SuttaInfo).filter(SuttaInfo.sc_code.isnot(None)).all()
        )

        for sutta_record in all_sutta_records:
            sc_code = sutta_record.sc_code

            # Check if this sc_code exists in the DV catalogue
            if sc_code in dv_catalogue:
                dv_data = dv_catalogue[sc_code]

                # Update fields that exist in both the DV catalogue and our mapping
                for excel_col, db_field in dv_mapping.items():
                    if excel_col in dv_data and pd.notna(dv_data[excel_col]):
                        # Only update if the field exists in the SuttaInfo model
                        if hasattr(sutta_record, db_field):
                            setattr(sutta_record, db_field, str(dv_data[excel_col]))

                updated_count += 1
            else:
                not_found_count += 1

        db_session.commit()
        pr.yes(updated_count)
        if not_found_count:
            pr.red(f"{not_found_count} sc_codes not found in DV catalogue")

    except Exception as e:
        pr.no(f"failed to update DV fields: {e}")
        db_session.rollback()
    finally:
        db_session.close()


def main():
    pth = ProjectPaths()

    catalogue_dict = read_dv_catalogue(pth)
    pr.green(f"Loaded {len(catalogue_dict)} entries")
    if catalogue_dict:
        first_key = list(catalogue_dict.keys())[0]
        pr.green(f"Sample entry ({first_key}):")
        pr.green(str(catalogue_dict[first_key]))


if __name__ == "__main__":
    main()
