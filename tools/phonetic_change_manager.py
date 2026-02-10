"""PhoneticChangeManager for detecting and applying phonetic changes.

This module provides a manager class that loads phonetic change rules
from a TSV file and provides methods to detect and process phonetic
changes for headwords.
"""

import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class PhoneticChangeResult:
    """Result of processing a headword for phonetic changes.

    Attributes:
        status: The action to take - "auto_update", "auto_add", or "manual_check"
        suggestion: The suggested phonetic change value
        rule: The rule that matched
        current_value: The current phonetic value (for auto_update)
    """

    status: str
    suggestion: str
    rule: dict
    current_value: str = ""


class PhoneticChangeManager:
    """Manages phonetic change detection and application.

    Loads rules from a TSV file and provides methods to detect phonetic
    changes based on construction patterns, base patterns, and lemma.
    """

    def __init__(self, tsv_path: str | Path) -> None:
        """Initialize the manager by loading TSV rules.

        Args:
            tsv_path: Path to the TSV file containing phonetic change rules.

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
                # Skip empty rows
                if not row.get("initial"):
                    continue

                # Parse exceptions into list
                exceptions_str = row.get("exceptions", "")
                if exceptions_str and exceptions_str != "x":
                    exceptions = [e.strip() for e in exceptions_str.split(",")]
                else:
                    exceptions = []

                rule = {
                    "initial": row["initial"],
                    "final": row["final"],
                    "correct": row["correct"],
                    "wrong": row.get("wrong", ""),
                    "without": row.get("without", ""),
                    "exceptions": exceptions,
                }
                self.rules.append(rule)

    def get_rules(self) -> List[dict[str, str | List[str]]]:
        """Return the loaded rules.

        Returns:
            List of rule dictionaries containing initial, final, correct,
            wrong, without, and exceptions.
        """
        return self.rules

    def _clean_headword_data(self, headword) -> tuple[str, str]:
        """Extract and clean construction and base from headword.

        Args:
            headword: A DpdHeadword instance.

        Returns:
            Tuple of (construction_clean, base_clean)
        """
        construction_clean = headword.construction_clean or ""
        construction_clean = re.sub(r"√", "", construction_clean)
        construction_clean = re.sub(r"\\*", "", construction_clean)

        base_clean = headword.root_base_clean or ""
        base_clean = re.sub(r"√", "", base_clean)
        base_clean = re.sub(r"\\*", "", base_clean)

        return construction_clean, base_clean

    def _check_rule_logic(
        self, headword, rule, construction_clean: str, base_clean: str
    ) -> PhoneticChangeResult | None:
        """Check if a specific rule matches a headword.

        Args:
            headword: A DpdHeadword instance to check.
            rule: The specific rule dictionary to check against.
            construction_clean: Cleaned construction string.
            base_clean: Cleaned base string.

        Returns:
            PhoneticChangeResult if rule matches, None otherwise.
        """
        # Skip if initial is "-" (end marker)
        if rule["initial"] == "-":
            return None

        # Check if lemma is in exceptions
        if headword.lemma_1 in rule["exceptions"]:
            return None

        # Check all conditions
        rule_initial = str(rule["initial"])
        rule_final = str(rule["final"])
        rule_correct = str(rule["correct"])
        rule_wrong = str(rule.get("wrong", ""))
        rule_without = str(rule.get("without", ""))

        initial_match = rule_initial in construction_clean or rule_initial in base_clean
        final_match = rule_final in headword.lemma_clean
        correct_not_present = rule_correct not in headword.phonetic

        # Check without exclusion
        without_exclusion = False
        if rule_without and rule_without != "x":
            if rule_without in construction_clean or rule_without in base_clean:
                without_exclusion = True

        if (
            initial_match
            and final_match
            and correct_not_present
            and not without_exclusion
        ):
            # Determine status
            if rule_wrong and rule_wrong in headword.phonetic:
                return PhoneticChangeResult(
                    status="auto_update",
                    suggestion=rule_correct,
                    rule=rule,
                    current_value=headword.phonetic,
                )
            elif not headword.phonetic:
                return PhoneticChangeResult(
                    status="auto_add",
                    suggestion=rule_correct,
                    rule=rule,
                )
            else:
                return PhoneticChangeResult(
                    status="manual_check",
                    suggestion=rule_correct,
                    rule=rule,
                    current_value=headword.phonetic,
                )

        return None

    def check_headword_against_rule(
        self, headword, rule
    ) -> PhoneticChangeResult | None:
        """Check a specific rule against a headword (for batch processing).

        This is an optimized method for batch scripts that iterate through
        rules externally. It checks only the provided rule without looping
        through all rules.

        Args:
            headword: A DpdHeadword instance to check.
            rule: The specific rule dictionary to check against.

        Returns:
            PhoneticChangeResult if rule matches, None otherwise.
        """
        # Check preconditions
        if not headword.meaning_1:
            return None

        if not headword.construction:
            return None

        # Clean construction and base
        construction_clean, base_clean = self._clean_headword_data(headword)

        # Check the specific rule
        return self._check_rule_logic(headword, rule, construction_clean, base_clean)

    def process_headword(self, headword) -> PhoneticChangeResult | None:
        """Process a headword and determine if phonetic changes are needed.

        This method checks all rules and returns the first match found.
        For batch processing where you iterate through rules externally,
        use check_headword_against_rule() instead.

        Args:
            headword: A DpdHeadword instance to process.

        Returns:
            PhoneticChangeResult if a match is found, None otherwise.
            The result contains:
            - status: "auto_update" if wrong value should be replaced,
                     "auto_add" if phonetic is empty,
                     "manual_check" if phonetic has other content
            - suggestion: The correct phonetic value
            - rule: The matching rule
            - current_value: Current phonetic value (for auto_update)
        """
        # Check preconditions
        if not headword.meaning_1:
            return None

        if not headword.construction:
            return None

        # Clean construction and base (once for all rules)
        construction_clean, base_clean = self._clean_headword_data(headword)

        # Check all rules
        for rule in self.rules:
            result = self._check_rule_logic(
                headword, rule, construction_clean, base_clean
            )
            if result:
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
