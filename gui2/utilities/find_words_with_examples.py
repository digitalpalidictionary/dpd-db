#!/usr/bin/env python3

"""
Find words which already have examples.
Look in:
1. example_1
2. example_2
3. commentary.
"""

import json
import re
from collections import defaultdict

import flet as ft

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.class_paths import Gui2Paths
from tools.goldendict_tools import open_in_goldendict_os
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths


class Controller:
    def __init__(self, page):
        self.ui = Gui(self, page)
        self.data = Data()
        self.load_next()

    def load_next(self):
        self.data.find_next_example()
        self.update_display()

    def update_display(self):
        open_in_goldendict_os(self.data.lemma)
        self.ui.message.value = ""
        self.ui.sentence_id.value = str(self.data.sentence_id)
        self.ui.word_in_sentence.value = self.data.word
        self.ui.lemma.value = self.data.lemma
        self.ui.headword.value = f"{self.data.headword.id}: {self.data.headword.lemma_1} {self.data.headword.pos}. {self.data.headword.meaning_combo}"
        self.ui.source.value = self.data.source
        self.ui.sutta.value = self.data.sutta
        self.ui.example.spans = self.ui.highlight_word_in_sentence(
            self.data.word, self.data.example
        )
        self.ui.page.update()

    def handle_no(self):
        self.data.update_exceptions()
        self.load_next()

    def handle_yes(self):
        self.data.save_data()
        self.load_next()

    def handle_pass(self):
        self.load_next()

    def handle_reset(self):
        self.data = Data()
        self.load_next()


class Gui:
    """Flet gui."""

    height = 250
    width = 1000

    def __init__(self, control: Controller, page: ft.Page):
        self.control = control
        self.page = page
        self.page.title = "Examples in Database"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 100
        self.page.spacing = 20
        self.page.window.top = 0
        self.page.window.left = 0
        self.page.window.height = 1280
        self.page.theme = ft.Theme(
            font_family="Inter",
        )

        # Set up the keyboard event handler
        self.page.on_keyboard_event = self.on_keyboard

        # Create controls
        self.message = ft.Text(
            "loading data", width=self.width, color=ft.Colors.BLUE_100
        )
        self.sentence_id = ft.Text("", width=self.width, color=ft.Colors.BLUE_200)
        self.word_in_sentence = ft.Text("", width=self.width, color=ft.Colors.BLUE_200)
        self.lemma = ft.Text("", width=self.width, color=ft.Colors.GREEN_500)
        self.headword = ft.Text("", width=self.width, color=ft.Colors.BLUE)
        self.source = ft.Text("", width=self.width, color=ft.Colors.BLUE_200)
        self.sutta = ft.Text("", width=self.width, color=ft.Colors.BLUE_200)
        self.example = ft.Text(
            "", width=self.width, max_lines=5, expand=True, selectable=True
        )

        self.yes_button = ft.ElevatedButton("yes", on_click=self.yes_clicked)
        self.no_button = ft.ElevatedButton("no", on_click=self.no_clicked)
        self.pass_button = ft.ElevatedButton("pass", on_click=self.pass_clicked)
        self.reset_button = ft.ElevatedButton("reset", on_click=self.reset_clicked)

        # Add controls to page
        self.page.add(
            ft.Row([self.label(""), self.message]),
            ft.Row([self.label("id"), self.sentence_id]),
            ft.Row([self.label("word"), self.word_in_sentence]),
            ft.Row([self.label("lemma"), self.lemma]),
            ft.Row([self.label("headword"), self.headword]),
            ft.Row([self.label(""), self.source]),
            ft.Row([self.label(""), self.sutta]),
            ft.Row([self.label(""), self.example]),
            ft.Row(
                [
                    self.label(""),
                    self.yes_button,
                    self.no_button,
                    self.pass_button,
                    self.reset_button,
                ]
            ),
        )
        self.page.update()

    def highlight_word_in_sentence(self, word, sentence):
        """Turns paragraph of text into a list of TextSpan."""

        sentence = re.sub("'", "", sentence)

        spans = []
        parts = re.split(word, sentence)

        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        word,
                        style=ft.TextStyle(color=ft.Colors.BLUE),
                    )
                )
        return spans

    # Handle Ctrl+Q to quit
    def on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def label(self, label):
        """Makes a text label."""
        return ft.Text(label, width=100)

    def update_message(self, text: str):
        """Updates the window message."""
        self.message.value = text
        self.page.update()

    def no_clicked(self, e):
        self.control.handle_no()

    def yes_clicked(self, e):
        self.control.handle_yes()

    def pass_clicked(self, e):
        self.control.handle_pass()

    def reset_clicked(self, e):
        self.control.handle_reset()


