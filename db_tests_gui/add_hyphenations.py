import json
import re
import time

import flet as ft
import pyperclip

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools import goldendict_tools
from tools.db_search_string import db_search_string
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.printer import p_red


class State:
    def __init__(self):
        self.is_complete = False


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

    def load_hyphenations_dict(self):
        if self.pth.add_hyphenations_dict.exists():
            with open(self.pth.add_hyphenations_dict) as file:
                return json.load(file)
        else:
            p_red("no hyphenations dict found")
            return {}

    def save_hyphenations_dict(self):
        with open(self.pth.add_hyphenations_dict, "w") as file:
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

            # test it's not a known hyphenation
            if (
                clean_word not in self.exceptions
                and self.exceptions.get(clean_word, None) != dirty_word
                and "-" in dirty_word
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

        # turn the variations into list so that they are subscribable
        for key, values in variations_dict.items():
            variations_dict[key]["dirty_words"] = list(set(values["dirty_words"]))

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

        replacement_count = 0
        db_list = []
        for replace_me in self.spelling_other:
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
                    if replace_me in field:
                        field_new = field.replace(replace_me, self.spelling_choice)

                        setattr(i, field_name, field_new)
                        replacement_count += 1

        if replacement_count > 0:
            self.db_session.commit()
            return f"{replacement_count} replacement(s) made"

        else:
            if self.ids:
                ids_str = db_search_string(self.ids)
                pyperclip.copy(ids_str)
            return (
                "0 replacements made. ids copied to clipboard. try replacing manually"
            )


class Controller:
    def __init__(
        self,
        e: ft.ControlEvent,
        page: ft.Page,
        right_panel: ft.Container,
        state: State,
    ) -> None:
        self.state = state
        self.ui = Gui(self, e, page, right_panel)

        self.ui.update_message("loading data")
        self.data = Data()
        self.ui.update_message("data loaded")

        self.handle_next_item()

    def handle_commit(self, choice):
        if self.data.clean_word in self.data.exceptions:
            self.ui.update_message(f"updating {self.data.clean_word}")
        else:
            self.ui.update_message(f"added {self.data.clean_word}")
        self.data.update_hyphenations_dict(choice)

        message = self.data.replace_word_in_db()
        self.ui.update_message(message)

        time.sleep(2)

        self.handle_next_item()

    def handle_pass(self):
        self.handle_next_item()

    def handle_next_item(self):
        ok = self.data.load_next_item()
        if ok:
            self.ui.update_gui(self.data.clean_word, self.data.dirty_words)
            self.ui.update_message(
                f"{self.data.index} / {len(self.data.variations_dict)}"
            )
            if self.data.clean_word:
                goldendict_tools.open_in_goldendict_os(self.data.clean_word)
        else:
            self.ui.update_message("no more data")
            time.sleep(2)
            self.ui.update_message("loading next set")
            self.ui.clear_fields()
            self.data.decrease_max_length()
            self.data.index = -1
            self.data.load_data()
            self.handle_next_item()

    def handle_quit(self):
        self.state.is_complete = True


class Gui:
    """Flet gui."""

    height = 250
    width = 1000

    def __init__(
        self, control, e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container
    ):
        self.control = control
        self.page = page
        self.right_panel = right_panel
        self.right_panel.padding = ft.padding.all(20)

        self.page.padding = 100
        self.page.spacing = 10
        self.page.window.height = 1280

        # Set up the keyboard event handler
        self.page.on_keyboard_event = self.on_keyboard

        self.message_field = ft.Text("", width=self.width)
        self.clean_word = ft.TextField("", width=self.width)
        self.dirty_words = ft.Column(
            [], width=self.width, height=self.height, expand=True
        )
        self.choice_field = ft.TextField("", width=self.width)

        self.commit_button = ft.TextButton("commit", on_click=self.clicked_commit)
        self.pass_button = ft.TextButton("pass", on_click=self.clicked_pass)
        self.exit_button = ft.TextButton("exit", on_click=self.clicked_exit)

        self.layout = self.create_layout()
        self.right_panel.content = self.layout
        self.page.update()

    def create_layout(self):
        return ft.Column(
            [
                ft.Row([self.label(""), self.message_field]),
                ft.Row([self.label("clean word"), self.clean_word]),
                ft.Row([self.label("dirty words"), self.dirty_words]),
                ft.Row([self.label("choice"), self.choice_field]),
                ft.Row(
                    [
                        self.label(""),
                        self.commit_button,
                        self.pass_button,
                        self.exit_button,
                    ]
                ),
                ft.Divider(),
                ft.Row(
                    [
                        self.label(""),
                        ft.Text("1. Process bold tags."),
                    ]
                ),
                ft.Row(
                    [
                        self.label(""),
                        ft.Text("2. What happens when db doesn't match exceptions?"),
                    ]
                ),
                ft.Row(
                    [
                        self.label(""),
                        ft.Text("3. Make dirty container self-adjustable."),
                    ]
                ),
            ]
        )

    def clear_fields(self):
        self.clean_word.value = ""
        self.dirty_words.controls = []
        self.choice_field.value = ""
        self.page.update()

    # Handle keyboard
    def on_keyboard(self, e: ft.KeyboardEvent):
        pass
        # if e.key == "Q" and e.ctrl:
        #     self.page.window.close()

    def label(self, label):
        """Makes a text label."""
        return ft.Text(label, width=200)

    def update_message(self, text):
        self.message_field.value = text
        self.page.update()

    def update_gui(self, clean_word, dirty_words):
        self.clean_word.value = clean_word

        # Create list of rows with numbered buttons and text fields
        self.dirty_words.controls = [
            ft.Row(
                [
                    ft.ElevatedButton(
                        str(i + 1),
                        on_click=self.clicked_on_dirty_word,
                    ),  # Button with number
                    ft.TextField(
                        dirty_word, width=self.width - 100
                    ),  # Text field with word
                ]
            )
            for i, dirty_word in enumerate(dirty_words)
        ]
        if len(dirty_words) == 0:
            self.choice_field.value = clean_word
        if len(dirty_words) < 2:
            self.choice_field.value = dirty_words[0]

        self.page.update()

    def clicked_on_dirty_word(self, e: ft.ControlEvent):
        self.choice_field.value = e.control.parent.controls[1].value

    def clicked_commit(self, e: ft.ControlEvent):
        print("commit clicked")
        self.control.handle_commit(self.choice_field.value)

    def clicked_pass(self, e: ft.ControlEvent):
        print("pass clicked")
        self.control.handle_pass()

    def clicked_exit(self, e: ft.ControlEvent):
        self.control.state.is_complete = True


def add_hyphenations(e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container):
    state = State()
    Controller(e, page, right_panel, state)

    while not state.is_complete:
        page.update()
        time.sleep(0.1)
