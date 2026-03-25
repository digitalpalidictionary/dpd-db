"""CompoundTypeManager for detecting compound types based on TSV rules.

This module provides a manager class that loads compound type detection rules
from a TSV file and provides methods to detect compound types based on
construction patterns.
"""

import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import List

from tools.pali_sort_key import pali_sort_key

TSV_FIELDNAMES = ["word", "pos", "position", "type", "exceptions", "notes"]


class CompoundTypeManager:
    """Manages compound type detection rules and logic.

    Loads rules from a TSV file and provides methods to detect compound types
    based on construction patterns, POS tags, and grammar information.
    """

    POS_EXCLUSIONS = ["sandhi", "idiom", "aor"]

    def __init__(self, tsv_path: str | Path) -> None:
        """Initialize the manager by loading TSV rules.

        Args:
            tsv_path: Path to the TSV file containing compound type rules.

        Raises:
            FileNotFoundError: If the TSV file does not exist.
        """
        self.tsv_path = Path(tsv_path)
        self.rules: List[dict[str, str | List[str]]] = []
        self._load_tsv()

    def _load_tsv(self) -> None:
        """Load and parse the TSV file.

        Raises:
            FileNotFoundError: If the TSV file does not exist.
        """
        if not self.tsv_path.exists():
            raise FileNotFoundError(f"TSV file not found: {self.tsv_path}")

        with open(self.tsv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                # Parse exceptions into list
                exceptions_str = row.get("exceptions", "")
                if exceptions_str:
                    exceptions = [e.strip() for e in exceptions_str.split(",")]
                else:
                    exceptions = []

                rule = {
                    "word": row["word"],
                    "pos": row["pos"],
                    "position": row["position"],
                    "type": row["type"],
                    "exceptions": exceptions,
                    "notes": row.get("notes", ""),
                }
                self.rules.append(rule)

    def get_rules(self) -> List[dict[str, str | List[str]]]:
        """Return the loaded rules.

        Returns:
            List of rule dictionaries containing word, pos, position, type, and exceptions.
        """
        return self.rules

    def _check_rule_logic(
        self,
        rule: dict,
        construction: str,
        pos: str,
        lemma: str = "",
    ) -> str | None:
        """Check if a specific rule matches the given criteria.

        Args:
            rule: The rule dictionary to check.
            construction: The construction field value.
            pos: Part of speech tag.
            lemma: Lemma identifier for exception checking.

        Returns:
            The detected compound type if rule matches, None otherwise.
        """
        rule_word = str(rule["word"])
        rule_pos = str(rule["pos"])
        rule_position = str(rule["position"])
        rule_type = str(rule["type"])

        # Check if lemma is in exceptions
        if lemma and lemma in rule["exceptions"]:
            return None

        # Check POS match
        if rule_pos != "any":
            rule_pos_list = [p.strip() for p in rule_pos.split(",")]
            noun_pos = {"masc", "fem", "nt"}
            expanded = set()
            for p in rule_pos_list:
                if p == "noun":
                    expanded |= noun_pos
                else:
                    expanded.add(p)
            if pos not in expanded:
                return None

        # Build pattern based on position
        if rule_position == "first":
            pattern = rf"^{re.escape(rule_word)} "
        elif rule_position == "middle":
            pattern = rf" {re.escape(rule_word)} "
        elif rule_position == "last":
            pattern = rf" {re.escape(rule_word)}\b"
        elif rule_position == "any":
            pattern = rf"\b{re.escape(rule_word)}\b"
        else:
            return None

        # Check if pattern matches in construction
        if re.search(pattern, construction):
            # Extract first type if multiple types specified
            detected_type = rule_type.split(">")[0].strip()
            return detected_type

        return None

    def check_headword_against_rule(
        self,
        rule: dict,
        construction: str,
        pos: str,
        grammar: str,
        lemma: str = "",
        meaning_1: str = "placeholder",
        compound_type: str = "",
    ) -> str | None:
        """Check a specific rule against headword fields (for batch processing).

        This is an optimized method for batch scripts that iterate through
        rules externally. It checks only the provided rule without looping
        through all rules.

        Args:
            rule: The specific rule dictionary to check against.
            construction: The construction field value.
            pos: Part of speech tag.
            grammar: Grammar field value.
            lemma: Lemma identifier for exception checking.
            meaning_1: Meaning field (must not be empty).
            compound_type: Existing compound type (if already set).

        Returns:
            The detected compound type if rule matches, None otherwise.
        """
        # Check preconditions
        if not meaning_1:
            return None

        if pos in self.POS_EXCLUSIONS:
            return None

        if ", comp" not in grammar:
            return None

        if compound_type:
            return None

        # Check the specific rule
        return self._check_rule_logic(rule, construction, pos, lemma)

    def detect_compound_type(
        self,
        construction: str,
        pos: str,
        grammar: str,
        lemma: str = "",
        meaning_1: str = "placeholder",
        compound_type: str = "",
    ) -> str | None:
        """Detect compound type based on construction and other fields.

        This method checks all rules and returns the first match found.
        For batch processing where you iterate through rules externally,
        use check_headword_against_rule() instead.

        Args:
            construction: The construction field value.
            pos: Part of speech tag.
            grammar: Grammar field value.
            lemma: Lemma identifier for exception checking.
            meaning_1: Meaning field (must not be empty).
            compound_type: Existing compound type (if already set).

        Returns:
            The detected compound type or None if no match found.
        """
        # Check preconditions
        if not meaning_1:
            return None

        if pos in self.POS_EXCLUSIONS:
            return None

        if ", comp" not in grammar:
            return None

        if compound_type and compound_type.strip():
            return None

        # Check all rules
        for rule in self.rules:
            result = self._check_rule_logic(rule, construction, pos, lemma)
            if result:
                rule_word = str(rule["word"])
                rule_pos = str(rule["pos"])
                rule_position = str(rule["position"])
                rule_type = str(rule["type"])
                print(
                    f"DEBUG: Rule MATCHED - word='{rule_word}', pos='{rule_pos}', position='{rule_position}', type='{rule_type}'"
                )
                return result

        return None

    def reload(self) -> None:
        """Reload rules from the TSV file, discarding in-memory state."""
        self.rules = []
        self._load_tsv()

    def get_rules_by_word(self, word: str) -> list[dict[str, str | List[str]]]:
        """Return all rules matching the given word.

        Args:
            word: The word to search for.

        Returns:
            List of matching rule dicts (may be empty).
        """
        return [r for r in self.rules if str(r["word"]) == word]

    def get_rule_by_word(self, word: str) -> dict[str, str | List[str]] | None:
        """Return the first rule matching the given word, or None.

        Args:
            word: The word to search for.

        Returns:
            The matching rule dict, or None if not found.
        """
        matches = self.get_rules_by_word(word)
        return matches[0] if matches else None

    def get_unique_values(self, field: str) -> list[str]:
        """Return sorted unique values for a given rule field.

        Args:
            field: One of "pos", "position", or "type".

        Returns:
            Sorted list of unique string values for that field.
        """
        seen: set[str] = set()
        for rule in self.rules:
            val = str(rule.get(field, "")).strip()
            if val:
                seen.add(val)
        return sorted(seen)

    def add_rule(
        self,
        word: str,
        pos: str,
        position: str,
        type_: str,
        exceptions: str,
        notes: str = "",
    ) -> None:
        """Append a new rule to the TSV and update in-memory rules.

        Args:
            word: The word for the rule.
            pos: Part of speech.
            position: Position (first, middle, last, any).
            type_: Compound type string.
            exceptions: Comma-separated exceptions string.
        """
        exceptions_list = (
            [e.strip() for e in exceptions.split(",") if e.strip()]
            if exceptions
            else []
        )
        new_rule: dict[str, str | List[str]] = {
            "word": word,
            "pos": pos,
            "position": position,
            "type": type_,
            "exceptions": exceptions_list,
            "notes": notes,
        }
        self.rules.append(new_rule)
        self._save_tsv()

    def update_rule(
        self,
        word: str,
        old_pos: str,
        old_position: str,
        new_word: str,
        pos: str,
        position: str,
        type_: str,
        exceptions: str,
        notes: str = "",
    ) -> None:
        """Update an existing rule matched by (word, pos, position) composite key.

        Args:
            word: The current word identifying the rule.
            old_pos: The current pos identifying the rule.
            old_position: The current position identifying the rule.
            new_word: New word value.
            pos: New part of speech.
            position: New position.
            type_: New compound type string.
            exceptions: New comma-separated exceptions string.
        """
        exceptions_list = (
            [e.strip() for e in exceptions.split(",") if e.strip()]
            if exceptions
            else []
        )
        for rule in self.rules:
            if (
                str(rule["word"]) == word
                and str(rule["pos"]) == old_pos
                and str(rule["position"]) == old_position
            ):
                rule["word"] = new_word
                rule["pos"] = pos
                rule["position"] = position
                rule["type"] = type_
                rule["exceptions"] = exceptions_list
                rule["notes"] = notes
                break
        self._save_tsv()

    def delete_rule(self, word: str, pos: str, position: str) -> None:
        """Delete a rule matched by (word, pos, position) composite key.

        Args:
            word: The word of the rule to delete.
            pos: The pos of the rule to delete.
            position: The position of the rule to delete.
        """
        self.rules = [
            r
            for r in self.rules
            if not (
                str(r["word"]) == word
                and str(r["pos"]) == pos
                and str(r["position"]) == position
            )
        ]
        self._save_tsv()

    def _save_tsv(self) -> None:
        """Write the current in-memory rules back to the TSV file."""
        self.rules.sort(
            key=lambda r: (
                pali_sort_key(str(r["word"])),
                str(r["pos"]),
                str(r["position"]),
            )
        )
        with open(self.tsv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=TSV_FIELDNAMES, delimiter="\t", lineterminator="\n"
            )
            writer.writeheader()
            for rule in self.rules:
                exceptions_list = rule.get("exceptions", [])
                if isinstance(exceptions_list, list):
                    exceptions_str = ", ".join(exceptions_list)
                else:
                    exceptions_str = str(exceptions_list)
                writer.writerow(
                    {
                        "word": rule["word"],
                        "pos": rule["pos"],
                        "position": rule["position"],
                        "type": rule["type"],
                        "exceptions": exceptions_str,
                        "notes": rule.get("notes", ""),
                    }
                )

    def open_tsv_for_editing(self) -> None:
        """Open the TSV file in LibreOffice Calc.

        Uses LibreOffice Calc to open the TSV file, with fallback to xdg-open
        if LibreOffice is not available. Matches the existing GUI pattern.

        Raises:
            FileNotFoundError: If the TSV file does not exist.
            RuntimeError: If unable to open the file with any method.
        """
        if not self.tsv_path.exists():
            raise FileNotFoundError(f"TSV file not found: {self.tsv_path}")

        try:
            # Try LibreOffice Calc first (matching existing GUI pattern)
            subprocess.Popen(["libreoffice", "--calc", str(self.tsv_path)])
        except FileNotFoundError:
            # Fallback to xdg-open on Linux
            if sys.platform == "linux":
                subprocess.run(["xdg-open", str(self.tsv_path)], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.tsv_path)], check=False)
            else:
                raise RuntimeError(
                    f"Unable to open TSV file. "
                    f"Please install LibreOffice or open manually: {self.tsv_path}"
                )
