"""Find long hyphenated words and choose one spelling for each."""

import json
import re
import sys
import termios
import tty

import pyperclip
from rich import print
from rich.markup import escape

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools import goldendict_tools
from tools.db_search_string import db_search_string
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager


def has_bold_tag_inside(text: str, form: str) -> bool:
    """Test if the form sits in the text with a bold tag inside the word."""
    tag = "(?:</?b>)*"
    pattern = tag.join(re.escape(char) for char in form)
    return any(match != form for match in re.findall(pattern, text))


def press_any_key() -> str:
    """Wait for a single keypress and return it."""

    print("press any key to continue or q to quit...", end="", flush=True)

    if not sys.stdin.isatty():
        return input().strip()

    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)
    print()
    return key


class Data:
    def __init__(self) -> None:
        self.hyphenated_only: bool = True

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()

        self.hyphenations_dict: dict = self.load_hyphenations_dict()

        self.clean_words_dict: dict[str, set]
        self.long_words_dict: dict
        self.hyphenated_words_dict: dict
        self.variations_dict: dict
        self.variations_list: list[tuple[str, dict]]
        self.load_data()

        self.index: int = -1
        self.clean_word: str | None = None
        self.values: dict | None = None
        self.dirty_words: list[str] | None = None
        self.ids: set | None = None

        self.spelling_choice: str | None = None
        self.replaced_nothing: bool = False

    @property
    def exceptions(self) -> dict[str, str]:
        return self.hyphenations_dict["exceptions"]

    @property
    def max_length(self) -> int:
        return self.hyphenations_dict["max_length"]

    def decrease_max_length(self):
        self.hyphenations_dict["max_length"] -= 1
        self.save_hyphenations_dict()

    def load_data(self):
        self.clean_words_dict: dict[str, set] = self.extract_clean_words()
        self.long_words_dict: dict = self.find_long_words()
        self.hyphenated_words_dict: dict = self.find_hyphenated_words()
        self.variations_dict: dict = self.find_variations()
        self.variations_list: list[tuple[str, dict]] = list(
            self.variations_dict.items()
        )
        self.auto_approved: int = self.auto_approve_single_forms()

    def find_forms(self, clean_words: set[str]) -> dict[str, set[str]]:
        """Map each given clean word to every form of it in the text."""
        regex_compile = re.compile(rf"[^{'|'.join(pali_alphabet)}]")

        forms: dict[str, set[str]] = {}
        for word in self.clean_words_dict:
            clean_word = re.sub(regex_compile, "", word)
            if clean_word in clean_words:
                forms.setdefault(clean_word, set()).add(word)
        return forms

    def auto_approve_single_forms(self) -> int:
        """Approve each word whose text holds one marked form. Return the count.

        The plain word may sit beside it: the marked form is still the only
        choice, and the plain form stays in the text. A word needs a choice
        only when its text has two differently marked forms.
        """
        forms = self.find_forms(set(self.variations_dict))

        approved = [
            (clean_word, next(iter(found - {clean_word})))
            for clean_word, found in forms.items()
            if len(found - {clean_word}) == 1 and clean_word not in self.exceptions
        ]
        for clean_word, form in approved:
            self.exceptions[clean_word] = form
            del self.variations_dict[clean_word]

        if approved:
            self.variations_list = list(self.variations_dict.items())
            self.save_hyphenations_dict()
        return len(approved)

    def load_hyphenations_dict(self):
        # a missing file raises FileNotFoundError, which names the path
        with open(self.pth.add_hyphenations_config_path, encoding="utf-8") as file:
            return json.load(file)

    def save_hyphenations_dict(self):
        with open(self.pth.add_hyphenations_config_path, "w", encoding="utf-8") as file:
            json.dump(self.hyphenations_dict, file, ensure_ascii=False, indent=2)

    def update_hyphenations_dict(self, choice):
        self.spelling_choice = choice
        self.hyphenations_dict["exceptions"][self.clean_word] = choice
        self.save_hyphenations_dict()

    def extract_clean_words(self):
        """extract all clean words from the db in examples and commentary."""

        # compile regex of pali_alphabet space apostrophe dash
        regex_compile = re.compile(f"[^{'|'.join(pali_alphabet)}| |'|-]")

        clean_words_dict = {}
        for i in self.db:
            id = i.id
            for column in ["example_1", "example_2", "commentary"]:
                cell = getattr(i, column)
                clean_cell = cell.replace("<b>", "").replace("</b>", "")
                clean_cell = re.sub(regex_compile, " ", clean_cell)
                clean_words = clean_cell.split(" ")

                for clean_word in clean_words:
                    if clean_word:
                        if clean_word not in clean_words_dict:
                            clean_words_dict[clean_word] = set([id])
                        else:
                            clean_words_dict[clean_word].add(id)
        return clean_words_dict

    def find_long_words(self):
        """Find all the long words"""

        long_words_dict: dict = {}
        for word, ids in self.clean_words_dict.items():
            if len(word) > self.max_length:
                long_words_dict.update({word: ids})

        return long_words_dict

    def find_hyphenated_words(self):
        """Find all hyphenated words"""

        hyphenated_words_dict: dict = {}
        for word, ids in self.clean_words_dict.items():
            if "-" in word:
                hyphenated_words_dict.update({word: ids})

        return hyphenated_words_dict

    def find_variations(self):
        """Find apostrophe and hyphenation variations in long words."""

        # compile regex of only pali_alphabet
        regex_compile = re.compile(rf"[^{'|'.join(pali_alphabet)}]")

        variations_dict: dict = {}
        for dirty_word, ids in self.long_words_dict.items():
            clean_word = re.sub(regex_compile, "", dirty_word)

            # An approved word comes back when the text holds another marked
            # form. An unapproved word needs a hyphen to be listed.
            if (
                dirty_word != clean_word
                and self.exceptions.get(clean_word) != dirty_word
                and ("-" in dirty_word or clean_word in self.exceptions)
            ):
                # add to or update variations_dict
                if clean_word not in variations_dict:
                    variations_dict[clean_word] = {
                        "dirty_words": set([dirty_word]),
                        "ids": ids,
                    }
                else:
                    variations_dict[clean_word]["dirty_words"].update([dirty_word])
                    variations_dict[clean_word]["ids"].update(ids)

        # list every marked form of the word, not only the long hyphenated ones,
        # so no form is left out of the choice. Sorted so the numbers are stable.
        all_forms = self.find_forms(set(variations_dict))
        for key, values in variations_dict.items():
            dirty_words = set(values["dirty_words"])
            dirty_words |= all_forms.get(key, set()) - {key}
            # list the approved spelling so it can be picked again
            approved = self.exceptions.get(key)
            if approved:
                dirty_words.add(approved)
            variations_dict[key]["dirty_words"] = sorted(dirty_words)

        return variations_dict

    def load_next_item(self):
        if self.index < len(self.variations_list) - 1:
            self.index += 1
            self.clean_word, self.values = self.variations_list[self.index]
            self.dirty_words = self.values["dirty_words"]
            self.ids = self.values["ids"]
            return True
        else:
            return False

    def unchosen_forms_have_bold_tag_inside(self) -> bool:
        """Test if a form that was not chosen has a bold tag inside it in the db.

        The replace cannot match such a form, so it needs a hand edit.
        """
        for form in self.spelling_other:
            if not form:
                continue
            for headword_id in self.clean_words_dict.get(form, set()):
                headword = self.db_session.get(DpdHeadword, headword_id)
                if headword and any(
                    has_bold_tag_inside(getattr(headword, field_name), form)
                    for field_name in ["example_1", "example_2", "commentary"]
                ):
                    return True
        return False

    @property
    def spelling_other(self):
        spelling_other = [self.clean_word]
        if self.dirty_words:
            spelling_other.extend(self.dirty_words)
        if self.spelling_choice in spelling_other:
            spelling_other.remove(self.spelling_choice)
        spelling_other = list(set(spelling_other))
        return spelling_other

    def replace_word_in_db(self) -> str:
        """Replace all variations with the preferred hyphenation."""

        if (
            self.dirty_words
            and len(self.dirty_words) == 1
            and self.dirty_words[0] == self.spelling_choice
        ):
            return "nothing to replace"

        # Both are Optional on the class; without a choice the queries below would
        # search for None and the replace would raise.
        spelling_choice = self.spelling_choice
        if not spelling_choice:
            return "no spelling choice selected"

        self.replaced_nothing = False
        replacement_count = 0
        db_list = []
        for replace_me in self.spelling_other:
            if not replace_me:
                continue
            db = (
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.example_1.contains(replace_me))
                .all()
            )
            db_list.extend(db)

            db = (
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.example_2.contains(replace_me))
                .all()
            )
            db_list.extend(db)

            db = (
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.commentary.contains(replace_me))
                .all()
            )
            db_list.extend(db)

            for i in db_list:
                for field, field_name in [
                    (i.example_1, "example_1"),
                    (i.example_2, "example_2"),
                    (i.commentary, "commentary"),
                ]:
                    if field and replace_me in field:
                        field_new = field.replace(replace_me, spelling_choice)

                        setattr(i, field_name, field_new)
                        replacement_count += 1

        if replacement_count > 0:
            self.db_session.commit()
            return f"{replacement_count} replacement(s) made"

        else:
            self.replaced_nothing = True
            if self.ids:
                ids_str = db_search_string(self.ids)
                pyperclip.copy(ids_str)
            return (
                "0 replacements made. ids copied to clipboard. try replacing manually"
            )


