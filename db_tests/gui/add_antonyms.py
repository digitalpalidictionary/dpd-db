"""
Add missing family compounds and idioms to su sur.
"""

from json import load
import queue
import time

import flet as ft
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict_os
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.negative_to_positive import make_positive
from db_tests.helpers import (
    make_internal_tests_list,
    write_internal_tests_list,
    InternalTestRow,
)


class UiManager:
    def __init__(self, e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container):
        self.pth = ProjectPaths()
        self.page = page
        if self.page.appbar:
            self.page.appbar.title = ft.Text(e.control.title.value)  # type: ignore
        self.right_panel = right_panel
        self.label_width = 200
        self.textfield_width = 700
        self.action_queue = queue.Queue()

        # Create UI components
        self.message_field = ft.Text(width=self.textfield_width)
        self.counter_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.id_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.lemma_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.pos_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.meaning_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.antonym_field = ft.TextField(
            value="",
            read_only=False,
            width=self.textfield_width,
            on_change=self._on_antonym_change,
        )
        self.results_field = ft.Text(
            width=self.textfield_width, expand=True, selectable=True
        )

        self.layout = self._create_layout()
        self.right_panel.content = self.layout
        self.page.update()
        self.update_message("loading database...")

        self.all_words = self.make_all_words_set()

    def show_all_matching_words(self):
        words = {
            word for word in self.all_words if word.startswith(self.antonym_field.value)
        }
        if words:
            words = sorted(words, key=len)[:20]
            self.results_field.value = ", ".join(words)
        else:
            self.results_field.value = "-"
        self.page.update()

    def make_all_words_set(self):
        all_words_set = set()
        with open(self.pth.cst_wordlist) as f:
            all_words_set.update(set(load(f)))
        with open(self.pth.bjt_wordlist) as f:
            all_words_set.update(set(load(f)))
        with open(self.pth.sc_wordlist) as f:
            all_words_set.update(set(load(f)))
        with open(self.pth.sya_wordlist) as f:
            all_words_set.update(set(load(f)))
        return all_words_set

    def _create_layout(self):
        return ft.Column(
            [
                ft.Row([ft.Text("", width=self.label_width), self.message_field]),
                ft.Row(
                    [ft.Text("counter", width=self.label_width), self.counter_field]
                ),
                ft.Row([ft.Text("id", width=self.label_width), self.id_field]),
                ft.Row([ft.Text("lemma_1", width=self.label_width), self.lemma_field]),
                ft.Row([ft.Text("pos", width=self.label_width), self.pos_field]),
                ft.Row(
                    [ft.Text("meaning_1", width=self.label_width), self.meaning_field]
                ),
                ft.Row(
                    [
                        ft.Text("antonym", width=self.label_width),
                        self.antonym_field,
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("", width=self.label_width),
                        ft.TextButton("Commit", on_click=self._on_commit_click),
                        ft.TextButton("Exception", on_click=self._on_exception_click),
                        ft.TextButton("Pass", on_click=self._on_pass_click),
                        ft.TextButton("Exit", on_click=self._on_exit_click),
                    ]
                ),
                ft.Divider(height=100, thickness=1),
                ft.Row(
                    [
                        ft.Text("", width=self.label_width),
                        self.results_field,
                    ]
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def update_fields(self, data: tuple[DpdHeadword, int, int, str]):
        i, counter, total_counter, positive = data
        self.message_field.value = ""
        self.counter_field.value = f"{counter} / {total_counter}"
        self.id_field.value = str(i.id)
        self.lemma_field.value = i.lemma_1
        self.pos_field.value = i.pos
        self.meaning_field.value = i.meaning_1
        self.antonym_field.value = positive
        self.results_field.value = ""
        self.show_all_matching_words()
        self.page.update()
        self.is_processing = True

    def _on_antonym_change(self, e):
        if self.antonym_field.value:
            open_in_goldendict_os(self.antonym_field.value)
        self.show_all_matching_words()

    def _on_commit_click(self, e):
        self.action_queue.put(("commit", self.get_antonym()))
        self.page.update()

    def _on_exception_click(self, e):
        self.action_queue.put(("exception", None))
        self.page.update()

    def _on_pass_click(self, e):
        self.action_queue.put(("pass", None))
        self.page.update()

    def _on_exit_click(self, e):
        self.action_queue.put(("exit", None))
        self.page.update()

    def get_next_action(self):
        try:
            return self.action_queue.get_nowait()
        except queue.Empty:
            return None

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def get_antonym(self):
        return self.antonym_field.value


class DataAndLogic:
    def __init__(self):
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.db = sorted(self.db, key=lambda x: pali_sort_key(x.lemma_1))
        self.internal_tests: list[InternalTestRow]
        self.exceptions: list[int] = self.get_exceptions()

        self.items_to_process: list[DpdHeadword] = [
            i for i in self.db if self.should_process(i)
        ]
        print([f"{i} {item}" for i, item in enumerate(self.items_to_process)])
        self.fc_set = self.make_antonym_set()

        self.current_item: DpdHeadword

        self.total_count = len(self.items_to_process)
        self.current_count = 0

    def get_exceptions(self):
        self.internal_tests: list[InternalTestRow] = make_internal_tests_list()
        for line in self.internal_tests:
            if line.test_name == "antonym: empty":
                return line.exceptions
        return []

    def should_process(self, i: DpdHeadword):
        return bool(
            i.meaning_1 and i.neg and not i.antonym and int(i.id) not in self.exceptions
        )

    def make_antonym_set(self):
        fc_set = set()
        return fc_set

    def update_current_item(self, i: DpdHeadword):
        self.current_item = i
        self.new_antonym = make_positive(i)
        if self.new_antonym:
            open_in_goldendict_os(self.new_antonym)
        self.current_count += 1
        return (
            self.current_item,
            self.current_count,
            self.total_count,
            self.new_antonym,
        )

    def commit_to_db(self, antonym: str):
        if self.current_item:
            self.current_item.antonym = antonym
            self.db_session.commit()

    def add_exception(self, id: int):
        test_name = "antonym: empty"
        test_row = next(
            (t for t in self.internal_tests if t.test_name == test_name), None
        )

        if test_row:
            if id not in test_row.exceptions:
                test_row.exceptions.append(id)
                test_row.exceptions = sorted(test_row.exceptions)

        write_internal_tests_list(self.internal_tests)


def add_antonyms(e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container):
    """add missing antonyms"""

    ui = UiManager(e, page, right_panel)
    lx = DataAndLogic()

    for i in lx.items_to_process:
        # update logix
        data_pack = lx.update_current_item(i)

        # update ui
        ui.update_fields(data_pack)

        # wait for user actions and process them
        while True:
            action = ui.get_next_action()
            if action:
                action_type, value = action
                if action_type == "commit":
                    if value:
                        lx.commit_to_db(value)
                    break
                elif action_type == "exception":
                    lx.add_exception(i.id)
                    break
                elif action_type == "pass":
                    break
                elif action_type == "exit":
                    return
            time.sleep(0.1)


if __name__ == "__main__":
    pass
