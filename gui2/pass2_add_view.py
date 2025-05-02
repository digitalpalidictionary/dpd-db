import copy
import flet as ft

# Import the backup function and ProjectPaths
from scripts.backup.backup_dpd_headwords_and_roots import backup_dpd_headwords_and_roots
from tools.paths import ProjectPaths  # Import ProjectPaths
from db.models import DpdHeadword
from gui2.daily_log import DailyLog
from gui2.database_manager import DatabaseManager
from gui2.dpd_fields_commentary import DpdCommentaryField
from gui2.dpd_fields_examples import DpdExampleField
from gui2.dpd_fields_lists import (
    ROOT_FIELDS,
    COMPOUND_FIELDS,
    WORD_FIELDS,
    PASS1_FIELDS,
)  # Import the lists
from gui2.history import HistoryManager  # Import HistoryManager
from gui2.mixins import PopUpMixin
from gui2.dpd_fields import DpdFields
from gui2.pass2_file_manager import Pass2AutoFileManager

from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from tools.fast_api_utils import request_dpd_server
from tools.sandhi_contraction import SandhiContractionDict, SandhiContractionFinder

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass2AddView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        db: DatabaseManager,
        daily_log: DailyLog,
        test_manger,
        sandhi_manager: SandhiContractionFinder,
        history_manager: HistoryManager,  # Add history_manager parameter
    ) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )
        from gui2.test_manager import GuiTestManager

        self.page: ft.Page = page
        self._db = db
        self._daily_log = daily_log
        self.test_manager: GuiTestManager = test_manger
        self.sandhi_manager: SandhiContractionFinder = sandhi_manager
        self.sandhi_dict: SandhiContractionDict = (
            self.sandhi_manager.get_contractions_simple()
        )
        self.history_manager: HistoryManager = history_manager  # Store history_manager

        self.dpd_fields: DpdFields

        self._pass2_auto_file_manager = Pass2AutoFileManager()
        self.headword: DpdHeadword | None = None
        self.headword_original: DpdHeadword | None = None

        self._message_field = ft.Text("", expand=True, selectable=True)
        self._next_pass2_auto_button = ft.ElevatedButton(
            "NextPass2Auto",
            width=BUTTON_WIDTH,
            on_click=self._click_load_next_pass2_entry,
        )
        self._enter_id_or_lemma_field = ft.TextField(
            "",
            width=400,
            expand=True,
            expand_loose=True,
            on_submit=self._click_edit_headword,
        )
        self._clone_headword_button = ft.ElevatedButton(
            "Clone", on_click=self._click_clone_headword
        )
        self._edit_headword_button = ft.ElevatedButton(
            "Edit", on_click=self._click_edit_headword
        )
        self._clear_all_button = ft.ElevatedButton(
            "Clear All", on_click=self._click_clear_all
        )
        self.update_sandhi_button = ft.ElevatedButton(
            "Update Sandhi", on_click=self._click_update_sandhi
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="History",  # Changed hint text
            options=[],  # Initially empty, populated later
            width=BUTTON_WIDTH,
            border_radius=20,
            # text_style=ft.TextStyle(color=ft.Colors.BLUE_200), # Optional styling
            text_size=14,
            on_change=self._handle_history_selection,  # Add the on_change handler
        )

        # --- Field Filter Radio Buttons ---
        self._filter_radios = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="all", label="All"),
                    ft.Radio(value="root", label="Root"),
                    ft.Radio(value="compound", label="Compound"),
                    ft.Radio(value="word", label="Word"),
                    ft.Radio(value="pass1", label="Pass1"),
                ]
            ),
            value="all",  # Default selection
            on_change=self._handle_filter_change,
        )

        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            # self._clone_headword_button,
                            self._enter_id_or_lemma_field,
                            self._edit_headword_button,
                            self._next_pass2_auto_button,
                            self._clear_all_button,
                            self.update_sandhi_button,
                            self._history_dropdown,
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
                            ft.ElevatedButton(
                                "Add to DB",
                                on_click=self._click_add_to_db,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Delete",
                                on_click=self._click_delete_from_db,
                                width=BUTTON_WIDTH,
                                on_hover=self._on_delete_hover,
                            ),
                            ft.ElevatedButton(
                                "Backup DB",
                                on_click=self._click_backup_db,
                                width=BUTTON_WIDTH,
                            ),  # Add backup button here
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

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()

    def add_headword_to_examples_and_commentary(self):
        # add headword to example_1 example_2 and commentary
        if self.headword:
            example_1_field: DpdExampleField = self.dpd_fields.get_field("example_1")
            example_1_field.word_to_find_field.value = self.headword.lemma_1[:-1]
            example_1_field.bold_field.value = self.headword.lemma_clean[:-1]

            example_2_field: DpdExampleField = self.dpd_fields.get_field("example_2")
            example_2_field.word_to_find_field.value = self.headword.lemma_clean[:-1]
            example_2_field.bold_field.value = self.headword.lemma_clean[:-1]

            commentary_field: DpdCommentaryField = self.dpd_fields.get_field(
                "commentary"
            )
            commentary_field.search_field_1.value = self.headword.lemma_clean[:-1]

    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        id_or_lemma = self._enter_id_or_lemma_field.value

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
                        in self._pass2_auto_file_manager.responses
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
        pass

    def _click_load_next_pass2_entry(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2 entry into the view."""
        headword_id, pass2_auto_data = (
            self._pass2_auto_file_manager.get_next_headword_data()
        )

        if headword_id is not None:
            self.clear_all_fields()
            headword = self._db.get_headword_by_id(int(headword_id))

            if headword is not None:
                self.headword = headword
                self.headword_original = copy.deepcopy(headword)

                self.dpd_fields.update_db_fields(self.headword)
                self.dpd_fields.update_add_fields(pass2_auto_data)
                self.add_headword_to_examples_and_commentary()
            else:
                self.update_message(f"{headword_id}: headword not found")

        else:
            self._message_field.value = "Current Pass2: None"
            self.clear_all_fields()

        self.update()

    def _click_clear_all(self, e: ft.ControlEvent):
        self.clear_all_fields()

    def _click_update_sandhi(self, e: ft.ControlEvent):
        self.update_message("updating sandhi... please wait...")
        self.sandhi_dict = self.sandhi_manager.update_contractions_simple()
        self.update_message("sandhi updated")

    def _handle_filter_change(self, e: ft.ControlEvent):
        """Handles changes in the field filter RadioGroup."""
        filter_type = e.control.value
        visible_fields = None  # Default to all

        if filter_type == "root":
            visible_fields = ROOT_FIELDS
        elif filter_type == "compound":
            visible_fields = COMPOUND_FIELDS
        elif filter_type == "word":
            visible_fields = WORD_FIELDS
        elif filter_type == "pass1":
            visible_fields = PASS1_FIELDS

        self.dpd_fields.filter_fields(visible_fields)
        self.page.update()

    def _update_history_dropdown(self):
        """Populates the history dropdown with the latest history."""
        history_items = self.history_manager.get_history()
        self._history_dropdown.options.clear()
        for item in history_items:
            self._history_dropdown.options.append(
                ft.dropdown.Option(
                    key=str(item.get("id")),  # Key must be string for Dropdown
                    text=f"{item.get('id')}: {item.get('lemma_1', 'N/A')}",
                )
            )
        self.page.update()  # Ensure dropdown updates visually

    def _handle_history_selection(self, e: ft.ControlEvent):
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
        self.dpd_fields = DpdFields(self, self._db, self.sandhi_dict)  # New instance
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
        self._filter_radios.value = "all"  # Reset filter to 'all'
        self.headword_original = None  # Resetting the original data reference

        self.update_message("")  # Clear message field
        self.page.update()

    def _click_run_tests(self, e: ft.ControlEvent):
        """Run tests on current field values"""

        self.dpd_fields.clear_messages()
        headword = self.dpd_fields.get_current_headword()
        self.test_manager.run_all_tests(self, headword)

    def _click_add_to_db(self, e: ft.ControlEvent):
        id_field = self.dpd_fields.fields.get("id")
        id_value: int | None = int(id_field.value) if id_field else None

        if (
            hasattr(self, "headword")
            and self.headword
            and hasattr(self, "headword_original")
            and self.headword_original
            and id_value == self.headword_original.id
        ):
            # Update existing word
            for field_name, field in self.dpd_fields.fields.items():
                if hasattr(self.headword, field_name):
                    setattr(self.headword, field_name, field.value)
            try:
                self._db.db_session.commit()
                committed, message = True, ""
            except Exception as ex:
                self._db.db_session.rollback()
                committed, message = False, str(ex)
            log_key = "pass2_update"  # It's an update if this block runs
        else:
            # Create new word (whether first time or ID changed)
            # Get data *before* making the object
            field_data = {
                # Use field.value directly, assuming it's the correct type or None
                field_name: field.value
                for field_name, field in self.dpd_fields.fields.items()
                if hasattr(DpdHeadword, field_name)
            }
            # Ensure ID is correctly handled if it was changed manually
            if id_field and id_field.value:
                try:
                    field_data["id"] = int(id_field.value)
                except ValueError:
                    field_data["id"] = None  # Or handle error appropriately
            new_word = make_dpd_headword_from_dict(field_data)
            committed, message = self._db.add_word_to_db(new_word)
            log_key = "pass2_add"  # It's an add if this block runs

        if committed:
            request_dpd_server(str(id_value))
            # Determine which item was added/updated for history
            item_id = (
                self.headword.id
                if hasattr(self, "headword") and self.headword
                else new_word.id
            )
            item_lemma = (
                self.headword.lemma_1
                if hasattr(self, "headword") and self.headword
                else new_word.lemma_1
            )

            # Add to history after successful commit
            was_new_to_history = self.history_manager.add_item(item_id, item_lemma)

            if was_new_to_history:  # Only increment log if it was new to history
                self._daily_log.increment(log_key)  # Use the determined log key

            self._update_history_dropdown()  # Refresh dropdown
            self.page.update()  # Ensure dropdown update is visible
            self.clear_all_fields()  # Clear fields AFTER history update
        else:
            # Update message but don't clear fields on failure
            self.update_message(f"Commit failed: {message}")

    def _click_delete_from_db(self, e: ft.ControlEvent):
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

    def _click_delete_ok(self, e: ft.ControlEvent):
        self.delete_alert.open = False
        self.page.update()

        if self.headword:
            deleted, message = self._db.delete_word_in_db(self.headword)
            if deleted:
                self.update_message(f"{self.headword.id} deleted from database")
            else:
                self.update_message(f"Delete failed: {message}")
            self.clear_all_fields()
        else:
            self.update_message("No headword to delete")

    def _click_delete_cancel(self, e: ft.ControlEvent):
        self.delete_alert.open = False
        self.page.update()

    def _click_backup_db(self, e: ft.ControlEvent):
        """Runs the backup script for DpdHeadword and DpdRoot tables."""
        # Instantiate ProjectPaths here
        pth = ProjectPaths()

        self.update_message("Running database backup...")
        try:
            # Call the function directly
            backup_dpd_headwords_and_roots(pth)
            self.update_message("Database backup completed successfully.")
        except Exception as ex:
            self.update_message(f"An unexpected error occurred during backup: {ex}")
            print(f"Backup error: {ex}")  # Log the error to console for debugging
