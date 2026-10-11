from pathlib import Path

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_2col_to_dict, write_tsv_2col_from_dict


class SpellingMistakesFileManager:
    def __init__(self, own_path: Path | None = None):
        """own_path is a contributor's own file: read on top of the shared
        file, and the only file written. None means the shared file alone."""
        self.own_path = own_path
        self.pth = ProjectPaths()
        self.spelling_mistakes_path = self.pth.spelling_mistakes_path
        self.spelling_mistakes_dict: dict[str, str]
        self.spelling_headers: list[str]
        self.load()

    def load(self):
        self.spelling_mistakes_dict, self.spelling_headers = read_tsv_2col_to_dict(
            self.spelling_mistakes_path
        )
        if self.own_path:
            self.spelling_mistakes_dict.update(
                read_tsv_2col_to_dict(self.own_path).data
            )

    def update_and_save(self, wrong_spelling: str, correct_spelling: str):
        self.load()  # in case the dict has changed elsewhere
        if self.own_path:
            own = read_tsv_2col_to_dict(self.own_path).data
            own[wrong_spelling] = correct_spelling
            write_tsv_2col_from_dict(self.own_path, own, self.spelling_headers)
            self.spelling_mistakes_dict[wrong_spelling] = correct_spelling
            return
        self.spelling_mistakes_dict[wrong_spelling] = correct_spelling
        write_tsv_2col_from_dict(
            self.spelling_mistakes_path,
            self.spelling_mistakes_dict,
            self.spelling_headers,
        )

    def get_spelling_mistakes(self) -> dict[str, str]:
        return self.spelling_mistakes_dict.copy()


if __name__ == "__main__":
    from rich import print

    # Example usage
    manager = SpellingMistakesFileManager()
    print("Current spelling mistakes:", manager.get_spelling_mistakes())
    print(manager.spelling_headers)
    # manager.update_and_save("test_variant", "test_main")
    # print("Updated variants:", manager.get_spelling_mistakes())
