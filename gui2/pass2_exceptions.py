import json
from pathlib import Path

from tools.pali_sort_key import pali_list_sorter


class Pass2ExceptionsFileManager:
    def __init__(self, toolkit):
        from gui2.toolkit import ToolKit

        self.toolkit: ToolKit = toolkit
        self.exceptions_json_path: Path = toolkit.paths.pass2_exceptions_path
        self.exceptions_set: set[str]
        self.read_exceptions()

    def read_exceptions(self):
        try:
            with open(self.exceptions_json_path, "r", encoding="utf-8") as file:
                self.exceptions_set = set(json.load(file))
        except FileNotFoundError:
            self.exceptions_set = set()

    def save_exceptions(self):
        with open(self.exceptions_json_path, "w", encoding="utf-8") as file:
            json.dump(
                pali_list_sorter(self.exceptions_set),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def update_exceptions(self, exception: str):
        if exception and exception.strip() and exception not in self.exceptions_set:
            self.exceptions_set.add(exception.strip())
            self.save_exceptions()
