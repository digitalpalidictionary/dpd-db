from db.db_helpers import get_db_session
from tools.printer import printer as pr
from scripts.extractor._dpd_headwords import extract_dpd_headwords
from scripts.extractor._tsv_helpers import get_existing_headwords

def prepare_word_list(source_headwords, pth, output_path, source_name="source"):
    """Find words in source but not in DPD, and not already processed."""
    pr.green("extracting dpd headwords")
    db_session = get_db_session(pth.dpd_db_path)
    dpd_headwords = extract_dpd_headwords(db_session)
    pr.yes(f"{len(dpd_headwords)}")

    pr.green(f"finding words only in {source_name}")
    only_in_source = sorted(source_headwords - dpd_headwords, key=lambda x: x.lower())
    pr.yes(f"{len(only_in_source)}")

    existing = get_existing_headwords(output_path)
    if existing:
        pr.info(f"Found {len(existing)} already processed")
    
    words_to_process = [w for w in only_in_source if w not in existing]
    return words_to_process, existing
