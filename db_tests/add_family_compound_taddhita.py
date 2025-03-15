"""
Add missing family compounds and idioms from taddhita.
"""

import json
import re
import time
from rich import print
import flet as ft
import queue

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyIdiom
from tools.paths import ProjectPaths
from tools.goldendict_tools import open_in_goldendict_os
from tools.tsv_read_write import read_tsv_dot_dict


class UiManager:
    def __init__(self, page: ft.Page, right_panel: ft.Container):
        self.page = page
        self.right_panel = right_panel
        self.label_width = 200
        self.textfield_width = 1000
        self.action_queue = queue.Queue()

        # Create UI components
        self.message_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.counter_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.id_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.lemma_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.pos_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.meaning_field = ft.TextField(read_only=True, width=self.textfield_width)
        self.family_compound_field = ft.TextField(
            value="",
            read_only=False,
            width=self.textfield_width,
            on_change=self._on_fc_change,
        )

        self.layout = self._create_layout()
        self.right_panel.content = self.layout
        self.page.update()
        self.update_message("loading database...")

    def _create_layout(self):
        return ft.Column(
            [
                ft.Row(
                    [ft.Text("message", width=self.label_width), self.message_field]
                ),
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
                        ft.Text("family compound", width=self.label_width),
                        self.family_compound_field,
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("", width=self.label_width),
                        ft.TextButton("Commit", on_click=self._on_commit_click),
                        ft.TextButton("Pass", on_click=self._on_pass_click),
                        ft.TextButton("Exit", on_click=self._on_exit_click),
                    ]
                ),
            ]
        )

    def update_fields(self, data: tuple[DpdHeadword, int, int, str]):
        i, counter, total_counter, positive = data
        self.message_field.value = ""
        self.counter_field.value = f"{counter} / {total_counter}"
        self.id_field.value = str(i.id)
        self.lemma_field.value = i.lemma_1
        self.pos_field.value = i.pos
        self.meaning_field.value = i.meaning_1
        self.family_compound_field.value = positive
        self.page.update()
        self.is_processing = True

    def _on_fc_change(self, e):
        """Handle changes to the positive field"""
        print(self.family_compound_field.value)

    def _on_commit_click(self, e):
        self.action_queue.put(("commit", self.get_family_compound()))
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

    def get_family_compound(self):
        return self.family_compound_field.value


class DataAndLogic:
    def __init__(self):
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.exceptions: list[int] = self.get_exceptions()
        self.items_to_process: list[DpdHeadword] = [
            i for i in self.db if self.should_process(i)
        ]
        print(self.items_to_process)
        self.fc_set = self.make_family_compound_and_idiom_set()

        self.current_item: DpdHeadword

        self.total_count = len(self.items_to_process)
        self.current_count = 0

    def get_exceptions(self):
        tests = read_tsv_dot_dict(self.pth.internal_tests_path)
        for line in tests:
            if line.test_name == "family_compound empty taddhita":
                return json.loads(line.exceptions)
        return []

    def should_process(self, i: DpdHeadword):
        return bool(
            i.meaning_1
            and i.derivative == "taddhita"
            and not i.family_compound
            and int(i.id) not in self.exceptions
        )

    def make_family_compound_and_idiom_set(self):
        fc_set = set()
        results_fc = self.db_session.query(FamilyCompound).all()
        fc_set = {i.compound_family for i in results_fc}
        results_id = self.db_session.query(FamilyIdiom).all()
        fc_set |= {i.idiom for i in results_id}
        return fc_set

    def update_current_item(self, i: DpdHeadword):
        self.current_item = i
        self.new_family_compound = self.make_family_compound()
        if self.new_family_compound:
            open_in_goldendict_os(self.new_family_compound)
        self.current_count += 1
        return (
            self.current_item,
            self.current_count,
            self.total_count,
            self.new_family_compound,
        )

    def make_family_compound(self):
        """
        1. it's already in family compounds
        2. from of|from
        3. as is
        """

        if self.current_item.lemma_clean in self.fc_set:
            return self.current_item.lemma_clean
        else:
            pattern = r"(?:of|from)\s+([^,]+)"
            match = re.search(pattern, self.current_item.grammar)
            if match:
                return match.group(1)
            else:
                return self.current_item.lemma_clean

    def commit_to_db(self, family_compound: str):
        if self.current_item:
            self.current_item.family_compound = family_compound
            self.current_item.family_idioms = family_compound
            self.db_session.commit()


def add_fc_taddhita(page: ft.Page, right_panel: ft.Container):
    """add missing family compounds from taddhita"""

    ui = UiManager(page, right_panel)
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
                elif action_type == "pass":
                    break
                elif action_type == "exit":
                    return
            time.sleep(0.1)


if __name__ == "__main__":
    pass
