import flet as ft
from gui2.class_database import DatabaseManager
from tools.dpd_fields import find_stem_pattern, lemma_clean
from tools.pos import NOUNS, PARTICIPLES, POS, VERBS
from tools.spelling import CustomSpellChecker


class FieldConfig:
    def __init__(
        self,
        name,
        field_type="text",
        options=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,
    ):
        self.name = name
        self.field_type = field_type
        self.options = options
        self.on_change = on_change
        self.on_submit = on_submit
        self.on_blur = on_blur
        self.multiline = multiline


class DpdTextField(ft.TextField):
    def __init__(
        self,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,  # Default to single-line
    ):
        super().__init__(
            width=700,
            expand=True,
            multiline=multiline,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )


class DpdDropdown(ft.Dropdown):
    def __init__(
        self,
        options=None,
        on_change=None,
    ):
        if not options:
            raise ValueError("Options must be provided for DpdDropdown")
        super().__init__(
            width=700,
            expand=True,
            options=[ft.dropdown.Option(o) for o in options],
            on_change=on_change,
            editable=True,
            enable_filter=True,
        )


# Predefined field configurations for all DPD database columns


class DpdFields:
    def __init__(self, ui, db: DatabaseManager):
        self.ui = ui
        self.db = db
        self.spellchcker = CustomSpellChecker()
        self.fields = {}
        self.field_configs = [
            FieldConfig("id", on_submit=self.id_submit),
            FieldConfig(
                "lemma_1",
                on_change=self.lemma_1_change,
                on_submit=self.lemma_1_change,
                on_blur=self.lemma_1_change,
            ),
            FieldConfig("lemma_2", on_submit=self.lemma_2_submit),
            FieldConfig("pos", field_type="dropdown", options=POS),
            FieldConfig("grammar", on_submit=self.grammar_submit),
            FieldConfig("derived_from"),
            FieldConfig("neg"),
            FieldConfig("verb"),
            FieldConfig("trans"),
            FieldConfig("plus_case"),
            FieldConfig("meaning_1"),
            FieldConfig("meaning_lit"),
            FieldConfig(
                "meaning_2",
                on_submit=self.meaning_2_submit,
                on_blur=self.meaning_2_submit,
            ),
            FieldConfig("non_ia"),
            FieldConfig("sanskrit"),
            FieldConfig("root_key", field_type="dropdown", options=self.db.all_roots),
            FieldConfig("root_sign"),
            FieldConfig("root_base"),
            FieldConfig("family_root"),
            FieldConfig("family_word"),
            FieldConfig("family_compound"),
            FieldConfig("family_idioms"),
            FieldConfig("family_set"),
            FieldConfig("construction", multiline=True),
            FieldConfig("derivative"),
            FieldConfig("suffix"),
            FieldConfig("phonetic"),
            FieldConfig("compound_type"),
            FieldConfig("compound_construction"),
            FieldConfig("non_root_in_comps"),
            FieldConfig("source_1"),
            FieldConfig("sutta_1"),
            FieldConfig("example_1", multiline=True),
            FieldConfig("translation_1", multiline=True),
            FieldConfig("source_2"),
            FieldConfig("sutta_2"),
            FieldConfig("example_2", multiline=True),
            FieldConfig("translation_2", multiline=True),
            FieldConfig("antonym"),
            FieldConfig("synonym"),
            FieldConfig("variant"),
            FieldConfig("var_phonetic"),
            FieldConfig("var_text"),
            FieldConfig("commentary", multiline=True),
            FieldConfig("notes"),
            FieldConfig("cognate"),
            FieldConfig("link"),
            FieldConfig("origin"),
            FieldConfig("stem", on_submit=self.stem_submit),
            FieldConfig("pattern"),
        ]
        self.create_fields()

    def create_fields(self):
        for config in self.field_configs:
            if config.field_type == "text":
                self.fields[config.name] = DpdTextField(
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                    multiline=config.multiline,
                )
            elif config.field_type == "dropdown":
                self.fields[config.name] = DpdDropdown(
                    options=config.options, on_change=config.on_change
                )
            else:
                raise ValueError(f"Unsupported field type: {config.field_type}")

    def add_to_ui(self, ui_component, visible_fields: list[str] | None = None):
        for config in self.field_configs:
            row = ft.Row(
                [
                    ft.Text(config.name, width=250, color=ft.Colors.GREY_500),
                    self.fields[config.name],
                ]
            )
            if visible_fields is not None:
                row.visible = config.name in visible_fields
            ui_component.controls.append(row)

    def get_field(self, name):
        return self.fields.get(name, "")

    def get_field_value(self, e: ft.ControlEvent):
        field = e.control
        value = field.value
        return field, value

    def id_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        last_id = self.db.get_next_id()
        field.value = last_id
        self.ui.page.update()
        field.focus()

    def lemma_1_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        if value in self.db.all_lemma_1:
            field.error_text = f"{value} aleady in db"
        elif not value:
            field.error_text = "required field"
        else:
            field.error_text = None
        self.ui.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def lemma_2_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        new_value = self.get_field("lemma_1").value
        field.value = lemma_clean(new_value)
        self.ui.page.update()
        field.focus()

    def grammar_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        pos = self.get_field("pos").value
        if pos in VERBS or pos in PARTICIPLES:
            field.value = f"{pos} of "
        elif pos in NOUNS:
            field.value = f"{pos}, from "
        else:
            field.value = f"{pos}, "
        self.ui.page.update()
        field.focus()

    def meaning_2_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        misspelled = self.spellchcker.check_sentence(value)
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
        self.ui.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def stem_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        pos = self.get_field("pos").value
        grammar = self.get_field("grammar").value
        lemma_1 = self.get_field("lemma_1").value
        stem, pattern = find_stem_pattern(pos, grammar, lemma_1)
        field.value = stem
        pattern_field = self.get_field("pattern")
        pattern_field.value = pattern

        self.ui.page.update()
        field.focus()
