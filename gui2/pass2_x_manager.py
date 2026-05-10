from collections import deque

from db.models import DpdHeadword
from gui2.database_manager import DatabaseManager


def filter_query(db: DatabaseManager) -> list[int]:
    """
    Return the list of headword IDs that the X button should iterate over.

    !!! Edit this function to change what the X button does !!!
    """
    rows = (
        db.db_session.query(DpdHeadword.id)
        .filter(
            DpdHeadword.meaning_1 != "",
            DpdHeadword.commentary == "",
            DpdHeadword.source_1 == "-",
        )
        .order_by(DpdHeadword.id)
        .all()
    )
    return [row.id for row in rows]


class Pass2XManager:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._queue: deque[int] = deque()
        self._loaded = False

    def _refill(self) -> None:
        self._queue = deque(filter_query(self._db))
        self._loaded = True

    def get_next(self) -> tuple[int | None, int]:
        if not self._loaded or not self._queue:
            self._refill()
        if not self._queue:
            return None, 0
        next_id = self._queue.popleft()
        return next_id, len(self._queue)
