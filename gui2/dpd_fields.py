import re
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
from gui2.dpd_fields_functions import (
    clean_construction_line1,
    clean_lemma_1,
    clean_root,
    find_stem_pattern,
    make_compound_construction_from_headword,
    make_construction,
    make_dpd_headword_from_dict,
    make_lemma_2,
)
from gui2.mixins import PopUpMixin
from tools.pos import DECLENSIONS, NOUNS, PARTICIPLES, POS, VERBS  # Import DECLENSIONS
from tools.sandhi_contraction import SandhiContractionDict
from tools.spelling import CustomSpellChecker


class DpdFields(PopUpMixin):
    def __init__(
        self,
        ui,
        db: DatabaseManager,
        sandhi_dict: SandhiContractionDict,
        simple_examples: bool = False,  # Add simple_examples flag
    ):
        super().__init__()  # Initialize PopUpMixin
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView = ui
        self.page = self.ui.page
        self.db: DatabaseManager = db
        self.spellchecker = CustomSpellChecker()
        self.sandhi_dict = sandhi_dict
        self.simple_examples = simple_examples  # Store the flag

        # Fetch compound types (ensure db is initialized first if needed)
        # Assuming db.initialize_db() has been called elsewhere before DpdFields is created
        compound_types_options = (
            self.db.all_compound_types if self.db.all_compound_types else []
        )

        self.fields = {}
        self.field_containers = {}  # To store the container for each field

        self.field_configs = [
            FieldConfig("id", on_submit=self.id_submit),
            FieldConfig(
                "lemma_1",
                on_change=self.lemma_1_change,
                on_submit=self.lemma_1_change,
                on_blur=self.lemma_1_change,
            ),
            FieldConfig("lemma_2", on_blur=self.lemma_2_blur),
            FieldConfig(
                "pos", field_type="dropdown", options=POS, on_blur=self.pos_blur
            ),
            FieldConfig("grammar", on_submit=self.grammar_submit),
            FieldConfig("derived_from"),
            FieldConfig("neg"),
            FieldConfig("verb"),
            FieldConfig("trans"),
            FieldConfig("plus_case"),
            FieldConfig("meaning_1", multiline=True),
            FieldConfig("meaning_lit"),
            FieldConfig(
                "meaning_2",
                on_focus=self.meaning_2_change,
                on_blur=self.meaning_2_change,
            ),
            FieldConfig("non_ia", on_blur=self.non_ia_blur),
            FieldConfig("sanskrit"),
            FieldConfig(
                "root_key",
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
            FieldConfig("root_base", on_submit=self.root_base_submit),
            FieldConfig(
                "family_root",
                on_submit=self.family_root_submit,
                on_blur=self.family_root_blur,
            ),
            FieldConfig(
                "family_word",
                on_focus=self.family_word_change,
                on_change=self.family_word_change,
                on_blur=self.family_word_change,
            ),
            FieldConfig(
                "family_compound",
                on_focus=self.family_compound_change,
                on_change=self.family_compound_change,
                on_blur=self.family_compound_change,
            ),
            FieldConfig("family_idioms"),
            FieldConfig("family_set"),
            FieldConfig("construction", multiline=True, on_blur=self.construction_blur),
            FieldConfig(
                "derivative",
                field_type="dropdown",
                options=["kita", "kicca", "taddhita"],
                on_change=self._derivative_change,
            ),
            FieldConfig("suffix"),
            FieldConfig("phonetic"),
            FieldConfig(
                "compound_type",
                field_type="dropdown",
                options=compound_types_options,
                on_change=self._compound_type_change,
            ),
            FieldConfig("compound_construction", field_type="compound_construction"),
            FieldConfig("non_root_in_comps"),
            FieldConfig("source_1"),
            FieldConfig("sutta_1"),
            FieldConfig("example_1", field_type="example"),
            FieldConfig("translation_1", multiline=True),
            FieldConfig("source_2"),
            FieldConfig("sutta_2"),
            FieldConfig("example_2", field_type="example"),
            FieldConfig("translation_2", multiline=True),
            FieldConfig("antonym"),
            FieldConfig("synonym"),
            FieldConfig("variant"),
            FieldConfig("var_phonetic"),
            FieldConfig("var_text"),
            FieldConfig("commentary", field_type="commentary"),
            FieldConfig("notes"),
            FieldConfig("cognate"),
            FieldConfig("link"),
            FieldConfig("origin"),
            FieldConfig("stem", on_submit=self.stem_submit, on_blur=self.stem_blur),
            FieldConfig("pattern"),
            FieldConfig("comment", multiline=True),
        ]

        # flags
        self.flag_construction_done: bool = False
        self.flag_stem_pattern_done: bool = False

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

            elif config.field_type == "example":
                self.fields[config.name] = DpdExampleField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    sandhi_dict=self.sandhi_dict,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                    simple_mode=self.simple_examples,  # Pass the flag
                )

            elif config.field_type == "commentary":
                self.fields[config.name] = DpdCommentaryField(
                    self.ui,
                    field_name=config.name,
                    dpd_fields=self,
                    sandhi_dict=self.sandhi_dict,
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

            else:
                raise ValueError(f"Unsupported field type: {config.field_type}")

            # Create corresponding _add field
            self.fields[f"{config.name}_add"] = DpdText()

    def _create_field_container(
        self, field_name: str, include_add_fields: bool
    ) -> ft.Column:
        """Creates a container holding the label and field row for a single field."""
        label_row = ft.Row([ft.Text(field_name, color=ft.Colors.GREY_500, size=10)])
        field_row = self._create_field_row(field_name, include_add_fields)
        return ft.Column([label_row, field_row], spacing=0)  # Group label and field

    def add_to_ui(
        self,
        ui_component,
        visible_fields: list[str] | None = None,
        include_add_fields: bool = False,
    ):
        for config in self.field_configs:
            field_name = config.name

            # Create the container for this field
            container = self._create_field_container(field_name, include_add_fields)

            if visible_fields is not None:
                container.visible = field_name in visible_fields
            else:
                container.visible = True  # Default to visible if no filter specified

            # Store the container and add it to the UI
            self.field_containers[field_name] = container
            ui_component.controls.append(container)

    def _create_field_row(self, field_name: str, include_add_fields: bool) -> ft.Row:
        """Creates the row containing the main field and optional add field/button."""
        main_field = self.fields[field_name]
        row_controls = [main_field]

        if include_add_fields:
            add_field = self.fields.get(f"{field_name}_add")
            if add_field:
                transfer_btn = ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_size=20,
                    tooltip="Copy to db field",
                    # Use a lambda that captures the correct field names
                    on_click=lambda e,
                    mf=main_field,
                    af=add_field: self.transfer_add_value(e, mf, af),
                )
                row_controls.extend([transfer_btn, add_field])

        return ft.Row(
            row_controls,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def filter_fields(self, visible_fields: list[str] | None = None):
        """Shows only the specified fields, hides others. Shows all if None."""
        for field_name, container in self.field_containers.items():
            main_field = self.fields.get(field_name)
            has_value = bool(
                main_field and main_field.value
            )  # Check if the main field has a value

            if visible_fields is None or field_name in visible_fields:
                container.visible = True
            else:
                # Only hide if it's not in the visible list AND it has no value
                if not has_value:
                    container.visible = False
                else:  # Keep visible if it has a value, even if not in the filter list
                    container.visible = True

    def update_db_fields(self, headword: DpdHeadword) -> None:
        """Update the left hand side fields with headword data."""

        headword_dict = vars(headword)

        for key, value in headword_dict.items():
            if key in self.fields:
                self.fields[key].value = value
                self.fields[key].error_text = None

        self.page.update()

    def update_add_fields(self, data: dict[str, str]) -> None:
        """Update _add fields from provided data dictionary."""

        for name, value in data.items():
            add_name = f"{name}_add"
            if add_name in self.fields:
                self.fields[add_name].value = value
                self.fields[add_name].error_text = None

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
                control.value = ""
                control.error_text = None
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

    def transfer_add_value(self, e, field, add_field):
        if add_field.value:
            field.value = add_field.value
            self.page.update()

    def get_field(self, name):
        return self.fields.get(name, "")

    def get_event_field_value(self, e: ft.ControlEvent):
        field = e.control
        value = field.value
        return field, value

    def get_current_headword(self) -> DpdHeadword:
        """Get all current field values as a dictionary
        and make a DpdHeadword instance from it."""

        values = {name: field.value for name, field in self.fields.items()}
        return make_dpd_headword_from_dict(values)

    # --- AUTOMATION ---

    def id_submit(self, e: ft.ControlEvent):
        """Get the next id on submit."""
        field, value = self.get_event_field_value(e)
        field.value = self.db.get_next_id()
        field.focus()
        self.page.update()

    def lemma_1_change(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
        if value in self.db.all_lemma_1:
            field.error_text = f"{value} already in db"
        elif not value:
            field.error_text = "required field"
        else:
            field.error_text = None
        self.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def lemma_2_blur(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
        new_value = self.get_field("lemma_1").value
        field.value = clean_lemma_1(new_value)
        self.page.update()

    def pos_blur(self, e: ft.ControlEvent):
        # update lemma_2 based on lemma_1 and pos
        field, value = self.get_event_field_value(e)
        lemma_1 = self.get_field("lemma_1").value
        lemma_2_field = self.get_field("lemma_2")
        lemma_2 = make_lemma_2(lemma_1, value)
        lemma_2_field.value = lemma_2
        self.page.update()

    def grammar_submit(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
        pos = self.get_field("pos").value
        if pos in VERBS or pos in PARTICIPLES:
            field.value = f"{pos} of "
        elif pos in NOUNS:
            field.value = f"{pos}, "
        else:
            field.value = f"{pos}, "
        self.page.update()
        field.focus()

    def meaning_2_change(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
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
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def non_ia_blur(self, e: ft.ControlEvent) -> None:
        """Get Sanskrit"""

        sanskrit_field = self.get_field("sanskrit")
        if not sanskrit_field.value:
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
            self.page.update()

    def root_key_change(self, e: ft.ControlEvent):
        """Test root_key"""

        field, value = self.get_event_field_value(e)
        # test if root key exists
        if value:
            if value not in self.db.all_roots:
                field.error_text = f"{value} unknown root"
                field.focus()
            else:
                field.error_text = None
                field.helper_text = self.db.get_root_string(value)
        else:
            field.helper_text = None
            field.error_text = None
        self.page.update()

    def root_sign_submit(self, e: ft.ControlEvent):
        """Load root_sign from db."""
        field, value = self.get_event_field_value(e)

        # show all possible signs
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_sign(root_key)
            self.page.update()
            field.focus()

    def root_sign_change(self, e: ft.ControlEvent):
        """Test root_sign."""

        field, value = self.get_event_field_value(e)
        root_key = self.get_field("root_key").value
        if value and not root_key:
            field.error_text = "no root_key"
        elif not value and root_key:
            field.error_text = "no root_sign"
        else:
            field.error_text = None
        self.page.update()

    def root_base_submit(self, e: ft.ControlEvent):
        """Get root_base from db."""

        field, value = self.get_event_field_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_base(root_key)
            self.page.update()
            field.focus()

    def family_root_submit(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_family_root(root_key)
            self.page.update()
            field.focus()

    def family_root_blur(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)

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

    def _compound_type_change(self, e: ft.ControlEvent):
        """When compound_type changes, try to generate compound_construction."""

        compound_construction_field = self.get_field("compound_construction")

        if not compound_construction_field.value:
            current_headword = self.get_current_headword()  # Get current data
            cc = make_compound_construction_from_headword(current_headword)
            compound_construction_field.value = cc
            compound_construction_field.focus()
            self.page.update()

    def _derivative_change(self, e: ft.ControlEvent):
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

    def family_word_change(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
        root_key = self.get_field("root_key").value

        # test if in word families
        if value:
            if root_key:
                field.error_text = "root_key and family_word"
            elif " " in value:
                field.error_text = "family_word contains space"
            elif value not in self.db.all_word_families:
                field.error_text = f"{value}"
            else:
                field.error_text = None
        else:
            field.error_text = None
        self.page.update()

    def family_compound_change(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)

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

    def construction_blur(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)

        if not value and not self.flag_construction_done:
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
            self.flag_construction_done = True

        elif value:
            # test words are in all_lemma_clean
            construction_line1 = clean_construction_line1(value)
            error_list = [
                word
                for word in construction_line1.split(" + ")
                if self.db.all_lemma_clean and word not in self.db.all_lemma_clean
            ]
            if error_list:
                field.error_text = f"{', '.join(error_list)} "
            else:
                field.error_text = None
            self.page.update()

    def stem_submit(self, e: ft.ControlEvent):
        self.update_stem(e)

    def stem_blur(self, e: ft.ControlEvent):
        if not self.flag_stem_pattern_done:
            self.update_stem(e)
            self.flag_stem_pattern_done = True

    def update_stem(self, e: ft.ControlEvent):
        field, value = self.get_event_field_value(e)
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
