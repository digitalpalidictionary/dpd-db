from pathlib import Path

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_2col_to_dict, write_tsv_2col_from_dict
from tools.variants_manager import VariantManager


class VariantReadingFileManager(VariantManager):
    def __init__(self, own_path: Path | None = None):
        """own_path is a contributor's own file: read on top of the shared
        file, and the only file written. None means the shared file alone."""
        self.own_path = own_path
        super().__init__()
        self.pth = ProjectPaths()
        self.variants_path = self.pth.variant_readings_path
        self.variant_headers: list[str] = self.headers

    def _load(self) -> None:
        super()._load()
        if self.own_path:
            self.variants_dict.update(read_tsv_2col_to_dict(self.own_path).data)

    def load(self):
        self._load()
        self.variant_headers = self.headers

    def update_and_save(self, variant: str, main: str):
        self.load()
        if self.own_path:
            own = read_tsv_2col_to_dict(self.own_path).data
            own[variant] = main
            write_tsv_2col_from_dict(self.own_path, own, self.variant_headers)
            self.variants_dict[variant] = main
            return
        self.variants_dict[variant] = main
        write_tsv_2col_from_dict(
            self.variants_path, self.variants_dict, self.variant_headers
        )

    def get_variants(self) -> dict[str, str]:
        return self.variants_dict.copy()


if __name__ == "__main__":
    from rich import print

    # Example usage
    manager = VariantReadingFileManager()
    print("Current variants:", manager.get_variants())
    print(manager.variant_headers)
    # manager.update_and_save("test_variant", "test_main")
    # print("Updated variants:", manager.get_variants())
