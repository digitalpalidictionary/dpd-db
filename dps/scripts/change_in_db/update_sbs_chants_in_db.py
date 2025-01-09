#!/usr/bin/env python3

"""Updating sbs_examples chanting book fields according to pali chant names"""

from gui.functions_db_dps import fetch_sbs_index
from db.models import SBS, DpdHeadword
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from sqlalchemy.orm import joinedload



pth: ProjectPaths = ProjectPaths()
dpspth = DPSPaths()

db_session = get_db_session(pth.dpd_db_path)


def update_sbs_chants_in_db(dpspth, db_session, dpd_word):
    """Update SBS chants and chapters directly in the database."""
    for number in range(1, 5):
        chant_field = f"sbs_chant_pali_{number}"
        chant = getattr(dpd_word, chant_field, None)
        
        if chant:
            result = fetch_sbs_index(dpspth, chant)
            if result is not None:
                english, chapter = result
                sbs_word = db_session.query(SBS).filter(SBS.id == dpd_word.id).first()

                old_english = getattr(sbs_word, f"sbs_chant_eng_{number}", None)
                old_chapter = getattr(sbs_word, f"sbs_chapter_{number}", None)

                if old_english != english:
                    print(f"Updating SBS ID {sbs_word.id}:")
                    # debug print for old and new values
                    print(f"  sbs_chant_eng_{number}: {old_english} -> {english}")
                    setattr(sbs_word, f"sbs_chant_eng_{number}", english)

                if old_chapter != chapter:
                    # debug print for old and new values
                    print(f"  sbs_chapter_{number}: {old_chapter} -> {chapter}")
                    setattr(sbs_word, f"sbs_chapter_{number}", chapter)
            else:
                # handle the case when the chant is not found
                error_message = f"chant is not found for {i.sbs.id}"
                print(error_message)
    

results = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).filter(DpdHeadword.sbs).all()
for i in results:
    if i.sbs:
        i: DpdHeadword
        update_sbs_chants_in_db(dpspth, db_session, i.sbs)

# db_session.commit()
# db_session.close()