class Data:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.gui2pth = Gui2Paths()
        self.data_path = self.gui2pth.find_words_dump_path
        self.exceptions_path = self.gui2pth.find_words_exceptions_path
        self.exceptions_dict: dict[str, int] = self.load_exceptions()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results = self.db_session.query(DpdHeadword).all()
        self.db_index = -1
        self.i2h_dict: defaultdict[str, set[str]] = self.make_i2h_dict()
        self.sentence_id: int
        self.word: str
        self.lemma: str
        self.headword: DpdHeadword | None
        self.source: str
        self.sutta: str
        self.example: str | None

    def load_exceptions(self) -> dict[str, int]:
        try:
            return json.loads(self.exceptions_path.read_text())
        except FileNotFoundError:
            return {}

    def update_exceptions(self):
        self.exceptions_dict[self.word] = self.headword.id
        self.exceptions_path.write_text(
            json.dumps(self.exceptions_dict, ensure_ascii=False, indent=2)
        )

    def make_i2h_dict(self):
        """
        Make a dictionary of all inflections without an example,
        mapped to their headword.
        """
        i2h_dict: defaultdict[str, set[str]] = defaultdict(set)
        for i in self.db_results:
            # Must have no example and a single meaning
            if i.example_1 == "" and not re.findall(r"\d", i.lemma_1):
                for inflection in i.inflections_list_all:
                    i2h_dict[inflection].add(i.lemma_1)

        # Reduce the dictionary to unambiguous examples with only one headword.
        # This can be adapted later.
        for i in list(i2h_dict):
            if len(i2h_dict[i]) != 1:
                del i2h_dict[i]

        return i2h_dict

    def cleaner(self, word: str) -> str:
        new_word: list[str] = []
        pali_alphabet.append(" ")
        for i in list(word):
            if i in pali_alphabet:
                new_word.append(i)
        return "".join(new_word)

    def clean_bold_tags(self, text) -> str:
        return re.sub(r"<.+?>", "", text)

    def find_next_example(self) -> None:
        """Iterate through all words in all examples and see if they match
        any entries in i2h_dict."""

        self.headword = None

        while not self.headword:
            self.db_index += 1
            if self.db_index >= len(self.db_results):
                break
            i = self.db_results[self.db_index]

            if i.example_1 != "":
                self.sentence_id = i.id
                # commentary is hardcoded for now, later add example_2 and commentary
                sentence: str = getattr(i, "commentary")
                clean_sentence: str = self.cleaner(sentence)
                if clean_sentence:
                    for word in clean_sentence.split():
                        if word in self.i2h_dict:
                            self.word = word
                            self.source = ""
                            self.sutta = ""
                            self.example = self.clean_bold_tags(i.commentary)
                            self.lemma = list(self.i2h_dict[word])[0]
                            result = (
                                self.db_session.query(DpdHeadword)
                                .filter(DpdHeadword.lemma_1 == self.lemma)
                                .first()
                            )
                            if (
                                result
                                and word not in self.exceptions_dict
                                and result.id != getattr(self.exceptions_dict, word, "")
                            ):
                                self.headword = result
                                return
                            else:
                                continue

    def save_data(self):
        data = json.dumps(
            [self.headword.id, self.source, self.sutta, self.example],
            ensure_ascii=False,
            indent=2,
        )
        self.data_path.write_text(data)


def run_gui(page):
    Controller(page)


if __name__ == "__main__":
    ft.app(target=run_gui)
