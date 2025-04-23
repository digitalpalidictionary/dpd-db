from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_2col_to_dict, write_tsv_2col_from_dict


class VariantReadingFileManager:
    def __init__(self):
        self.pth = ProjectPaths()
        self.variants_path = self.pth.variant_readings_path
        self.variants_dict: dict[str, str]
        self.variant_headers: list[str]
        self.load()

    def load(self):
        self.variants_dict, self.variant_headers = read_tsv_2col_to_dict(
            self.variants_path
        )

    def update_and_save(self, variant: str, main: str):
        self.load()  # in case the dict has changed elsewhere
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
