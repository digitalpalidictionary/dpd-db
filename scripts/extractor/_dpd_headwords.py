from db.models import DpdHeadword


def extract_dpd_headwords(db_session) -> set[str]:
    """Extract normalized headwords from DPD database."""
    headwords = set()
    db = db_session.query(DpdHeadword).all()
    for i in db:
        # lemma_clean is already normalized in DPD
        headwords.add(i.lemma_clean)
    return headwords
