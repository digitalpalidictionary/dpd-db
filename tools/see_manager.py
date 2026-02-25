# -*- coding: utf-8 -*-
"""Manager for handling "see" entries that point unusual word forms to headwords.

This module provides a SeeManager class for loading and managing see.tsv,
which stores one-to-one mappings of unusual word forms to their correct headwords.
"""

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_2col_to_dict, write_tsv_2col_from_dict


class SeeManager:
    """Manages see entries from see.tsv.

    Each entry maps an unusual word form to the headword the user should
    consult instead. Provides load, update_and_save, and get_see_dict methods.

    Attributes:
        see_dict: Dictionary mapping unusual_form -> headword
        headers: List of column headers from the TSV file
    """

    def __init__(self, pth: ProjectPaths | None = None) -> None:
        """Initialize the SeeManager.

        Args:
            pth: Optional ProjectPaths instance. If not provided, creates default.
        """
        if pth is None:
            pth = ProjectPaths()
        self.pth = pth
        self.see_dict: dict[str, str] = {}
        self.headers: list[str] = []
        self._load()

    def _load(self) -> None:
        """Load see entries from the TSV file."""
        result = read_tsv_2col_to_dict(self.pth.see_path)
        self.see_dict = result.data
        self.headers = result.headers if result.headers else ["see", "headword"]

    def load(self) -> None:
        """Reload see entries from the TSV file.

        Use this method if the file has been modified externally.
        """
        self._load()

    def update_and_save(self, see: str, headword: str) -> None:
        """Add or update a see entry and persist to TSV.

        Args:
            see: The unusual word form to map from.
            headword: The correct headword to point to.
        """
        self.see_dict[see] = headword
        write_tsv_2col_from_dict(self.pth.see_path, self.see_dict, self.headers)

    def get_see_dict(self) -> dict[str, str]:
        """Get a copy of the full see dictionary.

        Returns:
            Dictionary mapping unusual_form -> headword.
        """
        return self.see_dict.copy()


if __name__ == "__main__":
    sm = SeeManager()
    print(f"Loaded {len(sm.get_see_dict())} see entries")
