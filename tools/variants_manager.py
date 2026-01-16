# -*- coding: utf-8 -*-
"""Generalized variant manager for handling manual variant readings.

This module provides a reusable VariantManager class that can be used
by both GUI2 and webapp to manage manual variant readings from TSV files.
"""


from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_2col_to_dict


class VariantManager:
    """Manages manual variant readings from variant_readings.tsv.

    This class provides a generalized interface for loading and querying
    variant readings from the TSV file. It can be used by both GUI2 and
    webapp components.

    Attributes:
        variants_dict: Dictionary mapping variant -> main form
        headers: List of column headers from the TSV file
    """

    def __init__(self, pth: ProjectPaths | None = None) -> None:
        """Initialize the VariantManager.

        Args:
            pth: Optional ProjectPaths instance. If not provided, creates default.
        """
        if pth is None:
            pth = ProjectPaths()
        self.pth = pth
        self.variants_dict: dict[str, str]
        self.headers: list[str]
        self._load()

    def _load(self) -> None:
        """Load the variant readings from TSV file."""
        result = read_tsv_2col_to_dict(self.pth.variant_readings_path)
        self.variants_dict = result.data
        self.headers = result.headers

    def load(self) -> None:
        """Reload the variant readings from TSV file.

        Use this method if the file has been modified externally.
        """
        self._load()

    def get_all(self) -> dict[str, str]:
        """Get a copy of the full variants dictionary.

        Returns:
            Dictionary mapping variant -> main form.
        """
        return self.variants_dict.copy()

    def get_variants(self) -> dict[str, str]:
        """Get a copy of the variants dictionary (alias for get_all).

        Returns:
            Dictionary mapping variant -> main form.
        """
        return self.get_all()

    def get_main(self, variant: str) -> str | None:
        """Forward lookup: find main form by variant.

        Args:
            variant: The variant spelling to look up.

        Returns:
            The main form if found, None otherwise.
        """
        return self.variants_dict.get(variant)

    def get_variant(self, main_form: str) -> list[str]:
        """Reverse lookup: find all variants for a given main form.

        Args:
            main_form: The main form to find variants for.

        Returns:
            List of variant spellings that map to the main form.
        """
        return [variant for variant, main in self.variants_dict.items() if main == main_form]


if __name__ == "__main__":
    vm = VariantManager()
    print(f"Loaded {len(vm.get_all())} variant readings")
    print(f"Sample: celaṇḍukena -> {vm.get_main('celaṇḍukena')}")
