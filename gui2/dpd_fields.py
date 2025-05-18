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
from gui2.dpd_fields_family_set import DpdFamilySetField
from gui2.dpd_fields_meaning import DpdMeaningField
from gui2.dpd_fields_notes import DpdNotesField
from gui2.dpd_fields_flags import Flags
from gui2.dpd_fields_examples import DpdExampleField
from gui2.dpd_fields_functions import (
    clean_construction_line1,
    clean_lemma_1,
    clean_root,
    find_stem_pattern,
    make_construction,
    make_dpd_headword_from_dict,
    make_lemma_2,
)
from gui2.mixins import PopUpMixin
from gui2.toolkit import ToolKit
from tools.pos import DECLENSIONS, NOUNS, PARTICIPLES, POS, VERBS  # Import DECLENSIONS
from tools.sandhi_contraction import SandhiContractionDict
from tools.spelling import CustomSpellChecker
from tools.fuzzy_tools import find_closest_matches

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
        simple_examples: bool = False,  # Add simple_examples flag
    ):
        super().__init__()  # Initialize PopUpMixin
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView | Pass1AddView = ui
        self.page = self.ui.page
        self.db: DatabaseManager = db
        self.spellchecker = CustomSpellChecker()
        self.toolkit: ToolKit = toolkit

        self.sandhi_dict: SandhiContractionDict = self.toolkit.sandhi_dict
        self.hyphenation_dict: dict[str, str] = self.toolkit.hyphenation_dict
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
            ),
            FieldConfig(
                "pos",
                field_type="dropdown",
                options=POS,
                on_blur=self.pos_blur,
            ),
            FieldConfig(
                "grammar",
                on_submit=self.grammar_submit,
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
            ),
            FieldConfig(
                "meaning_lit",
                on_blur=self._handle_generic_spell_check,
            ),
            FieldConfig(
                "meaning_2",
                multiline=True,
                on_blur=self._handle_generic_spell_check,
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
            FieldConfig("phonetic", multiline=True),
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
            ),
            FieldConfig(
                "sanskrit",
                on_blur=self.sanskrit_blur,
            ),
            FieldConfig("source_1"),
            FieldConfig("sutta_1"),
            FieldConfig("example_1", field_type="example"),
            FieldConfig("translation_1", multiline=True),
            FieldConfig("source_2"),
            FieldConfig("sutta_2"),
            FieldConfig("example_2", field_type="example"),
            FieldConfig("translation_2", multiline=True),
            FieldConfig("antonym"),
            FieldConfig(
                "synonym",
                on_focus=self.synonym_focus,
            ),
            FieldConfig("variant"),
            FieldConfig("var_phonetic"),
            FieldConfig("var_text"),
            FieldConfig("commentary", field_type="commentary"),
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
            FieldConfig("comment", multiline=True),
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

            elif config.field_type == "meaning":  # Add condition for meaning
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
        """
        for config in self.field_configs:
            main_field_name = config.name
            add_field_name = f"{main_field_name}_add"

            main_field_control = self.fields.get(main_field_name)
            add_field_control = self.fields.get(add_field_name)

            if main_field_control and add_field_control:
                main_value = main_field_control.value
                add_value = add_field_control.value

                if main_value and add_value and main_value != add_value:
                    add_field_control.color = ft.Colors.RED
                else:
                    add_field_control.color = ft.Colors.GREY_500

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

    def get_current_headword(self) -> DpdHeadword:
        """Get all current field values as a dictionary
        and make a DpdHeadword instance from it."""

        values = {name: field.value or "" for name, field in self.fields.items()}
        if values["id"] == "":
            values["id"] = str(self.db.get_next_id())
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
            lemma_clean = clean_lemma_1(value)
            commentary_field: DpdCommentaryField | None = self.get_field("commentary")
            if commentary_field and hasattr(commentary_field, "search_field_1"):
                commentary_field.search_field_1.value = lemma_clean
            example_1_field: DpdExampleField | None = self.get_field("example_1")
            if example_1_field and hasattr(example_1_field, "word_to_find_field"):
                example_1_field.word_to_find_field.value = lemma_clean
            example_2_field: DpdExampleField | None = self.get_field("example_2")
            if example_2_field and hasattr(example_2_field, "word_to_find_field"):
                example_2_field.word_to_find_field.value = lemma_clean

        self.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def lemma_2_blur(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        new_value = self.get_field("lemma_1").value
        field.value = clean_lemma_1(new_value)
        self.page.update()

    def pos_blur(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)

        # test for wrong values
        if value not in self.db.all_pos:
            suggestions = find_closest_matches(
                value, list(self.db.all_pos or []), limit=3
            )
            if suggestions:
                field.error_text = ", ".join(suggestions)
            else:
                field.error_text = f"Unknown pattern: {value}"
            field.focus()
        else:
            field.error_text = None
        self.page.update()

        # then update lemma_2 based on lemma_1 and pos
        lemma_1 = self.get_field("lemma_1").value
        lemma_2_field = self.get_field("lemma_2")
        grammar = self.get_field("grammar").value
        lemma_2 = make_lemma_2(lemma_1, value, grammar)
        lemma_2_field.value = lemma_2
        self.page.update()

    def grammar_submit(self, e: ft.ControlEvent) -> None:
        field, value = self.get_event_field_and_value(e)
        pos = self.get_field("pos").value
        if pos in VERBS or pos in PARTICIPLES:
            field.value = f"{pos} of "
        elif pos in NOUNS:
            field.value = f"{pos}, "
        else:
            field.value = f"{pos}, "
        self.page.update()
        field.focus()

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
                self.flags.derived_from_done = True
                self.page.update()
                # derived_from_field.focus() # Focus might be better handled elsewhere or removed

    def compound_type_blur(self, e: ft.ControlEvent):
        compound_construction: DpdCompoundConstructionField = self.get_field(
            "compound_construction"
        )
        compound_construction.compound_construction_field.focus()
        self.page.update()

    def sanskrit_blur(self, e: ft.ControlEvent) -> None:
        """Get Sanskrit"""

        sanskrit_field = self.get_field("sanskrit")
        if not self.flags.sanskrit_done and not sanskrit_field.value:
            construction = self.get_field("construction").value
            constr_splits = construction.split(" + ")

            sanskrit = ""
            already_added = []
            for constr_split in constr_splits:
                results = (
                    self.db.db_session.query(DpdHeadword)
                    .filter(DpdHeadword.lemma_1.like(f"%{constr_split}%"))
                    .all()
                )
                for i in results:
                    if i.lemma_clean == constr_split:
                        if i.sanskrit not in already_added:
                            if constr_split != constr_splits[-1]:
                                sanskrit += f"{i.sanskrit} + "
                            else:
                                sanskrit += f"{i.sanskrit} "
                            already_added += [i.sanskrit]

            sanskrit = re.sub(r"\[.*?\]", "", sanskrit)  # remove square brackets
            sanskrit = re.sub("  ", " ", sanskrit)  # remove double spaces
            sanskrit = sanskrit.replace("+ +", "+")  # remove double plus signs
            sanskrit = sanskrit.strip()

            sanskrit_field.value = sanskrit
            self.flags.sanskrit_done = True  # Set the flag after auto-filling
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
                suffix = re.sub(r"\n.+", "", construction)  # Remove line 2
                suffix = re.sub(
                    r".+ \+ ", "", suffix
                )  # Remove everything up to the last ' + '
                suffix_field.value = suffix
                suffix_field.focus()  # Optional: shift focus to suffix field
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
            field.value = clean_lemma_1(lemma_1)
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

    def synonym_focus(self, e: ft.ControlEvent) -> None:
        """Auto-generate synonyms if the field is empty."""

        field, value = self.get_event_field_and_value(e)

        # Only run if the synonym field is currently empty
        # AND synonyms haven't been generated yet
        if not value and not self.flags.synonyms_done:
            pos = self.get_field("pos").value
            meaning_1 = self.get_field("meaning_1").value
            lemma_1 = self.get_field("lemma_1").value

            if pos and meaning_1 and lemma_1:
                synonyms_string = self.db.get_synonyms(pos, meaning_1, lemma_1)
                if synonyms_string:
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
        pattern_field = self.get_field("pattern")
        pattern_field.value = pattern

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
