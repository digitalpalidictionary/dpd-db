"""Mock anki system package so tests can import anki_updater without Anki installed."""

import sys
from unittest.mock import MagicMock

for _mod in ["anki", "anki.collection", "anki.errors", "anki.notes", "anki.cards"]:
    sys.modules.setdefault(_mod, MagicMock())
