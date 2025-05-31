import json
from pathlib import Path


class Pass2ExceptionsFileManager:
    def __init__(self, toolkit):
        from gui2.toolkit import ToolKit

        self.toolkit: ToolKit = toolkit
        self.exceptions_json_path: Path = toolkit.paths.pass2_exceptions_path
        self.exceptions_list = self.read_exceptions()

    def read_exceptions(self):
        try:
            with open(self.exceptions_json_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def save_exceptions(self):
        with open(self.exceptions_json_path, "w") as file:
            json.dump(
                self.exceptions_list,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def update_exceptions(self, exception: str):
        if exception not in self.exceptions_list and exception.strip():
            self.exceptions_list.append(exception.strip())
        self.save_exceptions()
