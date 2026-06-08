from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.variants.variants_modules import VariantsDict
from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class AddVariantsToDb:
    def __init__(
        self, variants_dict: VariantsDict, db_session: Session | None = None
    ) -> None:
        self.variants_dict = variants_dict
        self.pth = ProjectPaths()

        created_session = db_session is None
        self.db_session = db_session or get_db_session(self.pth.dpd_db_path)

        pr.green_tmr("syncing variant column")
        result = sync_lookup_column(
            self.db_session,
            "variant",
            self.variants_dict,
        )
        if created_session:
            self.db_session.close()
        pr.yes(result.updated + result.inserted)
