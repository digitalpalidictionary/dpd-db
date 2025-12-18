# -*- coding: utf-8 -*-
import json
import threading
from pathlib import Path
from typing import Any, Callable, Dict

from gui2.paths import Gui2Paths


class Pass1FileManager:
    def __init__(self, paths: Gui2Paths):
        self.gui2_data_path = paths.gui2_data_path
        self._lock = threading.Lock()

    def _get_filepath(self, book: str) -> Path:
        return self.gui2_data_path / f"pass1_auto_{book}.json"

    def read(self, book: str) -> Dict[str, Any]:
        with self._lock:
            filepath = self._get_filepath(book)
            if filepath.exists():
                with filepath.open("r", encoding="utf-8") as f:
                    try:
                        return json.load(f)
                    except json.JSONDecodeError:
                        return {}
            return {}

    def write(self, book: str, data: Dict[str, Any]):
        with self._lock:
            filepath = self._get_filepath(book)
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def update(
        self, book: str, update_function: Callable[[Dict[str, Any]], Any]
    ) -> Any:
        with self._lock:
            filepath = self._get_filepath(book)
            data = {}
            if filepath.exists():
                try:
                    with filepath.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    # Handle corrupted or empty file
                    pass

            result = update_function(data)

            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return result
