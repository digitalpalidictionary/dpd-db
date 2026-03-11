import re
from typing import Any, Union

import flet as ft

from db.models import DpdHeadword
from gui2.database_manager import DatabaseManager
from gui2.dpd_fields_classes import (
    DpdDropdown,
    DpdText,
    DpdTextField,
    FieldConfig,
)
from gui2.dpd_fields_commentary import DpdCommentaryField
from gui2.dpd_fields_compound_construction import DpdCompoundConstructionField
from gui2.dpd_fields_examples import DpdExampleField
from gui2.dpd_fields_family_set import DpdFamilySetField
from gui2.dpd_fields_flags import Flags
from gui2.dpd_fields_functions import (
    clean_construction_line1,
    clean_lemma_1,
    clean_root,
    find_stem_pattern,
    make_construction,
    make_dpd_headword_from_dict,
    make_lemma_2,
)
from gui2.dpd_fields_meaning import DpdMeaningField
from gui2.dpd_fields_notes import DpdNotesField
from gui2.mixins import PopUpMixin
from gui2.toolkit import ToolKit
from tools.compound_type_manager import CompoundTypeManager
from tools.phonetic_change_manager import PhoneticChangeManager
from tools.fuzzy_tools import find_closest_matches
from tools.pali_alphabet import pali_alphabet
from tools.pali_sort_key import pali_list_sorter
from tools.pos import DECLENSIONS, NOUNS, PARTICIPLES, POS, VERBS
from tools.speech_marks import SpeechMarkManager
from tools.spelling import CustomSpellChecker

DpdFieldType = Union[
    DpdTextField,
    DpdDropdown,
    DpdMeaningField,
    DpdExampleField,
    DpdCommentaryField,
    DpdCompoundConstructionField,
    DpdFamilySetField,
    DpdNotesField,
    DpdText,
]


