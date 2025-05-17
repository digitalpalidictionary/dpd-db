"""Finds all words in examples and commentary that contain an apostrophe
denoting sandhi or contraction, eg. ajj'uposatho, tañ'ca"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from json import dump, load

from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.pali_sort_key import pali_sort_key
from tools.printer import printer as pr


@dataclass
class SandhiContrItem:
    contractions: set[str]
    ids: list[str]


SandhiContractionDict = dict[str, list[str]]


class SandhiContractionFinder:
    def __init__(self):
        self._pth: ProjectPaths = ProjectPaths()
        self._db_session: Session
        self.refresh_db_session()
        self._exceptions: list[str] = [
            "maññeti",
            "āyataggaṃ",
            "nayanti",
            "āṇāti",
            "gacchanti",
            "jīvanti",
            "sayissanti",
            "gāmeti",
        ]
        self._contractions_details: dict[str, SandhiContrItem]
        self._contractions_simple: SandhiContractionDict
        self._load_or_create_data()

    def refresh_db_session(self):
        self._db_session: Session = get_db_session(self._pth.dpd_db_path)

    def _should_regenerate(self) -> bool:
        """Check if cache is older than 1 day"""

        return (
            not self._pth.sandhi_contractions_simple_path.exists()
            or datetime.now()
            - datetime.fromtimestamp(
                self._pth.sandhi_contractions_simple_path.stat().st_mtime
            )
            > timedelta(days=1)
        )

    def _load_or_create_data(self):
        """Load cached data or create new if expired"""

        if self._should_regenerate():
            self._make_sandhi_contractions()
        try:
            self._load_simple_cache()
        except Exception as e:
            pr.red(f"str{e}")
            self._make_sandhi_contractions()

    def _load_simple_cache(self) -> None:
        """Load the simple contractions data from database"""

        with open(self._pth.sandhi_contractions_simple_path) as f:
            self._contractions_simple = load(f)

    def _create_simple_version(self) -> SandhiContractionDict:
        """Create simplified dict of just contractions without IDs"""

        return {k: list(v.contractions) for k, v in self._contractions_details.items()}

    def _save_simple_version(self) -> None:
        """Save simplified contractions to JSON file"""

        sorted_contractions_simple = dict(
            sorted(
                self._contractions_simple.items(),
                key=lambda item: pali_sort_key(item[0]),
            )
        )

        with open(self._pth.sandhi_contractions_simple_path, "w") as f:
            dump(
                sorted_contractions_simple,
                f,
                indent=2,
                ensure_ascii=False,
            )

    def get_sandhi_contractions(self) -> dict[str, SandhiContrItem]:
        """Return the simple sandhi contractions dictionary."""
        return self._contractions_details

    def get_sandhi_contractions_simple(self) -> SandhiContractionDict:
        """Return the simple sandhi contractions dictionary."""
        return self._contractions_simple

    def save_contractions(self) -> None:
        """Save the contractions dictionary to a temp file."""

        self._save_to_temp_file()

    def update_contractions(self) -> None:
        """Regenerate and return the contractions dictionary."""
        self._make_sandhi_contractions()

    def update_contractions_simple(self) -> SandhiContractionDict:
        """Regenerate and return the simple contractions dictionary."""
        pr.green("updating sandhi contractions")

        self._make_sandhi_contractions()
        pr.yes(len(self._contractions_simple))

        return self._contractions_simple

    def _replace_split(self, string: str) -> list[str]:
        """Clean and split a string into words."""

        replacements = [
            ("<b>", ""),
            ("</b>", ""),
            ("<i>", ""),
            ("</i>", ""),
            (".", " "),
            (",", " "),
            (";", " "),
            ("!", " "),
            ("?", " "),
            ("/", " "),
            ("-", " "),
            ("{", " "),
            ("}", " "),
            ("(", " "),
            (")", " "),
            ("[", " "),
            ("]", " "),
            (":", " "),
            ("\n", " "),
            ("\r", " "),
        ]

        for old, new in replacements:
            string = string.replace(old, new)
        return string.split(" ")

    def _make_sandhi_contractions(self):
        """Find all sandhi words in db that are split with apostrophes."""

        # only include words with meaning_1,
        # there's some junk in examples without meaning_1
        db = (
            self._db_session.query(DpdHeadword)
            .filter(DpdHeadword.meaning_1 != "")
            .all()
        )
        sandhi_contraction_dict: dict[str, SandhiContrItem] = {}
        word_dict: dict[int, set[str]] = {}

        for i in db:
            word_dict[i.id] = set()
            fields_to_check = [i.example_1, i.example_2, i.commentary]

            for field in fields_to_check:
                if field and "'" in field:
                    for word in self._replace_split(field):
                        if "'" in word:
                            word_dict[i.id].add(word)

        for id, words in word_dict.items():
            for word in words:
                word_clean = word.replace("'", "")
                if word not in self._exceptions:
                    if word_clean not in sandhi_contraction_dict:
                        sandhi_contraction_dict[word_clean] = SandhiContrItem(
                            contractions={word}, ids=[str(id)]
                        )
                    else:
                        if word not in sandhi_contraction_dict[word_clean].contractions:
                            sandhi_contraction_dict[word_clean].contractions.add(word)
                        sandhi_contraction_dict[word_clean].ids.append(str(id))

        for i in db:
            fields = [i.example_1, i.example_2, i.commentary]
            for field in fields:
                if field:
                    for word in self._replace_split(field):
                        if word in sandhi_contraction_dict:
                            sandhi_contraction_dict[word].contractions.add(word)
                            sandhi_contraction_dict[word].ids.append(str(i.id))

        error_list = []
        for key in sandhi_contraction_dict:
            for char in key:
                if char not in pali_alphabet:
                    error_list.append(char)
                    print(key)
        if error_list:
            print("[red]SANDHI ERRORS IN EG1,2,COMM:", end=" ")
            print([x for x in error_list], end=" ")

        self._contractions_details = sandhi_contraction_dict
        self._contractions_simple = self._create_simple_version()
        self._save_simple_version()

    def _save_to_temp_file(self) -> None:
        """Save results to TSV file in temp directory."""

        filepath = self._pth.temp_dir.joinpath("sandhi_contraction.tsv")
        counter = 0

        with open(filepath, "w") as f:
            for key, values in self._contractions_details.items():
                if len(values.contractions) > 1 and key not in self._exceptions:
                    f.write(f"{counter}. {key}: \n")
                    for contraction in values.contractions:
                        f.write(f"{contraction}\n")
                    f.write(f"/^({'|'.join(values.ids)})$/\n\n")
                    counter += 1
        print(counter)

    def run(self) -> None:
        """Execute the full sandhi contraction finding process."""
        self._make_sandhi_contractions()
        self._save_to_temp_file()


def main() -> None:
    pr.tic()
    finder = SandhiContractionFinder()
    finder.update_contractions_simple()
    # finder.run()
    # print(len(finder.get_sandhi_contractions()))
    # print(len(finder.get_contractions()))
    pr.toc()


if __name__ == "__main__":
    main()
