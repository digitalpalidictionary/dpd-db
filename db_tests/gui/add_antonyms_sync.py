"""
Add missing antonyms from existing words with antonyms.
"""

import queue
import time
from json import dump, load

import flet as ft
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths


class UiManager:
    def __init__(self, e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container):
        self.page = page
        self.right_panel = right_panel
        self.right_panel.padding = ft.padding.all(20)
        self.label_width = 200
        self.action_queue = queue.Queue()

        # Define color variables (two shades of the primary color)
        self.source_colour = ft.Colors.BLUE_GREY_500
        self.dest_colour = ft.Colors.BLUE_GREY_50

        # Create UI components
        self.message_field = ft.Text(color=self.source_colour, expand=True)
        self.source_id_field = ft.TextField(
            read_only=True, width=100, color=self.source_colour
        )
        self.source_pos_field = ft.TextField(
            read_only=True,
            width=80,
            color=self.source_colour,
        )
        self.source_lemma_field = ft.TextField(
            read_only=True, width=300, color=self.source_colour
        )
        self.source_meaning_field = ft.TextField(
            read_only=True, width=700, color=self.source_colour
        )
        self.source_root_field = ft.TextField(
            read_only=True,
            width=150,
            color=self.source_colour,
            expand=True,
        )

        self.dest_id_field = ft.TextField(
            read_only=True, width=100, color=self.dest_colour
        )
        self.dest_pos_field = ft.TextField(
            read_only=True,
            width=80,
            color=self.dest_colour,
        )
        self.dest_lemma_field = ft.TextField(
            read_only=True, width=300, color=self.dest_colour
        )
        self.dest_meaning_field = ft.TextField(
            read_only=True, width=700, color=self.dest_colour
        )
        self.dest_root_field = ft.TextField(
            read_only=True,
            width=150,
            color=self.dest_colour,
            expand=True,
        )

        self.dest_antonym_field = ft.TextField(
            value="",
            read_only=False,
            width=1010,
            autofocus=True,
            color=self.dest_colour,
        )

        self.history_field = ft.Text(
            color=self.source_colour,
            expand=True,
            selectable=True,
        )

        self.layout = self._create_layout()
        self.right_panel.content = self.layout
        self.page.update()
        self.update_message("loading database...")

    def _create_layout(self):
        return ft.Column(
            [
                ft.Row([self.message_field]),
                ft.Row(
                    [
                        self.dest_id_field,
                        self.dest_pos_field,
                        self.dest_lemma_field,
                        self.dest_meaning_field,
                        self.dest_root_field,
                    ]
                ),
                ft.Row(
                    [
                        self.source_id_field,
                        self.source_pos_field,
                        self.source_lemma_field,
                        self.source_meaning_field,
                        self.source_root_field,
                    ]
                ),
                ft.Row(
                    [
                        ft.Container(width=100),
                        ft.Container(width=80),
                        self.dest_antonym_field,
                    ],
                    alignment=ft.MainAxisAlignment.START,
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
                ft.Divider(height=50),
                ft.Row(
                    [
                        ft.Container(width=100),
                        ft.Container(width=80),
                        self.history_field,
                    ]
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    def update_fields(self, data: tuple):
        total_counter, counter, source, dest, dest_antonyms, history = data
        source: DpdHeadword
        dest: DpdHeadword

        self.message_field.value = f"{counter} / {total_counter}"
        self.source_id_field.value = str(source.id)
        self.source_pos_field.value = source.pos
        self.source_lemma_field.value = source.lemma_1
        self.source_meaning_field.value = source.meaning_combo
        self.source_root_field.value = f"{source.root_key} {source.family_root}"

        self.dest_id_field.value = str(dest.id)
        self.dest_pos_field.value = dest.pos
        self.dest_lemma_field.value = dest.lemma_1
        self.dest_meaning_field.value = dest.meaning_combo
        self.dest_antonym_field.value = ", ".join(dest_antonyms)
        self.dest_root_field.value = f"{dest.root_key} {dest.family_root}"
        self.history_field.value = "\n".join(history)

        self.page.update()

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
        if self.dest_antonym_field.value:
            return self.dest_antonym_field.value


def load_antonym_exceptions_dict(pth: ProjectPaths) -> dict:
    if pth.add_antonyms_sync_dict.exists():
        with open(pth.add_antonyms_sync_dict) as file:
            return load(file)
    else:
        print("[red]error opening antonym dict")
        return {}


def save_antonym_exceptions_dict(pth: ProjectPaths, antonym_exceptions_dict: dict):
    with open(pth.add_antonyms_sync_dict, "w") as file:
        dump(antonym_exceptions_dict, file, ensure_ascii=False, indent=2)


def update_exceptions(
    pth: ProjectPaths, antonym_exceptions_dict: dict, source_id: int, dest_id: int
):
    # json keys are strings
    source_id_key: str = str(source_id)

    if not antonym_exceptions_dict.get(source_id_key, []):
        antonym_exceptions_dict.update({source_id_key: []})

    if dest_id not in antonym_exceptions_dict[source_id_key]:
        antonym_exceptions_dict[source_id_key].append(dest_id)
        save_antonym_exceptions_dict(pth, antonym_exceptions_dict)

    print(antonym_exceptions_dict[source_id_key])


def commit_to_db(dest: DpdHeadword, dest_antonyms: str, db_session):
    dest.antonym = dest_antonyms
    db_session.commit()


def update_history(history, dest):
    history.insert(0, dest.lemma_1)
    return history[:10]


def make_dest_antonyms(source: DpdHeadword, dest: DpdHeadword):
    dest_antonyms = set(dest.antonym_list)
    dest_antonyms.add(source.lemma_clean)
    dest_antonyms = pali_list_sorter(dest_antonyms)
    return dest_antonyms


def add_antonyms_sync(e: ft.ControlEvent, page: ft.Page, right_panel: ft.Container):
    ui = UiManager(e, page, right_panel)
    pth = ProjectPaths()

    # load antonym exceptions dict
    antonym_exceptions_dict = load_antonym_exceptions_dict(pth)

    db_session = get_db_session(pth.dpd_db_path)

    sources = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.antonym != "")
        .filter(DpdHeadword.meaning_1 != "")
        .all()
    )
    sources = sorted(sources, key=lambda x: pali_sort_key(x.lemma_1))
    dests = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()
    dests = sorted(dests, key=lambda x: pali_sort_key(x.lemma_1))

    i: int
    sources: list[DpdHeadword]
    dests: list[DpdHeadword]
    source: DpdHeadword
    dest: DpdHeadword

    ui.update_message("processing antonyms...")
    # Create a dictionary for faster lookup
    dest_dict = {}
    for dest in dests:
        key = (dest.lemma_clean, dest.pos)
        if key not in dest_dict:
            dest_dict[key] = []
        dest_dict[key].append(dest)

    total_counter = len(sources)
    counter = 0
    history = []

    for i, source in enumerate(sources):
        print("source", source)
        counter += 1
        for antonym in source.antonym_list:
            antonym_key = (antonym, source.pos)
            if antonym_key in dest_dict:
                for dest in dest_dict[antonym_key]:
                    if (
                        source.lemma_clean not in dest.antonym_list
                        and dest.id
                        not in antonym_exceptions_dict.get(str(source.id), [])
                    ):
                        dest_antonyms = make_dest_antonyms(source, dest)
                        history = update_history(history, dest)

                        ui.update_fields(
                            (
                                total_counter,
                                counter,
                                source,
                                dest,
                                dest_antonyms,
                                history,
                            )
                        )

                        while True:
                            action = ui.get_next_action()
                            if action:
                                action_type, antonyms = action
                                if action_type == "commit":
                                    dest_antonyms = ui.get_antonym()
                                    commit_to_db(dest, antonyms, db_session)
                                    break
                                elif action_type == "exception":
                                    update_exceptions(
                                        pth, antonym_exceptions_dict, source.id, dest.id
                                    )
                                    break
                                if action_type == "pass":
                                    break
                                elif action_type == "exit":
                                    return
                            time.sleep(0.01)