class DpdFields(PopUpMixin):
    def __init__(
        self,
        ui,
        db: DatabaseManager,
        toolkit,
        simple_examples: bool = False,
    ):
        super().__init__()  # Initialize PopUpMixin
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView | Pass1AddView = ui
        self.page = self.ui.page
        self.db: DatabaseManager = db
        self.spellchecker = CustomSpellChecker()
        self.toolkit: ToolKit = toolkit

        self.speech_marks_manager: SpeechMarkManager = self.toolkit.speech_marks_manager
        self.speech_marks_dict = self.speech_marks_manager.get_speech_marks()
        self.simple_examples = simple_examples  # Store the flag

        # Fetch compound types (ensure db is initialized first if needed)
        # Assuming db.initialize_db() has been called elsewhere before DpdFields is created
        compound_types_options = (
            self.db.all_compound_types if self.db.all_compound_types else []
        )

        # Fetch all dropdown options
        plus_case_options = self.db.all_plus_cases if self.db.all_plus_cases else []
        verb_options = self.db.all_verbs if self.db.all_verbs else []
        root_key_options = sorted(list(self.db.all_roots)) if self.db.all_roots else []

        family_set_options = self.db.all_family_sets if self.db.all_family_sets else []
        self.fields: dict[str, DpdFieldType] = {}
        self.field_containers = {}

        self.field_configs = [
            FieldConfig("id", on_submit=self.id_submit),
            FieldConfig(
                "lemma_1",
                on_change=self.lemma_1_change,
                on_submit=self.lemma_1_change,
                on_blur=self.lemma_1_change,
            ),
            FieldConfig(
                "lemma_2",
                on_blur=self.lemma_2_blur,
                on_submit=self.lemma_2_submit,
            ),
            FieldConfig(
                "pos",
                field_type="dropdown",
                options=POS,
                on_blur=self.pos_blur,
            ),
            FieldConfig(
                "grammar",
                on_blur=self.grammar_blur,
            ),
            FieldConfig("derived_from"),
            FieldConfig(
                "neg",
                field_type="dropdown",
                options=[" ", "neg", "neg x2"],
            ),
            FieldConfig(
                "verb",
                field_type="dropdown",
                options=[" "] + verb_options,
            ),
            FieldConfig(
                "trans",
                field_type="dropdown",
                options=[" ", "trans", "intrans", "ditrans"],
                on_blur=self.trans_blur,
            ),
            FieldConfig(
                "plus_case",
                field_type="dropdown",
                options=[" "] + plus_case_options,
            ),
            FieldConfig(
                "meaning_1",
                multiline=True,
                field_type="meaning",
                on_focus=self.meaning_1_focus,
                on_blur=self.meaning_1_blur,
            ),
            FieldConfig(
                "meaning_lit",
                on_blur=self._handle_generic_spell_check,
            ),
            FieldConfig(
                "meaning_2",
                multiline=True,
                field_type="meaning",
            ),
            FieldConfig(
                "root_key",
                field_type="dropdown",
                options=[" "] + root_key_options,
                on_focus=self.root_key_change,
                on_change=self.root_key_change,
                on_blur=self.root_key_change,
            ),
            FieldConfig(
                "root_sign",
                on_focus=self.root_sign_change,
                on_change=self.root_sign_change,
                on_submit=self.root_sign_submit,
                on_blur=self.root_sign_change,
            ),
            FieldConfig(
                "root_base",
                on_submit=self.root_base_submit,
            ),
            FieldConfig(
                "family_root",
                on_submit=self.family_root_submit,
                on_blur=self.family_root_blur,
            ),
            FieldConfig(
                "family_word",
                on_focus=self.family_word_change,
                on_change=self.family_word_change,
            ),
            FieldConfig(
                "family_compound",
                on_focus=self.family_compound_focus,
                on_change=self.family_compound_change,
                on_blur=self.family_compound_change,
            ),
            FieldConfig(
                "family_idioms",
                on_focus=self.family_idioms_focus,
            ),
            FieldConfig(
                "construction",
                multiline=True,
                on_focus=self.construction_focus,
                on_change=self.construction_change,
                on_blur=self.construction_blur,
            ),
            FieldConfig(
                "derivative",
                field_type="dropdown",
                options=[" ", "kita", "kicca", "taddhita"],
                on_change=self.derivative_change,
            ),
            FieldConfig(
                "suffix",
                on_change=self.suffix_on_change,
            ),
            FieldConfig(
                "phonetic",
                multiline=True,
                on_focus=self.phonetic_focus,
            ),
            FieldConfig(
                "compound_type",
                field_type="dropdown",
                options=[" "] + compound_types_options,
                on_blur=self.compound_type_blur,
            ),
            FieldConfig(
                "compound_construction",
                field_type="compound_construction",
            ),
            FieldConfig("non_root_in_comps"),
            FieldConfig(
                "non_ia",
                on_blur=self.non_ia_blur,
            ),
            FieldConfig(
                "sanskrit",
                on_blur=self.sanskrit_blur,
                on_focus=self.sanskrit_focus,
                on_submit=self.sanskrit_submit,
            ),
            FieldConfig(
                "source_1",
                on_focus=self.source_1_focus,
            ),
            FieldConfig("sutta_1"),
            FieldConfig("example_1", field_type="example"),
            FieldConfig("translation_1", multiline=True),
            FieldConfig("source_2"),
            FieldConfig("sutta_2"),
            FieldConfig("example_2", field_type="example"),
            FieldConfig("translation_2", multiline=True),
            FieldConfig(
                "antonym",
                on_change=self.clean_pali_field,
                on_blur=self.clean_pali_field,
            ),
            FieldConfig(
                "synonym",
                on_focus=self.synonym_focus,
                on_change=self.synonym_field_change,
                on_blur=self.clean_pali_field,
            ),
            FieldConfig(
                "variant",
                on_change=self.synonym_variant_check,
                on_blur=self.variant_blur,
            ),
            FieldConfig("var_phonetic", on_blur=self.clean_pali_field),
            FieldConfig("var_text", on_blur=self.clean_pali_field),
            FieldConfig(
                "commentary", field_type="commentary", on_focus=self.commentary_focus
            ),
            FieldConfig(
                "notes",
                field_type="notes",
                on_blur=self._handle_generic_spell_check,
            ),
            FieldConfig("cognate"),
            FieldConfig("link", multiline=True),
            FieldConfig(
                "family_set",
                field_type="family_set",
                options=family_set_options,
            ),
            FieldConfig(
                "origin",
                on_blur=self.origin_blur,
            ),
            FieldConfig(
                "stem",
                on_submit=self.stem_submit,
                on_blur=self.stem_blur,
            ),
            FieldConfig(
                "pattern",
                on_focus=self.pattern_change,
                on_change=self.pattern_change,
            ),
            FieldConfig(
                "comment",
                multiline=True,
                on_focus=self.comment_change,
                on_blur=self.comment_change,
                on_change=self.comment_change,
            ),
        ]

        # Initialize flags
        self.flags = Flags()

        self.create_fields()

    def create_fields(self):
        for config in self.field_configs:
            if config.field_type == "text":
                self.fields[config.name] = DpdTextField(
                    name=config.name,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                    multiline=config.multiline,
                )

            elif config.field_type == "dropdown":
                self.fields[config.name] = DpdDropdown(
                    name=config.name,
                    options=config.options,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_blur=config.on_blur,
                )

            elif config.field_type == "meaning":
                self.fields[config.name] = DpdMeaningField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    spellchecker=self.spellchecker,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                )

            elif config.field_type == "example":
                self.fields[config.name] = DpdExampleField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    toolkit=self.toolkit,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                    simple_mode=self.simple_examples,
                )

            elif config.field_type == "commentary":
                self.fields[config.name] = DpdCommentaryField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    toolkit=self.toolkit,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                )

            elif config.field_type == "compound_construction":
                self.fields[config.name] = DpdCompoundConstructionField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                )

            elif config.field_type == "notes":
                self.fields[config.name] = DpdNotesField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                )

            elif config.field_type == "family_set":
                self.fields[config.name] = DpdFamilySetField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    options=config.options,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                )

            else:
                raise ValueError(f"Unsupported field type: {config.field_type}")

            # Create corresponding _add field
            self.fields[f"{config.name}_add"] = DpdText()

    def add_to_ui(
        self,
        ui_component,
        visible_fields: list[str] | None = None,
        include_add_fields: bool = False,
    ):
        for config in self.field_configs:
            field_name = config.name

            # Create the row for this field (label + input(s))
            field_row = self._create_field_row(field_name, include_add_fields)

            if visible_fields is not None:
                field_row.visible = field_name in visible_fields
            else:
                field_row.visible = True  # Default to visible if no filter specified

            # Store the row and add it to the UI
            self.field_containers[field_name] = field_row
            ui_component.controls.append(field_row)

    def _create_field_row(self, field_name: str, include_add_fields: bool) -> ft.Row:
        """Creates the row containing the main field and optional add field/button."""

        label = ft.Text(
            field_name,
            color=ft.Colors.GREY_500,
            size=12,
            width=150,
            selectable=True,
        )
        main_field = self.fields[field_name]
        row_controls = [label, main_field]  # Add label first

        # Add edit button for compound_type field
        if field_name == "compound_type":
            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_size=16,
                tooltip="Edit compound type rules",
                on_click=self._click_edit_compound_types,
                padding=0,
                width=24,
                height=24,
            )
            row_controls.append(edit_btn)

        # Add edit button for phonetic field
        if field_name == "phonetic":
            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_size=16,
                tooltip="Edit phonetic change rules",
                on_click=self._click_edit_phonetic_changes,
                padding=0,
                width=24,
                height=24,
            )
            row_controls.append(edit_btn)

        if include_add_fields:
            add_field = self.fields.get(f"{field_name}_add")
            if add_field:
                # Create the button initially disabled
                transfer_btn = ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_size=20,
                    tooltip="Copy to db field",
                    # Use a lambda that captures the correct field names
                    on_click=lambda e,
                    mf=main_field,
                    af=add_field,
                    btn=None: self.transfer_add_value(
                        e, mf, af, None
                    ),  # Placeholder for btn
                    disabled=True,  # Start disabled
                    data=f"{field_name}_transfer_btn",  # Add data to identify the button later
                )
                row_controls.extend([transfer_btn, add_field])

        return ft.Row(
            row_controls,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def filter_fields(self, visible_fields: list[str] | None = None):
        """Shows only the specified fields, hides others. Shows all if None."""
        for field_name, field_row in self.field_containers.items():
            main_field = self.fields.get(field_name)
            has_value = bool(
                main_field and main_field.value
            )  # Check if the main field has a value

            if visible_fields is None or field_name in visible_fields:
                field_row.visible = True
            else:
                # Only hide if it's not in the visible list AND it has no value
                if not has_value:
                    field_row.visible = False
                else:  # Keep visible if it has a value, even if not in the filter list
                    field_row.visible = True

    def update_db_fields(self, headword: DpdHeadword) -> None:
        """Update the left hand side fields with headword data."""

        headword_dict = vars(headword)

        for key, value in headword_dict.items():
            if key in self.fields:
                self.fields[key].value = value
                self.fields[key].error_text = None

        self.page.update()
        self.flags.loaded_from_db = True

    def update_add_fields(self, data: dict[str, str]) -> None:
        """Update _add fields from provided data dictionary."""

        for name, value in data.items():
            add_field_name = f"{name}_add"
            add_field = self.fields.get(add_field_name)
            if add_field:
                add_field.value = value
                add_field.error_text = None

                # Find the corresponding button and update its state
                field_row = self.field_containers.get(name)
                if field_row:
                    for control in field_row.controls:
                        if (
                            isinstance(control, ft.IconButton)
                            and control.data == f"{name}_transfer_btn"
                        ):
                            control.disabled = not bool(
                                value
                            )  # Enable if value exists, disable otherwise
                            # Update the lambda to pass the button itself
                            control.on_click = lambda e, mf=self.fields[
                                name
                            ], af=add_field, btn=control: self.transfer_add_value(
                                e, mf, af, btn
                            )
                            break

        self.page.update()
        self.check_and_color_add_fields()

    def clear_fields(self, target: str = "all") -> None:
        """Clear field values.

        use `all`, `db`, or `add` to target specific fields
        """
        for name, control in self.fields.items():
            if (
                target == "all"
                or (target == "db" and not name.endswith("_add"))
                or (target == "add" and name.endswith("_add"))
            ):
                control.value = None
                control.error_text = None

                # If it's an _add field, find and disable its button
                if name.endswith("_add"):
                    base_name = name[:-4]
                    field_row = self.field_containers.get(base_name)
                    if field_row:
                        for ctrl in field_row.controls:
                            if (
                                isinstance(ctrl, ft.IconButton)
                                and ctrl.data == f"{base_name}_transfer_btn"
                            ):
                                ctrl.disabled = True
        self.flags.reset()
        self.page.update()

    def clear_messages(self) -> None:
        """Clear all error and helper messages from fields without changing values."""
        for control in self.fields.values():
            control.error_text = None
            control.helper_text = None
        self.page.update()

    def check_and_color_add_fields(self) -> None:
        """
        Checks if main fields and their corresponding _add fields have different values
        and changes the _add field's text color to red if they do.
        Also syncs the transfer button enabled state based on whether the _add field has content.
        """
        for config in self.field_configs:
            main_field_name = config.name
            add_field_name = f"{main_field_name}_add"

            main_field_control = self.fields.get(main_field_name)
            add_field_control = self.fields.get(add_field_name)

            if main_field_control and add_field_control:
                main_value = main_field_control.value
                add_value = add_field_control.value

                if main_value != add_value:
                    add_field_control.color = ft.Colors.RED
                else:
                    add_field_control.color = ft.Colors.GREY_500

                field_row = self.field_containers.get(main_field_name)
                if field_row:
                    for control in field_row.controls:
                        if (
                            isinstance(control, ft.IconButton)
                            and control.data == f"{main_field_name}_transfer_btn"
                        ):
                            control.disabled = not bool(add_value)
                            control.on_click = (
                                lambda e,
                                mf=main_field_control,
                                af=add_field_control,
                                btn=control: self.transfer_add_value(e, mf, af, btn)
                            )
                            break

        self.page.update()

    def transfer_add_value(
        self,
        e: ft.ControlEvent,
        field: ft.Control,
        add_field: ft.Control,
        button: ft.IconButton | None,
    ):
        """Transfers value from add_field to field and updates button state."""

        if add_field.value:
            field.value = add_field.value
            # Optionally clear the add_field after transfer
            # add_field.value = ""
            if button:  # Disable button after transfer if add_field is now empty (or always if desired)
                button.disabled = not bool(add_field.value)
            self.page.update()

    def get_field(self, name: str) -> Any:
        return self.fields.get(name, "")

    def get_event_field_and_value(self, e: ft.ControlEvent) -> tuple[ft.Control, Any]:
        field = e.control
        value = field.value
        return field, value

    def get_current_values(self) -> dict[str, str]:
        """Get all current field values as a dictionary"""

        values = {name: field.value or "" for name, field in self.fields.items()}
        if values["id"] == "":
            values["id"] = str(self.db.get_next_id())
        return values

    def get_current_headword(self):
        """Get the values and make a DpdHeadword instance from it."""
        values = self.get_current_values()
        return make_dpd_headword_from_dict(values)

    def _handle_generic_spell_check(self, e: ft.ControlEvent):
        """Common logic for spell checking generic text fields on blur."""
        field = e.control
        value = field.value
        if not value:
            field.error_text = None
            self.page.update()
            return

        misspelled = self.spellchecker.check_sentence(value)
        if misspelled:
            error_string = ". ".join(
                [
                    f"{word}: {', '.join(suggestions)}"
                    for word, suggestions in misspelled.items()
                ]
            )
            field.error_text = error_string
        else:
            field.error_text = None
        self.page.update()

    # --- AUTOMATION ---

    def id_submit(self, e: ft.ControlEvent) -> None:
        """Get the next id on submit."""
        field, value = self.get_event_field_and_value(e)
        field.value = self.db.get_next_id()
        field.focus()
        self.page.update()

    def lemma_1_change(self, e: ft.ControlEvent) -> None:
        """Test lemma_1 already in db."""

        field, value = self.get_event_field_and_value(e)

        if not self.flags.loaded_from_db:
            if value in self.db.all_lemma_1:
                field.error_text = f"{value} already in db"

        elif not value:
            field.error_text = "required field"
        else:
            field.error_text = None

        # Autofill search fields for new entries (not loaded from DB)
        if not self.flags.loaded_from_db and value:
            # Check if the UI has the method before calling it
            if hasattr(self.ui, "add_headword_to_examples_and_commentary"):
                self.ui.add_headword_to_examples_and_commentary()

        # Autofill meaning_lit for words ending in "sutta" or "vagga"
        if e.name == "blur" and value:
            lemma_clean = clean_lemma_1(value)
            meaning_lit_field = self.get_field("meaning_lit")
            if meaning_lit_field and not meaning_lit_field.value:
                if lemma_clean.endswith("sutta"):
                    meaning_lit_field.value = "discourse on "
                    meaning_lit_field.update()
                    self.page.update()
                elif lemma_clean.endswith("vagga"):
                    meaning_lit_field.value = "chapter on "
                    meaning_lit_field.update()
                    self.page.update()

        self.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def meaning_1_focus(self, e: ft.ControlEvent) -> None:
        """Copy meaning_2 to meaning_1 for suttas/vaggas if meaning_1 is empty and not loaded from DB."""
        field, value = self.get_event_field_and_value(e)
        if not value or not str(value).strip():
            lemma_1_field = self.get_field("lemma_1")
            if lemma_1_field and lemma_1_field.value:
                lemma_clean = clean_lemma_1(lemma_1_field.value)
                if lemma_clean.endswith(("sutta", "vagga")):
                    meaning_2_field = self.get_field("meaning_2")
                    if meaning_2_field and meaning_2_field.value:
                        field.value = meaning_2_field.value
                        field.update()
                        self.page.update()

    def meaning_1_blur(self, e: ft.ControlEvent) -> None:
        """Clear synonyms when meaning_1 loses focus so they regenerate from the new meaning."""
        syn_field = self.get_field("synonym")
        if self.flags.synonyms_done or (syn_field and syn_field.value):
            self.flags.synonyms_done = False
            syn_field.value = ""
            syn_field.update()
            self.ui.update_message("synonyms deleted - redo them")
            self.page.update()

    def lemma_2_blur(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        if not self.flags.lemma_2_done:
            new_value = self.get_field("lemma_1").value
            field.value = clean_lemma_1(new_value)
        self.page.update()

    def lemma_2_submit(self, e: ft.ControlEvent) -> None:
        self.update_lemma_2(e)

    def update_lemma_2(self, e: ft.ControlEvent) -> None:
        lemma_1 = self.get_field("lemma_1").value
        pos = self.get_field("pos").value
        grammar = self.get_field("grammar").value
        lemma_2_field = self.get_field("lemma_2")
        lemma_2 = make_lemma_2(lemma_1, pos, grammar)
        lemma_2_field.value = lemma_2
        lemma_2_field.update()
        self.page.update()

    def pos_blur(self, e: ft.ControlEvent) -> None:
        pos_field, pos = self.get_event_field_and_value(e)
        grammar_field = self.get_field("grammar")
        grammar = grammar_field.value

        # test for wrong values
        if pos not in self.db.all_pos:
            suggestions = find_closest_matches(
                pos, list(self.db.all_pos or []), limit=3
            )
            if suggestions:
                pos_field.error_text = ", ".join(suggestions)
            else:
                pos_field.error_text = f"Unknown pattern: {pos}"
            pos_field.focus()
        else:
            pos_field.error_text = None
        self.page.update()

        # then update lemma_2 based on lemma_1 and pos (only once)
        if not self.flags.lemma_2_done:
            lemma_1 = self.get_field("lemma_1").value
            lemma_2_field = self.get_field("lemma_2")
            lemma_2 = make_lemma_2(lemma_1, pos, grammar)
            lemma_2_field.value = lemma_2
            lemma_2_field.update()
            self.flags.lemma_2_done = True
            self.page.update()

        # then update grammar field
        if grammar == "":
            if pos in VERBS or pos in PARTICIPLES:
                grammar_field.value = f"{pos} of "
            elif pos in NOUNS:
                grammar_field.value = f"{pos}, "
            else:
                grammar_field.value = f"{pos}, "
            grammar_field.update()
            grammar_field.focus()
            self.page.update()

    def grammar_blur(self, e: ft.ControlEvent) -> None:
        """Autofill derived_from."""

        field, value = self.get_event_field_and_value(e)
        derived_from_field = self.get_field("derived_from")

        if not self.flags.derived_from_done:
            if " of " in value or " from " in value:
                # find what follows 'of' or 'from'
                derived_from = re.sub(".+( of | from )(.+)(,|$)", r"\2", value)
                # remove negatives
                derived_from = re.sub("^na ", "", derived_from)
                # remove comma and everything following
                derived_from = re.sub(",.+", "", derived_from)
                derived_from_field.value = derived_from
                derived_from_field.update()
                self.flags.derived_from_done = True
                self.page.update()
                # derived_from_field.focus() # Focus might be better handled elsewhere or removed

    def trans_blur(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        if value == "trans":
            plus_case_field = self.get_field("plus_case")
            plus_case_field.value = "+acc"
            plus_case_field.update()
            plus_case_field.focus()
            self.page.update()

    def compound_type_blur(self, e: ft.ControlEvent):
        compound_construction: DpdCompoundConstructionField = self.get_field(
            "compound_construction"
        )
        compound_construction.compound_construction_field.focus()
        self.page.update()

    def phonetic_focus(self, e: ft.ControlEvent) -> None:
        """Process phonetic changes when field gets focus."""
        field, value = self.get_event_field_and_value(e)

        # Get current headword data from fields
        current_headword = self.get_current_headword()

        # Initialize manager and process headword
        from tools.paths import ProjectPaths

        pth = ProjectPaths()
        manager = PhoneticChangeManager(pth.phonetic_changes_path)

        results, all_suggestions = manager.process_headword_all_matches(
            current_headword
        )

        if results:
            if all_suggestions:
                # If phonetic field is empty, put suggestions there; otherwise use phonetic_add field
                if not field.value:
                    field.value = all_suggestions
                    field.update()
                else:
                    phonetic_add_field = self.get_field("phonetic_add")
                    if phonetic_add_field:
                        phonetic_add_field.value = all_suggestions
                        phonetic_add_field.update()
                        self.check_and_color_add_fields()
                        print(
                            f"DEBUG: phonetic suggestions '{all_suggestions}' added to phonetic_add for '{current_headword.lemma_1}'"
                        )
                print(
                    f"DEBUG: phonetic auto-filled with '{all_suggestions}' for '{current_headword.lemma_1}'"
                )

            first_result = results[0]
            if first_result.status in ["auto_add", "auto_update"]:
                pass  # Already handled above
            self.page.update()

    def sanskrit_blur(self, e: ft.ControlEvent) -> None:
        """Get Sanskrit and clean field."""

        sanskrit_field = self.get_field("sanskrit")

        # Auto-replace common Sanskrit text errors
        if sanskrit_field.value:
            old_value = sanskrit_field.value
            new_value = self._clean_sanskrit_simple(old_value)
            if old_value != new_value:
                sanskrit_field.value = new_value
                sanskrit_field.update()
                self.page.update()

        if not self.flags.sanskrit_done and not sanskrit_field.value:
            self._search_and_fill_sanskrit()

    def sanskrit_focus(self, e: ft.ControlEvent) -> None:
        """Search for Sanskrit when field gets focus."""
        sanskrit_field = self.get_field("sanskrit")
        if not self.flags.sanskrit_done and not sanskrit_field.value:
            self._search_and_fill_sanskrit()

    def sanskrit_submit(self, e: ft.ControlEvent) -> None:
        """Re-initiate Sanskrit search on Enter."""
        self._search_and_fill_sanskrit()

    def _clean_sanskrit_simple(self, value: str) -> str:
        """Standardize Sanskrit sūkta, sūtra (bsk) variations."""
        if not value:
            return ""

        # Simple string replacements from the old logic + common mess patterns
        for mess in [
            "supta sūkta, sūtra (bsk) sūtra",
            "supta + sūkta, sūtra (bsk) + sūtra",
            "supta + sūkta, sūtra + sūtra",
            "sūkta, sūtra sūtra",
        ]:
            value = value.replace(mess, "sūkta, sūtra (bsk)")

        # If ends with "sūkta, sūtra", add " (bsk)"
        if value.endswith("sūkta, sūtra"):
            value = value + " (bsk)"

        return value

    def _search_and_fill_sanskrit(self) -> None:
        """Search database for Sanskrit and fill the field."""
        sanskrit_field = self.get_field("sanskrit")
        if not sanskrit_field:
            return

        construction = self.get_field("construction").value
        if not construction:
            return

        constr_splits = construction.split(" + ")

        sanskrit = ""
        already_added = []

        # Create thread-local session for thread safety
        from db.db_helpers import get_db_session
        from tools.paths import ProjectPaths

        pth = ProjectPaths()
        thread_session = get_db_session(pth.dpd_db_path)

        try:
            for constr_split in constr_splits:
                clean_split = constr_split.strip()
                if not clean_split:
                    continue

                results = (
                    thread_session.query(DpdHeadword)
                    .filter(DpdHeadword.lemma_1.like(f"%{clean_split}%"))
                    .all()
                )
                for i in results:
                    if i.lemma_clean == clean_split:
                        if i.sanskrit and i.sanskrit not in already_added:
                            if sanskrit:
                                sanskrit += " + "
                            sanskrit += i.sanskrit
                            already_added.append(i.sanskrit)
        finally:
            thread_session.close()

        # Standard cleanup for compiled DB results
        sanskrit = re.sub(r"\[.*?\]", "", sanskrit)  # remove square brackets
        sanskrit = re.sub(r" +", " ", sanskrit)  # remove double spaces
        sanskrit = sanskrit.replace("+ +", "+")  # remove double plus signs
        sanskrit = sanskrit.strip()

        # Apply specific standardization logic
        sanskrit = self._clean_sanskrit_simple(sanskrit)

        sanskrit_field.value = sanskrit
        sanskrit_field.update()
        self.flags.sanskrit_done = True
        self.page.update()

    def non_ia_blur(self, e: ft.ControlEvent) -> None:
        """Trigger Sanskrit search when non_ia field loses focus."""
        sanskrit_field = self.get_field("sanskrit")
        if not self.flags.sanskrit_done and sanskrit_field and not sanskrit_field.value:
            self._search_and_fill_sanskrit()

    def source_1_focus(self, e: ft.ControlEvent) -> None:
        """Autofill source_1 with '-' for words ending in 'sutta' or 'vagga'."""
        field, value = self.get_event_field_and_value(e)
        if value:
            return
        lemma_1_field = self.get_field("lemma_1")
        if not lemma_1_field or not lemma_1_field.value:
            return
        lemma_clean = clean_lemma_1(lemma_1_field.value)
        if lemma_clean.endswith(("sutta", "vagga")):
            field.value = "-"
            field.update()
            self.page.update()

    def commentary_focus(self, e: ft.ControlEvent) -> None:
        """Autofill commentary with '-' for words ending in 'sutta' or 'vagga'."""
        field, value = self.get_event_field_and_value(e)
        if value:
            return
        lemma_1_field = self.get_field("lemma_1")
        if not lemma_1_field or not lemma_1_field.value:
            return
        lemma_clean = clean_lemma_1(lemma_1_field.value)
        if lemma_clean.endswith(("sutta", "vagga")):
            field.value = "-"
            field.update()
            self.page.update()

    def root_key_change(self, e: ft.ControlEvent) -> None:
        """Test root_key"""

        field, value = self.get_event_field_and_value(e)
        # test if root key exists
        if value:
            if value in self.db.all_roots:
                field.error_text = None
                field.helper_text = self.db.get_root_string(value)
            else:
                field.helper_text = None
                field.error_text = None
        self.page.update()

    def root_sign_submit(self, e: ft.ControlEvent) -> None:
        """Load root_sign from db."""
        field, value = self.get_event_field_and_value(e)

        # show all possible signs
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_sign(root_key)
            self.page.update()
            field.focus()

    def root_sign_change(self, e: ft.ControlEvent) -> None:
        """Test root_sign."""

        field, value = self.get_event_field_and_value(e)
        root_key = self.get_field("root_key").value
        if value and not root_key:
            field.error_text = "no root_key"
        elif not value and root_key:
            field.error_text = "no root_sign"
        else:
            field.error_text = None
        self.page.update()

    def root_base_submit(self, e: ft.ControlEvent) -> None:
        """Get root_base from db."""

        field, value = self.get_event_field_and_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_base(root_key)
            self.page.update()
            field.focus()

    def family_root_submit(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_family_root(root_key)
            self.page.update()
            field.focus()

    def family_root_blur(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        # test root in root family
        if value:
            root_key_clean = clean_root(self.get_field("root_key").value)
            if root_key_clean not in value:
                field.error_text = "root_key and family_root dont's match"
                field.focus()

            # test root_family exists
            elif value not in self.db.all_root_families:
                field.error_text = f"{value} unknown root family"
            else:
                field.error_text = None
                self.page.update()

    def derivative_change(self, e: ft.ControlEvent) -> None:
        """When derivative changes, try to generate suffix."""

        suffix_field = self.get_field("suffix")

        # Only generate if the suffix field is currently empty
        if not suffix_field.value:
            pos = self.get_field("pos").value
            grammar = self.get_field("grammar").value
            construction = self.get_field("construction").value

            if pos in DECLENSIONS and "comp" not in grammar and construction:
                suffix = re.sub(r"\n.+", "", construction)
                suffix = re.sub(r".+ \+ ", "", suffix)
                suffix_field.value = suffix
                suffix_field.update()
                suffix_field.focus()
                self.page.update()

    def suffix_on_change(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        if value and field.error_text:
            field.error_text = None
            self.page.update()

    def family_word_change(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        root_key = self.get_field("root_key").value

        if value:
            # Test for root and family_word
            if root_key:
                field.error_text = "Cannot have both root_key and family_word"
                field.focus()

            # Test for space
            elif " " in value:
                field.error_text = "family_word contains space"
                field.focus()

            # Test if known value
            elif value not in self.db.all_word_families:
                suggestions = find_closest_matches(
                    value, list(self.db.all_word_families or []), limit=3
                )
                if suggestions:
                    field.error_text = ", ".join(suggestions)
                    field.focus()
                else:
                    field.error_text = f"Unknown: {value}"
                    field.focus()

            # All good
            else:
                field.error_text = None
        else:
            field.error_text = None
        self.page.update()

    def family_compound_focus(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        if not self.flags.family_compound_done and not value:
            lemma_1 = self.get_field("lemma_1").value
            lemma_clean = clean_lemma_1(lemma_1)
            pos = self.get_field("pos").value

            if not lemma_clean.endswith(("sutta", "vagga")) and pos not in (
                "sandhi",
                "idiom",
            ):
                field.value = lemma_clean
                field.update()
                field.focus()
                self.page.update()
            self.flags.family_compound_done = True

    def family_compound_change(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        # test family compounds exist
        if value:
            error_list = [
                c for c in value.split() if c not in self.db.all_compound_families
            ]
            if error_list:
                field.error_text = f"{', '.join(error_list)} "
            else:
                field.error_text = None
        else:
            field.error_text = None
        self.page.update()

    def family_idioms_focus(self, e: ft.ControlEvent) -> None:
        """
        Copy family_compound
          - if family_idioms is empty
          - and family_compound has no space.
        """

        field, value = self.get_event_field_and_value(e)
        family_compound_field = self.get_field("family_compound")
        family_compound_value = family_compound_field.value

        if not value and family_compound_value and " " not in family_compound_value:
            field.value = family_compound_value
            self.page.update()

        # Always focus the field when it gains focus
        field.focus()

    def clean_pali_field(self, e: ft.ControlEvent) -> None:
        """Clean field value to only allow Pali chars, comma and space."""
        field = e.control
        if not field.value:
            return

        # Build allowed characters: Pali alphabet + comma + space
        allowed = set(pali_alphabet + [",", " "])
        cleaned = "".join(char for char in field.value if char in allowed)

        # Only update if changed
        if cleaned != field.value:
            field.value = cleaned
            field.update()

    def synonym_field_change(self, e: ft.ControlEvent) -> None:
        """Clean text and check for duplicates in variant field."""
        # First clean the field
        self.clean_pali_field(e)
        # Then check for duplicates
        self.synonym_variant_check(e)

    def synonym_focus(self, e: ft.ControlEvent) -> None:
        """Auto-generate synonyms if the field is empty."""

        field, value = self.get_event_field_and_value(e)

        if not self.flags.synonyms_done:
            pos = self.get_field("pos").value
            meaning_1 = self.get_field("meaning_1").value
            lemma_1 = self.get_field("lemma_1").value

            if pos and meaning_1 and lemma_1:
                synonyms_string = self.db.get_synonyms(pos, meaning_1, lemma_1)
                if synonyms_string:
                    var_field = self.get_field("variant")
                    var_value = var_field.value or ""
                    var_set = set(
                        word.strip() for word in var_value.split(",") if word.strip()
                    )
                    syn_set = set(
                        word.strip()
                        for word in synonyms_string.split(",")
                        if word.strip()
                    )
                    syn_set = syn_set - var_set
                    synonyms_string = ", ".join(pali_list_sorter(list(syn_set)))
                    field.value = synonyms_string
                    self.ui.update_message("Synonyms auto-generated")
                    self.flags.synonyms_done = True
                else:
                    self.ui.update_message("No synonyms found")
            else:
                self.ui.update_message(
                    "POS, Meaning 1, and Lemma 1 needed for synonyms"
                )
            self.page.update()

    def synonym_variant_check(self, e: ft.ControlEvent) -> None:
        """Ensure that the same word does not exist in both synonym and variant fields."""

        # Determine which field triggered the event
        triggering_field_name = e.control.name

        syn_field = self.get_field("synonym")
        var_field = self.get_field("variant")

        syn_value = syn_field.value or ""
        var_value = var_field.value or ""

        # Split into sets of cleaned words
        syn_set = set(word.strip() for word in syn_value.split(",") if word.strip())
        var_set = set(word.strip() for word in var_value.split(",") if word.strip())

        intersection = syn_set.intersection(var_set)

        if intersection:
            if triggering_field_name == "synonym":
                for word in intersection:
                    var_set.discard(word)
                var_field.value = ", ".join(pali_list_sorter(list(var_set)))
                var_field.update()
            elif triggering_field_name == "variant":
                for word in intersection:
                    syn_set.discard(word)
                syn_field.value = ", ".join(pali_list_sorter(list(syn_set)))
                syn_field.update()

            self.page.update()

    def variant_blur(self, e: ft.ControlEvent) -> None:
        self.clean_pali_field(e)
        field, value = self.get_event_field_and_value(e)
        var_text_field = self.get_field("var_text")
        var_text_field.value = value
        var_text_field.update()
        self.page.update()

    def construction_focus(self, e: ft.ControlEvent) -> None:
        """Make a construction from the parts."""

        field, value = self.get_event_field_and_value(e)

        if not value and not self.flags.construction_done:
            lemma_1 = self.get_field("lemma_1").value
            lemma_clean = clean_lemma_1(lemma_1)
            grammar = self.get_field("grammar").value
            root_key = self.get_field("root_key").value
            root_base = self.get_field("root_base").value
            family_root = self.get_field("family_root").value
            neg = self.get_field("neg").value
            construction = make_construction(
                lemma_clean, grammar, neg, root_key, root_base, family_root
            )
            field.value = construction
            field.update()
            self.page.update()
            field.focus()
            self.flags.construction_done = True

        elif value:
            # test words are in all_lemma_clean
            construction_line1 = clean_construction_line1(value)
            error_list = []
            # Ensure db.all_lemma_clean is loaded and not None before iterating
            if self.db.all_lemma_clean:
                cleaned_line1_strip = construction_line1.strip()
                if cleaned_line1_strip:  # Check if not empty after stripping
                    # Split, filter out empty strings resulting from multiple spaces around '+'
                    parts = [
                        part.strip()
                        for part in cleaned_line1_strip.split("+")
                        if part.strip()
                    ]
                    error_list = [
                        word for word in parts if word not in self.db.all_lemma_clean
                    ]

            if error_list:
                field.error_text = f"Unknown: {', '.join(error_list)} "
            else:
                field.error_text = None
            self.page.update()

        self.page.update()

    def origin_blur(self, e: ft.ControlEvent) -> None:
        """Set origin to 'pass2' if empty on blur."""

        field, value = self.get_event_field_and_value(e)
        if not value:
            field.value = "pass2"
            field.update()
            self.page.update()

    def construction_change(self, e: ft.ControlEvent) -> None:
        """Handle change events for the construction field to detect Enter press when field has content."""

        field, current_value = self.get_event_field_and_value(e)

        # --- Detect if Enter key was the primary change AND field had content before ---
        # Check if current ends with \n and the part *before* the \n is not empty/whitespace
        if current_value.endswith("\n") and current_value[:-1].strip():
            lemma_1 = self.get_field("lemma_1").value
            if lemma_1:  # Only append if lemma_1 exists
                lemma_clean = clean_lemma_1(lemma_1)
                field.value = current_value + lemma_clean
                self.flags.construction_done = (
                    False  # Mark as not done if user adds manually
                )
                self.page.update()
                return  # Exit early, Enter handled

    def construction_blur(self, e: ft.ControlEvent) -> None:
        """Detect compound type when construction field loses focus."""
        field, value = self.get_event_field_and_value(e)

        if not value:
            return

        # Check if word has a root_key - if so, it's not a compound
        root_key_field = self.get_field("root_key")
        root_key = root_key_field.value if root_key_field else ""
        if root_key and root_key.strip():
            return

        # Get required field values
        meaning_1_field = self.get_field("meaning_1")
        meaning_1 = meaning_1_field.value if meaning_1_field else ""

        pos_field = self.get_field("pos")
        pos = pos_field.value if pos_field else ""

        grammar_field = self.get_field("grammar")
        grammar = grammar_field.value if grammar_field else ""

        compound_type_field = self.get_field("compound_type")
        current_compound_type = compound_type_field.value if compound_type_field else ""
        current_compound_type_stripped = (
            current_compound_type.strip() if current_compound_type else ""
        )

        lemma_1_field = self.get_field("lemma_1")
        lemma = lemma_1_field.value if lemma_1_field else ""

        # Initialize manager and detect compound type
        from tools.paths import ProjectPaths

        pth = ProjectPaths()
        manager = CompoundTypeManager(pth.compound_type_path)

        detected_type = manager.detect_compound_type(
            construction=value,
            pos=pos,
            grammar=grammar,
            lemma=lemma,
            meaning_1=meaning_1,
            compound_type=current_compound_type_stripped,
        )

        if detected_type and compound_type_field:
            print(f"DEBUG: compound_type set to '{detected_type}' for '{lemma}'")

            # Only populate compound_type_add field (shows in red as suggestion)
            compound_type_add_field = self.get_field("compound_type_add")
            if compound_type_add_field:
                compound_type_add_field.value = detected_type
                compound_type_add_field.update()
                self.check_and_color_add_fields()

            self.page.update()

    def _click_edit_compound_types(self, e: ft.ControlEvent) -> None:
        """Open the compound type TSV file for editing."""
        from tools.paths import ProjectPaths

        pth = ProjectPaths()

        if not pth.compound_type_path.exists():
            self.show_message(
                f"Error: Compound type file not found at {pth.compound_type_path}"
            )
            return

        try:
            manager = CompoundTypeManager(pth.compound_type_path)
            manager.open_tsv_for_editing()
            self.show_message(f"Opening compound types TSV: {pth.compound_type_path}")
        except FileNotFoundError as fnf_error:
            self.show_message(f"Error: {fnf_error}")
        except RuntimeError as rte_error:
            self.show_message(f"Error: {rte_error}")
        except Exception as error:
            self.show_message(f"Error opening compound types file: {error}")

    def _click_edit_phonetic_changes(self, e: ft.ControlEvent) -> None:
        """Open the phonetic changes TSV file for editing."""
        from tools.paths import ProjectPaths

        pth = ProjectPaths()

        if not pth.phonetic_changes_path.exists():
            self.show_message(
                f"Error: Phonetic changes file not found at {pth.phonetic_changes_path}"
            )
            return

        try:
            manager = PhoneticChangeManager(pth.phonetic_changes_path)
            manager.open_tsv_for_editing()
            self.show_message(
                f"Opening phonetic changes TSV: {pth.phonetic_changes_path}"
            )
        except FileNotFoundError as fnf_error:
            self.show_message(f"Error: {fnf_error}")
        except RuntimeError as rte_error:
            self.show_message(f"Error: {rte_error}")
        except Exception as error:
            self.show_message(f"Error opening phonetic changes file: {error}")

    def show_message(self, message: str) -> None:
        """Display a message to the user."""
        # Try to use the UI's update_message method if available
        if hasattr(self.ui, "update_message"):
            self.ui.update_message(message)
        else:
            # Fallback: print to console
            print(message)

    def stem_submit(self, e: ft.ControlEvent) -> None:
        self.update_stem(e)

    def stem_blur(self, e: ft.ControlEvent) -> None:
        if not self.flags.stem_pattern_done:
            self.update_stem(e)
            self.flags.stem_pattern_done = True

    def update_stem(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        pos = self.get_field("pos").value
        grammar = self.get_field("grammar").value
        lemma_1 = self.get_field("lemma_1").value
        stem, pattern = find_stem_pattern(pos, grammar, lemma_1)
        field.value = stem
        field.update()
        pattern_field = self.get_field("pattern")
        pattern_field.value = pattern
        pattern_field.update()

        self.page.update()
        if e.name == "submit":
            field.focus()

    def pattern_change(self, e: ft.ControlEvent) -> None:
        """Validate pattern against known patterns on blur."""

        field, value = self.get_event_field_and_value(e)

        if value:
            if self.db.all_patterns is None:
                self.db.get_all_patterns()

            if value not in (self.db.all_patterns or set()):
                suggestions = find_closest_matches(
                    value, list(self.db.all_patterns or []), limit=3
                )
                if suggestions:
                    field.error_text = ", ".join(suggestions)
                else:
                    field.error_text = f"Unknown pattern: {value}"
                field.focus()
            else:
                field.error_text = None
        else:
            field.error_text = None
        self.page.update()

    def comment_change(self, e: ft.ControlEvent) -> None:
        """Make a noise if there's no comment."""

        if self.toolkit.username_manager.is_not_primary():
            field, value = self.get_event_field_and_value(e)
            if not value:
                field.error_text = "Add a comment"
                self.page.update()
            else:
                field.error_text = None
                self.page.update()
