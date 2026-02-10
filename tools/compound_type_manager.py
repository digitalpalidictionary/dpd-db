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
            if pos not in rule_pos_list:
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

        if compound_type:
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
