"""Find family compounds where nir in construction"""

import re
from sqlalchemy import inspect
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

inspector = inspect(DpdHeadword)
column_names = [column.name for column in inspector.columns]

db = db_session.query(DpdHeadword)

for i in db:
    if (
        re.findall(r"\bnir\b", i.construction_line1)
        and i.meaning_1
        and i.family_compound
        and not re.findall(r"\bnir\b", i.family_compound)
    ):
        print(i.lemma_1)
        i.family_compound = "nir " + i.family_compound
        print(i.family_compound)
        if i.family_idioms:
            i.family_idioms = "nir " + i.family_idioms
            print(i.family_idioms)
        print("--------")


# db_session.commit()
# db_session.close()
