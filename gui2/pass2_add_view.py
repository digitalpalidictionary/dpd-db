import copy
import json
from collections.abc import Callable
from pathlib import Path

import flet as ft

from db.models import DpdHeadword
from gui2.dpd_fields import DpdFields
from gui2.dpd_fields_commentary import DpdCommentaryField
from gui2.dpd_fields_examples import DpdExampleField
from gui2.dpd_fields_functions import clean_lemma_1, increment_lemma_1
from gui2.dpd_fields_lists import (
    COMPOUND_FIELDS,
    NO_CLONE_LIST,
    NO_SPLIT_LIST,
    PASS1_FIELDS,
    ROOT_FIELDS,
    SUTTA_FIELDS,
    WORD_FIELDS,
)
from gui2.mixins import PopUpMixin
from gui2.pass2_auto_control import Pass2AutoController
from gui2.pass2_auto_file_manager import Pass2AutoFileManager
from gui2.pass2_eg_manager import Pass2EgManager
from gui2.pass2_pre_new_word_manager import Pass2NewWordManager
from gui2.pass2_x_manager import Pass2XManager
from gui2.toolkit import ToolKit
from scripts.find.missing_meanings import find_missing_meanings
from tools.fast_api_utils import request_dpd_server
from tools.speech_marks import SpeechMarkManager

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass2AddView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )
        from gui2.test_manager import GuiTestManager

        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self._db = self.toolkit.db_manager
        self._daily_log = self.toolkit.daily_log
        self.pass2_auto_controller = Pass2AutoController(self, self.toolkit)
        self.test_manager: GuiTestManager = self.toolkit.test_manager
        self.toolkit: ToolKit = toolkit

        self.speech_marks_manager: SpeechMarkManager = self.toolkit.speech_marks_manager
        self.speech_marks_dict = self.speech_marks_manager.get_speech_marks()
        self.history_manager = self.toolkit.history_manager
        self.history_manager.register_refresh_callback(self._update_history_dropdown)
        self.corrections_manager = self.toolkit.corrections_manager
        self.additions_manager = self.toolkit.additions_manager
        self._x_manager = Pass2XManager(self._db)

        self.dpd_fields: DpdFields
        self._pass2_auto_file_manager = Pass2AutoFileManager(self.toolkit)
        self.pass2_new_word_manager: Pass2NewWordManager = (
            self.toolkit.pass2_new_word_manager
        )
        self.pass2_eg_manager: Pass2EgManager = Pass2EgManager(self.toolkit)
        self._eg_alert: ft.AlertDialog | None = None
        self._eg_checkboxes: dict[str, ft.Checkbox] = {}
        self._eg_prefills: dict[str, dict[str, str]] = {}
        self._eg_comment: str = ""
        self._eg_section_textboxes: list[tuple[ft.TextField, dict[str, str]]] = []
        self._eg_saved_kb: Callable[[ft.KeyboardEvent], None] | None = None
        self.headword: DpdHeadword | None = None
        self.headword_original: DpdHeadword | None = None
        self.current_correction: dict | None = None
        self.current_addition: dict | None = None
        self._current_addition_origin: Path | None = None
        self._current_addition_key: str | None = None
        self._current_correction_origin: Path | None = None
        self._current_correction_key: str | None = None

        self._message_field = ft.TextField(
            "",
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
            color=ft.Colors.BLUE_200,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Messages",
            read_only=True,
            text_size=14,
            width=700,
        )
        self._pass2_auto_button = ft.ElevatedButton(
            "P2A",
            on_click=self._click_load_pass2_auto,
            on_hover=self._update_count_tooltip,
            tooltip="Next Pass2Auto",
        )
        self._new_word_button = ft.ElevatedButton(
            "New",
            on_click=self._click_load_new_word,
            on_hover=self._update_count_tooltip,
            tooltip="Next new word",
        )
        self._corrections_button = ft.ElevatedButton(
            "Cor",
            on_click=self._click_corrections_button,
            on_hover=self._update_count_tooltip,
            tooltip="corrections",
        )
        self._additions_button = ft.ElevatedButton(
            "Add",
            on_click=self._click_additions_button,
            on_hover=self._update_count_tooltip,
            tooltip="additions",
        )
        self._x_button = ft.ElevatedButton(
            "X",
            on_click=self._click_x_button,
            on_hover=self._update_count_tooltip,
            tooltip="filter queue",
        )
        self._eg_button = ft.ElevatedButton(
            "Eg",
            on_click=self._click_eg_button,
            on_hover=self._update_count_tooltip,
            tooltip="eg queue",
        )
        self._pread_button = ft.ElevatedButton(
            "PRead",
            on_click=self._click_pread_button,
            on_hover=self._update_count_tooltip,
            tooltip="proofreader",
        )
        self._enter_id_or_lemma_field = ft.TextField(
            "",
            autofocus=True,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Enter ID or Lemma",
            on_submit=self._click_edit_headword,
            on_blur=self._disable_id_field_autofocus,
            text_size=14,
            width=400,
        )
        self._clone_headword_button = ft.ElevatedButton(
            "Clone", on_click=self._click_clone_headword
        )
        self._split_headword_button = ft.ElevatedButton(
            "Split", on_click=self._click_split_headword
        )
        self._clear_all_button = ft.ElevatedButton(
            "Clear All", on_click=self._click_clear_all
        )
        self._missing_words_switch = ft.Switch(
            label="Missing Words",
            value=True,
        )
        self._action_menu_button = ft.PopupMenuButton(
            icon=ft.Icons.ARROW_DROP_DOWN,
            tooltip="Actions",
            items=[
                ft.PopupMenuItem(
                    text="Update Speech Marks",
                    on_click=self._click_update_sandhi,
                ),
                ft.PopupMenuItem(
                    text="AiAutofill",
                    on_click=self._click_update_with_ai,
                ),
                ft.PopupMenuItem(),  # divider
                ft.PopupMenuItem(content=self._missing_words_switch),
            ],
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="History",
            hint_style=ft.TextStyle(color=ft.Colors.BLUE_200),
            options=[],
            expand=True,
            expand_loose=True,
            border_radius=20,
            text_size=14,
            on_change=self._handle_history_selection,
        )

        # --- Field Filter Radio Buttons ---
        self._filter_radios = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="all", label="All"),
                    ft.Radio(value="root", label="Root"),
                    ft.Radio(value="compound", label="Compound"),
                    ft.Radio(value="sutta", label="Sutta"),
                    ft.Radio(value="word", label="Word"),
                    ft.Radio(value="pass1", label="Pass1"),
                ]
            ),
            value="all",  # Default selection
            on_change=self._handle_filter_change,
        )

        # Define the Add to DB button as a member variable
        self._add_to_db_button = ft.ElevatedButton(
            "Add to DB",
            on_click=self._click_add_to_db,
            width=BUTTON_WIDTH,
        )
        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._enter_id_or_lemma_field,
                            self._clone_headword_button,
                            self._split_headword_button,
                            self._pass2_auto_button,
                            self._new_word_button,
                            self._eg_button,
                            self._corrections_button,
                            self._additions_button,
                            self._x_button,
                            self._pread_button,
                            self._clear_all_button,
                            self._history_dropdown,
                            self._action_menu_button,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row([self._message_field, self._filter_radios]),
                ],
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        # Build middle section using the new method
        self._middle_section = self._build_middle_section()

        # Populate history dropdown initially
        self._update_history_dropdown()

        self._bottom_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Test",
                                on_click=self._click_run_tests,
                                width=BUTTON_WIDTH,
                            ),
                            self._add_to_db_button,  # Use the member variable here
                            ft.ElevatedButton(
                                "Delete",
                                on_click=self._click_delete_from_db,
                                width=BUTTON_WIDTH,
                                on_hover=self._on_delete_hover,
                            ),
                        ],
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Stash",
                                on_click=self._click_stash,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Unstash",
                                on_click=self._click_unstash,
                                width=BUTTON_WIDTH,
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )

        self.controls = [
            self._top_section,
            self._middle_section,
            self._bottom_section,
        ]

    def _disable_id_field_autofocus(self, e: ft.ControlEvent) -> None:
        if self._enter_id_or_lemma_field.autofocus:
            self._enter_id_or_lemma_field.autofocus = False

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    def _update_count_tooltip(self, e: ft.ControlEvent) -> None:
        if e.data != "true":
            return
        if e.control is self._pread_button:
            field, count = self.toolkit.proofreader_manager.next_queue_status()
            label = field or "proofreader"
            e.control.tooltip = f"{label} — {count} remaining"
            e.control.update()
            return
        counts = {
            id(self._pass2_auto_button): (
                "Next Pass2Auto",
                lambda: len(self._pass2_auto_file_manager.pass2_auto_data),
            ),
            id(self._new_word_button): (
                "Next new word",
                lambda: len(self.pass2_new_word_manager.new_words_dict),
            ),
            id(self._corrections_button): (
                "corrections",
                lambda: len(self.corrections_manager.corrections_dict),
            ),
            id(self._additions_button): (
                "additions",
                lambda: len(self.additions_manager.additions_dict),
            ),
            id(self._x_button): (
                "filter queue",
                lambda: self._x_manager.remaining_count(),
            ),
            id(self._eg_button): (
                "eg queue",
                lambda: self.pass2_eg_manager.count(),
            ),
        }
        entry = counts.get(id(e.control))
        if entry is None:
            return
        base, count_fn = entry
        e.control.tooltip = f"{base} — {count_fn()} remaining"
        e.control.update()

    def _click_stash(self, e: ft.ControlEvent) -> None:
        """Save all current field values to a JSON stash file."""
        values = self.dpd_fields.get_current_values()
        if not values.get("lemma_1"):
            self.update_message("Nothing to stash")
            return

        stash_path = self.toolkit.paths.headword_stash_json_path
        try:
            stash_path.parent.mkdir(parents=True, exist_ok=True)
            with open(stash_path, "w", encoding="utf-8") as f:
                json.dump(values, f, indent=4, ensure_ascii=False)
        except (OSError, TypeError, ValueError) as ex:
            self.update_message(f"Stash failed: {ex}")
            return

        self.update_message(f"Stashed: {values.get('lemma_1', '')}")

    def _click_unstash(self, e: ft.ControlEvent) -> None:
        """Restore field values from the JSON stash file."""
        stash_path = self.toolkit.paths.headword_stash_json_path
        if not stash_path.exists():
            self.update_message("No stash found")
            return

        try:
            with open(stash_path, "r", encoding="utf-8") as f:
                values = json.load(f)
        except (json.JSONDecodeError, OSError) as ex:
            self.update_message(f"Failed to read stash: {ex}")
            return

        if not isinstance(values, dict) or not values:
            self.update_message("Stash is empty or invalid")
            return

        self.clear_all_fields()
        for name, value in values.items():
            if name in self.dpd_fields.fields:
                self.dpd_fields.fields[name].value = value

        stashed_id = values.get("id", "")
        if stashed_id:
            try:
                headword = self._db.get_headword_by_id(int(stashed_id))
                if headword:
                    self.headword = headword
                    self.headword_original = copy.deepcopy(headword)
            except (ValueError, TypeError):
                pass

        self.update_message(f"Unstashed: {values.get('lemma_1', '')}")
        self.page.update()

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()

    def add_headword_to_examples_and_commentary(self) -> None:
        # add headword to example_1 example_2 and commentary
        # if self.headword:
        lemma_1 = self.dpd_fields.get_field("lemma_1").value
        if lemma_1:
            lemma_clean = clean_lemma_1(lemma_1)
            commentary_field: DpdCommentaryField = self.dpd_fields.get_field(
                "commentary"
            )
            if commentary_field and hasattr(commentary_field, "search_field_1"):
                commentary_field.search_field_1.value = lemma_clean[:-1]

            example_1_field: DpdExampleField = self.dpd_fields.get_field("example_1")
            if example_1_field and hasattr(example_1_field, "word_to_find_field"):
                example_1_field.word_to_find_field.value = lemma_clean[:-1]
                example_1_field.bold_field.value = lemma_clean[:-1]

            example_2_field: DpdExampleField = self.dpd_fields.get_field("example_2")
            if example_2_field and hasattr(example_2_field, "word_to_find_field"):
                example_2_field.word_to_find_field.value = lemma_clean[:-1]
                example_2_field.word_to_find_field.value = lemma_clean[:-1]

        self._apply_sutta_prefill()

    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        id_or_lemma = ""
        if self._enter_id_or_lemma_field.value:
            id_or_lemma = self._enter_id_or_lemma_field.value.strip()

        if id_or_lemma:
            headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
            if headword:
                self.clear_all_fields()
                self.headword = headword
                self._enter_id_or_lemma_field.value = headword.lemma_1  # show the word
                self.headword_original = copy.deepcopy(
                    headword
                )  # Store original for ID comparison
                self.dpd_fields.update_db_fields(headword)

                self.add_headword_to_examples_and_commentary()

                if self.headword is not None:
                    self.update_message(f"loaded {self.headword.lemma_clean}")

                    # load pass2auto if available
                    if (
                        self.headword.id is not None
                        and str(self.headword.id)
                        in self._pass2_auto_file_manager.pass2_auto_data
                    ):
                        to_add = self._pass2_auto_file_manager.get_headword(
                            str(self.headword.id)
                        )
                        self.dpd_fields.update_add_fields(to_add)
            else:
                self.update_message("headword not found")
        else:
            self.update_message("you're shooting blanks")

    def _click_clone_headword(self, e: ft.ControlEvent) -> None:
        """Fetches a headword and adds its data to empty fields in the current view."""
        id_or_lemma = self._enter_id_or_lemma_field.value

        if not id_or_lemma:
            self.update_message("Enter an ID or Lemma to clone from.")
            return

        headword_to_clone = self._db.get_headword_by_id_or_lemma(id_or_lemma)

        if not headword_to_clone:
            self.update_message(f"Headword '{id_or_lemma}' not found for cloning.")
            return

        cloned_count = 0
        for field_name, ui_field in self.dpd_fields.fields.items():
            if (
                hasattr(headword_to_clone, field_name)
                and field_name not in NO_CLONE_LIST
                and not ui_field.value
            ):
                db_value = getattr(headword_to_clone, field_name)
                if db_value is not None:  # Only clone non-None values
                    ui_field.value = db_value
                    cloned_count += 1

        self.update_message(
            f"Cloned {cloned_count} fields from {headword_to_clone.lemma_1}."
        )
        self.page.update()

    def _click_split_headword(self, e: ft.ControlEvent) -> None:
        """Copies current fields to a new ID, increments lemma_1, and clears specific fields."""
        current_lemma_1_field = self.dpd_fields.get_field("lemma_1")
        if not current_lemma_1_field or not current_lemma_1_field.value:
            self.update_message("Cannot split an entry with an empty lemma_1.")
            return

        old_lemma = current_lemma_1_field.value
        new_id = self._db.get_next_id()
        new_lemma = increment_lemma_1(old_lemma)

        cleared_count = 0
        for field_name, ui_field in self.dpd_fields.fields.items():
            if field_name == "id":
                ui_field.value = str(new_id)  # Ensure ID is string for TextField
            elif field_name == "lemma_1":
                ui_field.value = new_lemma
            elif field_name in NO_SPLIT_LIST:
                if ui_field.value:  # Only count if it actually had a value
                    cleared_count += 1
                ui_field.value = ""
                ui_field.error_text = None  # Clear errors too
            # else: field keeps its current value

        # Reset flags as this is effectively a new entry state
        self.dpd_fields.flags.reset()

        # Clear _add fields as they relate to the original word's auto-data
        self.dpd_fields.clear_fields(target="add")

        self.update_message(f"Split {old_lemma} into {new_lemma} id: {new_id})")
        self.page.update()
        current_lemma_1_field.focus()

    def _click_load_new_word(self, e: ft.ControlEvent | None = None) -> None:
        """Load next new word into the view."""
        new_word_data = self.pass2_new_word_manager.get_next_new_word()
        word_in_text, source_sutta_example = new_word_data
        if source_sutta_example:
            self.clear_all_fields()
            # Show the saved comment in the existing message field
            saved_comment = ""
            if isinstance(source_sutta_example, dict):
                saved_comment = str(source_sutta_example.get("comment", ""))

            remaining = len(self.pass2_new_word_manager.new_words_dict)
            prefix = f"[{remaining}] {word_in_text}"

            self.update_message(
                prefix if not saved_comment else f"{prefix}: {saved_comment}"
            )
            self.dpd_fields.update_add_fields(source_sutta_example)
        else:
            self.clear_all_fields()
            self.update_message("No more new words")
        self.update()

    def _click_load_pass2_auto(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2_auto entry into the view."""
        headword_id, pass2_auto_data, count = (
            self._pass2_auto_file_manager.get_next_headword_data()
        )

        if headword_id is not None:
            self.clear_all_fields()
            headword = self._db.get_headword_by_id(int(headword_id))

            if headword is not None:
                self.update_message(f"{headword.lemma_1}. {count} pass2auto remaining")
                self.headword = headword
                self.headword_original = copy.deepcopy(headword)

                self.dpd_fields.update_db_fields(self.headword)
                self.dpd_fields.update_add_fields(pass2_auto_data)
                self.add_headword_to_examples_and_commentary()
            else:
                self.update_message(f"{headword_id}: headword not found—deleting")
                self._pass2_auto_file_manager.delete_item(headword_id)
                self._click_load_pass2_auto()

        else:
            self.clear_all_fields()
            self.update_message("No more pass2auto entries")

        self.update()

    def _click_clear_all(self, e: ft.ControlEvent) -> None:
        self.clear_all_fields()

    def _click_update_sandhi(self, e: ft.ControlEvent) -> None:
        self.update_message("updating speech marks... please wait...")
        self.speech_marks_manager.regenerate_from_db()
        self.speech_marks_dict = self.speech_marks_manager.get_speech_marks()
        self.update_message("speech marks updated")

    def _apply_sutta_prefill(self) -> None:
        """If sutta filter is active, prefill empty source_1 and commentary with '-'."""
        if self._filter_radios.value != "sutta":
            return
        for prefill_name in ("source_1", "commentary"):
            prefill_field = self.dpd_fields.get_field(prefill_name)
            if prefill_field is not None and not prefill_field.value:
                prefill_field.value = "-"

    def _handle_filter_change(self, e: ft.ControlEvent) -> None:
        """Handles changes in the field filter RadioGroup."""
        filter_type = e.control.value
        visible_fields = None  # Default to all

        if filter_type == "root":
            visible_fields = ROOT_FIELDS
        elif filter_type == "compound":
            visible_fields = COMPOUND_FIELDS
        elif filter_type == "sutta":
            visible_fields = SUTTA_FIELDS
            self._apply_sutta_prefill()
        elif filter_type == "word":
            visible_fields = WORD_FIELDS
        elif filter_type == "pass1":
            visible_fields = PASS1_FIELDS

        self.dpd_fields.filter_fields(visible_fields)
        self.page.update()

    def _update_history_dropdown(self) -> None:
        """Populates the history dropdown with the latest history."""
        history_items = self.history_manager.get_history()
        if self._history_dropdown.options is not None:
            self._history_dropdown.options.clear()
            for item in history_items:
                self._history_dropdown.options.append(
                    ft.dropdown.Option(
                        key=str(item.get("id")),  # Key must be string for Dropdown
                        text=f"{item.get('id')}: {item.get('lemma_1', 'N/A')}",
                    )
                )
        self.page.update()

    def _handle_history_selection(self, e: ft.ControlEvent) -> None:
        """Loads the selected headword from history."""
        selected_id_str = e.control.value
        if selected_id_str:
            try:
                selected_id = int(selected_id_str)
                headword = self._db.get_headword_by_id(selected_id)
                if headword:
                    # Use existing logic similar to _click_edit_headword
                    self.clear_all_fields()
                    self.headword = headword
                    self.headword_original = copy.deepcopy(headword)
                    self.dpd_fields.update_db_fields(headword)
                    self.add_headword_to_examples_and_commentary()
                    self.update_message(
                        f"loaded {self.headword.lemma_clean} from history"
                    )
                    # Optionally load Pass2Auto data here if needed
                else:
                    self.update_message(
                        f"History item ID {selected_id} not found in DB"
                    )
            except ValueError:
                self.update_message("Invalid history item ID selected")
            finally:
                self._history_dropdown.value = None  # Reset dropdown selection
                self.page.update()

    # Add the new builder method
    def _build_middle_section(self) -> ft.Column:
        """Build and return the middle section with DpdFields."""
        self.dpd_fields = DpdFields(self, self._db, self.toolkit)
        middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=5,
            # Add any other specific Column properties if needed
        )
        self.dpd_fields.add_to_ui(middle_section, include_add_fields=True)
        return middle_section

    def clear_all_fields(
        self, e: ft.ControlEvent | None = None
    ) -> None:  # Add event arg if needed for button binding
        """Clear all fields by rebuilding the middle section."""
        # Rebuild middle section
        self._middle_section = self._build_middle_section()

        # Update view controls with new middle section
        self.controls = [self._top_section, self._middle_section, self._bottom_section]

        # Clear relevant top-section fields
        self._enter_id_or_lemma_field.value = ""
        self._enter_id_or_lemma_field.error_text = None
        self.headword = None  # Resetting the data model reference
        if self._filter_radios.value == "sutta":
            self._apply_sutta_prefill()
            self.dpd_fields.filter_fields(SUTTA_FIELDS)
        else:
            self._filter_radios.value = "all"  # Reset filter to 'all'
        self.headword_original = None  # Resetting the original data reference
        self.current_correction = None
        self.current_addition = None
        self._current_addition_origin = None
        self._current_addition_key = None
        self._current_correction_origin = None
        self._current_correction_key = None

        self.update_message("")  # Clear message field
        self.page.update()

    def _click_run_tests(self, e: ft.ControlEvent) -> None:
        """Run tests on current field values"""

        # Get the lemma_1 field and its value first
        lemma_1_field = self.dpd_fields.get_field("lemma_1")
        lemma_1_value = lemma_1_field.value if lemma_1_field else None

        # Check if lemma_1 has a value
        if lemma_1_value and str(lemma_1_value).strip():
            # lemma_1 has a value, proceed to get headword and run tests
            headword = (
                self.dpd_fields.get_current_headword()
            )  # Now we expect this to succeed
            if (
                headword
            ):  # Double check just in case get_current_headword has other failure modes
                self.dpd_fields.clear_messages()
                self.test_manager.run_all_tests(self, headword)
                # Change button color based on test results
                if hasattr(self.test_manager, "passed") and self.test_manager.passed:
                    self._add_to_db_button.color = ft.Colors.GREEN
                else:
                    self._add_to_db_button.color = None
            else:
                # Should ideally not happen if lemma_1 has value, but handle defensively
                self.update_message("Error creating headword")
                self._add_to_db_button.color = None
        else:
            # No lemma_1 value, open the test file instead
            self.update_message("Opening tests TSV...")
            self.test_manager._handle_open_test_file(e)
            self._add_to_db_button.color = None
        self.page.update()

    def _click_add_to_db(self, e: ft.ControlEvent) -> None:
        """Add the word to db, or update in db."""

        if not self._db.is_db_loaded():
            self.update_message("Database still loading — please wait before saving.")
            return

        word_to_save = self.dpd_fields.get_current_headword()
        comment = self.dpd_fields.get_field("comment").value

        for field_name in ("meaning_1", "meaning_lit"):
            field = self.dpd_fields.get_field(field_name)
            value = field.value if field else ""
            if value:
                misspelled = self.dpd_fields.spellchecker.check_sentence(value)
                if misspelled:
                    error_string = ", ".join(misspelled.keys())
                    self.update_message(
                        f"spelling mistakes in {field_name}: {error_string}"
                    )
                    return

        if (
            hasattr(self, "headword")
            and self.headword
            and hasattr(self, "headword_original")
            and self.headword_original
            and word_to_save.id
            == self.headword_original.id  # Compare ID from UI state with original
        ):
            # it's an update if this block runs
            committed, message = self._db.update_word_in_db(word_to_save)
            log_key = "pass2_update"

            if self.toolkit.username_manager.is_not_primary():
                # if not in additions then add to corrections
                if self.toolkit.additions_manager.is_not_in_additions(word_to_save.id):
                    self.corrections_manager.update_corrections(word_to_save, comment)

                # if in additions then update to additions
                else:
                    self.additions_manager.add_additions(word_to_save, comment)
        else:
            # Check for duplicate id or lemma_1 when adding a new word
            if not self.dpd_fields.validate_no_duplicates(
                word_to_save.id, word_to_save.lemma_1
            ):
                return

            # add to additions json
            if self.toolkit.username_manager.is_not_primary():
                self.additions_manager.add_additions(word_to_save, comment)

            # add to db
            committed, message = self._db.add_word_to_db(word_to_save)

            log_key = "pass2_add"
            item_to_history = word_to_save

        if committed:
            request_dpd_server(str(word_to_save.id))
            item_id = (
                self.headword.id
                if hasattr(self, "headword") and self.headword
                else item_to_history.id
            )
            item_lemma = (
                self.headword.lemma_1
                if hasattr(self, "headword") and self.headword
                else item_to_history.lemma_1
            )

            if log_key == "pass2_add":
                item_id = item_to_history.id
                item_lemma = item_to_history.lemma_1
            else:
                item_id = self.headword.id if self.headword else None
                item_lemma = self.headword.lemma_1 if self.headword else ""

            if item_id is not None:
                was_new_to_history = self.history_manager.add_item(item_id, item_lemma)
            else:
                was_new_to_history = False

            if was_new_to_history:
                self._daily_log.increment(log_key)

            if item_id is not None:
                removed_from_auto = self._pass2_auto_file_manager.delete_item(
                    str(item_id)
                )
                if removed_from_auto:
                    self.update_message(f"Removed ID {item_id} from pass2_auto.json")

            # Save addition if flag is set
            if (
                hasattr(self.dpd_fields.flags, "addition")
                and self.dpd_fields.flags.addition
            ):
                word_data = self.dpd_fields.get_current_values()
                if word_data:
                    self.additions_manager.save_processed_addition(
                        word_data,
                        self._current_addition_origin,
                        self._current_addition_key,
                    )

            # Save correction if flag is set
            if self.dpd_fields.flags.correction:
                word_data = self.dpd_fields.get_current_values()
                if word_data:
                    # Fix:
                    # Base fields = the original PROPOSAL (from corrections.json)
                    # _add fields = the final modified GUI values (the user's result)
                    if hasattr(self, "current_correction") and self.current_correction:
                        current_gui_values = copy.deepcopy(word_data)
                        for key in word_data:
                            if key.endswith("_add"):
                                # Set logged _add field to the current UI BASE field value
                                base_key = key[:-4]
                                word_data[key] = current_gui_values.get(base_key, "")
                            else:
                                # Set logged base field to the original PROPOSAL value
                                if key in self.current_correction:
                                    val = self.current_correction[key]
                                    word_data[key] = str(val) if val is not None else ""
                                # Otherwise keep current UI value if not in correction (e.g. ID)

                    self.corrections_manager.save_processed_correction(
                        word_data,
                        self._current_correction_origin,
                        self._current_correction_key,
                    )

            self.page.set_clipboard(word_to_save.lemma_1)

            self._update_history_dropdown()
            self.page.update()
            self.clear_all_fields()
            self._show_missing_words_dialog(word_to_save)
        else:
            self.update_message(f"Commit failed: {message}")

        self._add_to_db_button.color = ft.Colors.RED
        self.page.update()

    def _click_update_with_ai(self, e: ft.ControlEvent) -> None:
        """Handles the 'Update with AI' button click."""
        current_headword = self.dpd_fields.get_current_headword()
        if not current_headword or not current_headword.id:
            self.update_message("Load or create a headword first.")
            return

        self.update_message(f"Requesting AI update for {current_headword.lemma_1}...")

        # Call the controller's single-word processing method
        # Pass None for sentence_data for now
        response_dict = self.pass2_auto_controller.process_single_headword_from_view(
            current_headword
        )

        if response_dict:
            self.dpd_fields.update_add_fields(response_dict)
            self.update_message(
                f"AI suggestions loaded for {current_headword.lemma_1}."
            )
        else:
            self.update_message(f"AI update failed for {current_headword.lemma_1}.")

    def _click_delete_from_db(self, e: ft.ControlEvent) -> None:
        self.dpd_fields.clear_messages()

        if not self.headword:
            self.headword = self.dpd_fields.get_current_headword()

        self.delete_alert = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[
                    ft.Text("Delete Confirmation", color=ft.Colors.RED_900, size=20),
                    ft.Text("Are you sure you want to delete?"),
                    ft.Text(
                        str(self.headword.id),
                        color=ft.Colors.BLUE_200,
                        selectable=True,
                    ),
                    ft.Text(
                        self.headword.lemma_1,
                        color=ft.Colors.BLUE_200,
                        selectable=True,
                    ),
                ],
                height=150,
                width=500,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            actions=[
                ft.TextButton("OK", on_click=self._click_delete_ok),
                ft.TextButton("Cancel", on_click=self._click_delete_cancel),
            ],
        )

        self.page.open(self.delete_alert)
        self.page.update()

    def _click_delete_ok(self, e: ft.ControlEvent) -> None:
        self.delete_alert.open = False
        self.page.update()

        if not self._db.is_db_loaded():
            self.update_message("Database still loading — please wait before deleting.")
            return

        if self.headword:
            deleted, message = self._db.delete_word_in_db(self.headword)
            if deleted:
                self.update_message(f"{self.headword.id} deleted from database")
            else:
                self.update_message(f"Delete failed: {message}")
            self.clear_all_fields()
        else:
            self.update_message("No headword to delete")

    def _click_delete_cancel(self, e: ft.ControlEvent) -> None:
        self.delete_alert.open = False
        self.page.update()

    def _click_corrections_button(self, e: ft.ControlEvent) -> None:
        """Loads the next correction and populates the _add fields."""
        correction_data, origin, source_key, corrections_remaining = (
            self.corrections_manager.get_next_correction()
        )

        if not correction_data:
            self.update_message("No more corrections available")
            return

        self.current_correction = copy.deepcopy(correction_data)
        self._current_correction_origin = origin
        self._current_correction_key = source_key

        try:
            # Clear any existing add fields
            self.dpd_fields.clear_fields()

            # Optionally load corresponding headword if ID is available
            if "id" in correction_data:
                try:
                    headword_id = int(correction_data["id"])
                    headword = self._db.get_headword_by_id(headword_id)
                    if headword:
                        self.headword = headword
                        self.headword_original = copy.deepcopy(headword)
                        self.dpd_fields.update_db_fields(headword)
                        self.add_headword_to_examples_and_commentary()
                except ValueError:
                    pass

            # Map correction data to add fields
            processed_correction: dict[str, str] = {}
            for field_name, value in correction_data.items():
                processed_correction[field_name] = str(value)
                if field_name in self.dpd_fields.fields:
                    add_field = f"{field_name}_add"
                    if hasattr(self.dpd_fields, add_field):
                        getattr(self.dpd_fields, add_field).value = value

            self.dpd_fields.update_add_fields(processed_correction)

            # Set correction flag
            self.dpd_fields.flags.correction = True

            # Update message with lemma if available
            lemma = correction_data.get("lemma_1", "unknown")
            self.update_message(
                f"Loaded correction for {lemma}. {corrections_remaining} corrections remaining."
            )

        except Exception as ex:  # noqa: BLE001
            self.update_message(f"Error loading correction: {ex!s}")

        self.page.update()

    def _click_additions_button(self, e: ft.ControlEvent) -> None:
        """Loads the next addition and populates the _add fields."""
        addition_data, origin, source_key, additions_remaining = (
            self.additions_manager.get_next_addition()
        )

        if not addition_data:
            self.update_message("No more additions available")
            return

        self.current_addition = copy.deepcopy(addition_data)
        self._current_addition_origin = origin
        self._current_addition_key = source_key

        try:
            # Clear any existing fields
            self.dpd_fields.clear_fields()

            # Do not load headword for additions, as per request

            # Map addition data to add fields
            processed_addition: dict[str, str] = {}
            for field_name, value in addition_data.items():
                processed_addition[field_name] = str(value)
                if field_name in self.dpd_fields.fields:
                    add_field = f"{field_name}_add"
                    if hasattr(self.dpd_fields, add_field):
                        getattr(self.dpd_fields, add_field).value = value

            self.dpd_fields.update_add_fields(processed_addition)

            # Set addition flag
            self.dpd_fields.flags.addition = True

            # Update message with lemma if available
            lemma = addition_data.get("lemma_1", "unknown")
            self.update_message(
                f"Loaded addition for {lemma}. {additions_remaining} additions remaining."
            )

        except Exception as ex:  # noqa: BLE001
            self.update_message(f"Error loading addition: {ex!s}")

        self.page.update()

    def _click_x_button(self, e: ft.ControlEvent) -> None:
        """Loads the next headword from the X filter queue."""
        if self._x_manager._loaded and not self._x_manager._queue:
            # Re-read pass2_x_manager.py from disk so edits to filter_query
            # take effect without restarting the app. Bypasses sys.modules
            # and __pycache__ — importlib.reload was not reliably picking
            # up changes.
            import importlib.util

            path = self.toolkit.paths.pass2_x_manager_py_path
            spec = importlib.util.spec_from_file_location(
                f"pass2_x_manager_live_{id(self)}", path
            )
            assert spec is not None and spec.loader is not None
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._x_manager = mod.Pass2XManager(self._db)

        headword_id, remaining = self._x_manager.get_next()

        if headword_id is None:
            self.update_message("No more X words")
            self.page.update()
            return

        try:
            headword = self._db.get_headword_by_id(headword_id)
            if not headword:
                self.update_message(f"Headword ID {headword_id} not found in DB")
                self.page.update()
                return

            self.clear_all_fields()
            self.headword = headword
            self._enter_id_or_lemma_field.value = headword.lemma_1
            self.headword_original = copy.deepcopy(headword)
            self.dpd_fields.update_db_fields(headword)
            self.add_headword_to_examples_and_commentary()

            self.update_message(
                f"Loaded {headword.lemma_clean}. {remaining} X remaining."
            )
        except Exception as ex:  # noqa: BLE001
            self.update_message(f"Error loading X word: {ex!s}")

        self.page.update()

    @staticmethod
    def _order_by_appearance(words: list[str], text: str) -> list[str]:
        """Sort words by their position in the text. Existing headwords are
        lemma_1 values whose inflected form appears in the text, so match on a
        progressively shortened stem; unmatched words go to the end."""

        def position(word: str) -> int:
            stem = clean_lemma_1(word)
            while len(stem) >= 4:
                index = text.find(stem)
                if index != -1:
                    return index
                stem = stem[:-1]
            return len(text)

        return sorted(words, key=position)

    def _find_missing_eg_words(
        self, word_to_save: DpdHeadword
    ) -> list[tuple[str, dict[str, dict[str, str]]]]:
        """Scan examples and commentary for words missing meaning or example.
        Returns one (labelled field text, {word: prefill}) section per scanned field
        containing missing words, words ordered by appearance in that text."""

        def unbold(text: str) -> str:
            return text.replace("<b>", "").replace("</b>", "")

        field_prefills: list[tuple[str, str, dict[str, str]]] = [
            (
                "EG1:",
                word_to_save.example_1,
                {
                    "source_1": word_to_save.source_1,
                    "sutta_1": word_to_save.sutta_1,
                    "example_1": unbold(word_to_save.example_1),
                },
            ),
            (
                "EG2:",
                word_to_save.example_2,
                {
                    "source_1": word_to_save.source_2,
                    "sutta_1": word_to_save.sutta_2,
                    "example_1": unbold(word_to_save.example_2),
                },
            ),
            (
                "COMM:",
                word_to_save.commentary,
                {"example_1": unbold(word_to_save.commentary)},
            ),
        ]

        sections: list[tuple[str, dict[str, dict[str, str]]]] = []
        seen: set[str] = set()
        for label, text, prefill in field_prefills:
            if not text or text == "-":
                continue
            found = [
                word
                for word in find_missing_meanings(self._db.db_session, text, level=3)
                if word not in seen
                and word != word_to_save.lemma_1
                and not self._is_eg_queued(word)
            ]
            if not found:
                continue
            seen.update(found)
            section_words = {
                word: prefill for word in self._order_by_appearance(found, text)
            }
            sections.append((f"{label} {text}", section_words))
        return sections

    def _is_eg_queued(self, word: str) -> bool:
        """Match on clean form so a queued 'uppāṭita' also covers 'uppāṭita 1'
        and vice versa — the queue is one entry per word, homonyms get sorted
        out when the word is actually worked on."""

        clean = clean_lemma_1(word)
        return any(
            clean == clean_lemma_1(queued)
            for queued in self.pass2_eg_manager.eg_words_dict
        )

    @staticmethod
    def _parse_pasted_words(text: str) -> list[str]:
        """Split on commas only, so phrases containing spaces stay intact.
        Homonym numbers ('kata 1', 'kata 1.1') survive because they keep their
        internal space. Empty tokens are dropped."""

        return [w.strip() for w in text.split(",") if w.strip()]

    def _show_missing_words_dialog(self, word_to_save: DpdHeadword) -> None:
        """After a successful save, list missing words found in the saved word's
        examples and commentary. Ticked words go to the eg queue; unticked words
        are simply not added this time."""

        if not self._missing_words_switch.value:
            return

        sections = self._find_missing_eg_words(word_to_save)
        if not sections:
            return

        self._eg_prefills = {}
        self._eg_comment = f"eg: found in {word_to_save.lemma_1}"
        self._eg_checkboxes = {}
        self._eg_section_textboxes = []

        rows: list[ft.Control] = []
        for text, section_words in sections:
            rows.append(
                ft.Text(
                    text,
                    color=LABEL_COLOUR,
                    size=12,
                    selectable=True,
                )
            )
            for word, prefill in section_words.items():
                self._eg_prefills[word] = prefill
                checkbox = ft.Checkbox(value=False)
                self._eg_checkboxes[word] = checkbox
                rows.append(
                    ft.Row(
                        controls=[
                            checkbox,
                            ft.Text(word, selectable=True),
                        ]
                    )
                )
            add_field = ft.TextField(
                label="words to add (comma-separated)",
                dense=True,
                text_size=12,
                expand=True,
                on_submit=self._click_eg_add,
            )
            section_prefill = next(iter(section_words.values()))
            self._eg_section_textboxes.append((add_field, section_prefill))
            rows.append(ft.Row(controls=[add_field]))

        self._eg_alert = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[
                    ft.Text("Missing words", color=ft.Colors.BLUE_200, size=20),
                    ft.Text(f"found in {word_to_save.lemma_1}", color=LABEL_COLOUR),
                    ft.Column(
                        controls=rows,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                ],
                height=500,
                width=500,
            ),
            alignment=ft.alignment.center,
            actions=[
                ft.TextButton("Add ticked", on_click=self._click_eg_add),
                ft.TextButton("Close", on_click=self._click_eg_close),
            ],
            on_dismiss=self._restore_eg_kb,
        )

        def _eg_kb_handler(e: ft.KeyboardEvent) -> None:
            if e.key == "Enter":
                self._click_eg_add(e)
                return
            if self._eg_saved_kb is not None:
                self._eg_saved_kb(e)

        self._eg_saved_kb = self.page.on_keyboard_event
        self.page.on_keyboard_event = _eg_kb_handler
        self.page.open(self._eg_alert)
        self.page.update()

    def _click_eg_add(self, e: ft.ControlEvent) -> None:
        if not self._eg_alert or not self._eg_alert.open:
            return
        added = 0
        for word, checkbox in self._eg_checkboxes.items():
            if checkbox.value:
                self.pass2_eg_manager.add_word(
                    word, self._eg_prefills[word], self._eg_comment
                )
                added += 1
        for add_field, prefill in self._eg_section_textboxes:
            if not add_field.value:
                continue
            for word in self._parse_pasted_words(add_field.value):
                if not self._is_eg_queued(word):
                    self.pass2_eg_manager.add_word(word, prefill, self._eg_comment)
                    added += 1
        self._close_eg_alert()
        self.update_message(f"eg: {added} added")

    def _click_eg_close(self, e: ft.ControlEvent) -> None:
        self._close_eg_alert()

    def _restore_eg_kb(self, e: ft.ControlEvent | None = None) -> None:
        if self._eg_saved_kb is not None:
            self.page.on_keyboard_event = self._eg_saved_kb
            self._eg_saved_kb = None

    def _close_eg_alert(self) -> None:
        if self._eg_alert:
            self._eg_alert.open = False
        self._restore_eg_kb()
        self.page.update()

    def _click_eg_button(self, e: ft.ControlEvent) -> None:
        """Load the next eg queue word: edit mode if it exists in the db,
        otherwise a prefilled new word."""

        word, prefill = self.pass2_eg_manager.get_next()
        if word is None or prefill is None:
            self.update_message("No more eg words")
            self.page.update()
            return

        remaining = self.pass2_eg_manager.count()
        comment = prefill.get("comment", "")
        headword = self._db.get_headword_by_lemma(word)

        self.clear_all_fields()
        if headword:
            self.headword = headword
            self._enter_id_or_lemma_field.value = headword.lemma_1
            self.headword_original = copy.deepcopy(headword)
            self.dpd_fields.update_db_fields(headword)
            self.add_headword_to_examples_and_commentary()
            self.dpd_fields.update_add_fields(prefill)
        else:
            lemma_1_field = self.dpd_fields.get_field("lemma_1")
            if lemma_1_field:
                lemma_1_field.value = word
            self.dpd_fields.update_add_fields(prefill)

        self.update_message(
            f"[{remaining}] {word}: {comment}" if comment else f"[{remaining}] {word}"
        )
        self.update()

    def _click_pread_button(self, e: ft.ControlEvent) -> None:
        """Loads the next proofreader correction and populates the gui."""
        correction, remaining, field = (
            self.toolkit.proofreader_manager.get_next_correction()
        )

        if not correction or not field:
            self.update_message("No more proofreadings available")
            return

        try:
            headword_id = int(correction["id"])
            headword = self._db.get_headword_by_id(headword_id)

            if not headword:
                self.update_message(f"Headword ID {headword_id} not found in DB")
                return

            self.clear_all_fields()
            self.headword = headword
            self._enter_id_or_lemma_field.value = headword.lemma_1
            self.headword_original = copy.deepcopy(headword)
            self.dpd_fields.update_db_fields(headword)
            self.add_headword_to_examples_and_commentary()

            # Load correction into the add-field matching the proofread field
            corrected = correction.get(f"{field}_corrected", "")
            self.dpd_fields.update_add_fields({field: corrected})

            self.update_message(
                f"Loaded {field} proofreading for {headword.lemma_clean}. {remaining} proofreadings remaining."
            )

        except Exception as ex:  # noqa: BLE001
            self.update_message(f"Error loading proofreading: {ex!s}")

        self.page.update()