def show_existing_versions(data: Data) -> None:
    """Print each version of the word plainly, for editing by hand."""
    print()
    for form in data.dirty_words or []:
        print(escape(form))
    print("-" * 50)


def main() -> None:
    """Show each set of hyphen variants and ask which spelling to keep."""
    pr.tic()
    pr.yellow_title("find long hyphenated words and choose one spelling")

    data = Data()
    changed = ask_about_all_words(data)

    # the speech marks file is rebuilt from the db text, so the spellings
    # just rejected leave it
    if changed:
        print("[green]updating speech marks")
        SpeechMarkManager().regenerate_from_db()
        print("[green]speech marks updated")

    pr.toc()


def ask_about_all_words(data: Data) -> bool:
    """Ask about every set of variants. Return True if any choice was saved."""
    changed = False

    while True:
        if data.auto_approved:
            print(f"[green]{data.auto_approved} words with one form approved")
        total = len(data.variations_list)
        if not total:
            print("[green]nothing to do")

        while data.load_next_item():
            clean_word = data.clean_word or ""
            dirty_words = data.dirty_words or []
            goldendict_tools.open_in_goldendict(clean_word)

            print()
            print("-" * 50)
            print()
            pr.summary("", f"{data.index + 1} / {total}")
            pr.summary("max length", data.max_length)
            pr.summary("clean word", escape(clean_word))
            for number, dirty_word in enumerate(dirty_words, start=1):
                pr.summary(str(number), escape(dirty_word))
            print()
            print(
                "[yellow]1[white]-9 pick, [yellow]p[white]ass [yellow]q[white]uit or Enter to pass: ",
                end="",
            )
            answer = input().strip()

            if answer == "q":
                return changed
            elif answer == "p":
                continue
            elif answer.isdigit() and 1 <= int(answer) <= len(dirty_words):
                choice = dirty_words[int(answer) - 1]
            elif answer:
                choice = answer
            else:
                continue

            if clean_word in data.exceptions:
                print(f"[green]updating {escape(choice)}")
            else:
                print(f"[green]added {escape(choice)}")
            data.update_hyphenations_dict(choice)
            print(escape(data.replace_word_in_db()))
            changed = True
            if data.replaced_nothing or data.unchosen_forms_have_bold_tag_inside():
                show_existing_versions(data)
                if press_any_key() == "q":
                    return changed

        # this length is done, so go on to shorter words. Stop at 1 without
        # saving 0, because a saved 0 would make every word count as long.
        if data.max_length <= 1:
            print("[green]no more data")
            break
        data.decrease_max_length()
        print(f"[green]loading words longer than {data.max_length}")
        data.index = -1
        data.load_data()

    return changed


if __name__ == "__main__":
    main()
