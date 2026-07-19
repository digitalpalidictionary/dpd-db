# -*- coding: utf-8 -*-
import json
from pathlib import Path

from db.models import DpdHeadword
from tools.printer import printer as pr

CorrectionsDict = dict[str, dict[str, str | int]]


class CorrectionsManager:
    from gui2.toolkit import ToolKit

    def __init__(self, toolkit: ToolKit):
        self.paths = toolkit.paths
        self.corrections_path = self.paths.corrections_path
        self._origin: dict[str, Path] = {}
        self.corrections_dict: CorrectionsDict = self.load_corrections()

    def load_corrections(self) -> CorrectionsDict:
        """Primary user: non-destructively merge all contributor files.
        Contributor (non-primary) user: load only their own file.
        """
        merged: CorrectionsDict = {}
        self._origin = {}

        if self.corrections_path.name == "corrections.json":
            data_dir = self.corrections_path.parent
            for contrib_file in sorted(data_dir.glob("corrections_*.json")):
                if "corrections_added" in contrib_file.name:
                    continue
                try:
                    with open(contrib_file, encoding="utf-8") as f:
                        contrib_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
                for key, value in contrib_data.items():
                    if key in merged:
                        pr.red(
                            f"duplicate correction key {key} in {contrib_file.name}; "
                            f"overriding previous origin {self._origin[key].name}"
                        )
                    merged[key] = value
                    self._origin[key] = contrib_file
        else:
            try:
                with open(self.corrections_path, encoding="utf-8") as f:
                    merged = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        return merged

    def _save_dict(self, data: CorrectionsDict) -> None:
        with open(self.corrections_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_corrections(self) -> None:
        self._save_dict(self.corrections_dict)

    def update_corrections(self, word: DpdHeadword, comment: str) -> None:
        word_dict = {k: v for k, v in vars(word).items() if not k.startswith("_")}
        word_dict["comment"] = comment
        # Key = "{username}_{id}": unique across contributors (username) and
        # stable per word (id + dedup), so re-correcting the same word overwrites
        # its one live entry (latest wins) instead of piling up duplicates the
        # reviewer would process repeatedly. Reuse an existing entry's key even
        # if it predates this scheme (e.g. an old uuid key).
        key = self._key_for_id(word.id) or f"{self._username()}_{word.id}"
        self.corrections_dict[key] = word_dict
        self.save_corrections()

    def _username(self) -> str:
        """The contributor this file belongs to, from its name
        (corrections_{username}.json). Primary user's corrections.json → '1'."""
        stem = self.corrections_path.stem
        prefix = "corrections_"
        return stem[len(prefix) :] if stem.startswith(prefix) else "1"

    def _key_for_id(self, id_no: int) -> str | None:
        """Return the existing key for an entry with this db id, or None."""
        for key, entry in self.corrections_dict.items():
            if entry.get("id") == id_no:
                return key
        return None

    def get_next_correction(
        self,
    ) -> tuple[dict[str, str | int] | None, Path | None, str | None, int]:
        """Retrieves and removes the next correction from the in-memory queue.

        Returns (correction, origin_path, source_key, corrections_remaining).
        source_key is the key as it appears in the contributor file — needed
        because the DB may assign a different id when the correction is
        committed. For the primary user flow, origin_path is the contributor
        file the item came from. The first three are None if no corrections
        are available.
        """
        if not self.corrections_dict:
            return None, None, None, 0

        first_key = next(iter(self.corrections_dict))
        correction = self.corrections_dict.pop(first_key)
        origin = self._origin.pop(first_key, None)
        return correction, origin, first_key, len(self.corrections_dict)

    def save_processed_correction(
        self,
        word_data: dict[str, str],
        origin_path: Path | None = None,
        source_key: str | None = None,
    ) -> None:
        """Append processed correction to corrections_added.json, tagging the
        contributor, and remove that key from the origin contributor file.
        source_key is the key as stored in the contributor file (may differ
        from word_data["id"] which gets a new DB-assigned value on commit).
        """
        contributor = _contributor_from_origin(origin_path, prefix="corrections_")

        existing_data: list[dict] = []
        try:
            with open(self.paths.corrections_added_path, encoding="utf-8") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        tagged = {**word_data, "_contributor": contributor}
        existing_data.append(tagged)

        with open(self.paths.corrections_added_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        if origin_path is not None and source_key is not None:
            _remove_key_from_file(origin_path, source_key)


def _contributor_from_origin(origin_path: Path | None, prefix: str) -> str:
    if origin_path is None:
        return "primary"
    stem = origin_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def _remove_key_from_file(path: Path, key: str) -> None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    if key in data:
        del data[key]
    with open(path, "w", encoding="utf-8") as f:
        if data:
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            f.write("{}")
