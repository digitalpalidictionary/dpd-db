import flet as ft

from gui2.class_database import DatabaseManager
from gui2.def_dpd_fields import (
    clean_construction_line1,
    clean_lemma_1,
    clean_root,
    find_stem_pattern,
    make_construction,
    make_lemma_2,
)
from tools.pos import NOUNS, PARTICIPLES, POS, VERBS
from tools.spelling import CustomSpellChecker


class FieldConfig:
    def __init__(
        self,
        name,
        field_type="text",
        options=None,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,
    ):
        self.name = name
        self.field_type = field_type
        self.options = options
        self.on_focus = on_focus
        self.on_change = on_change
        self.on_submit = on_submit
        self.on_blur = on_blur
        self.multiline = multiline


class DpdTextField(ft.TextField):
    def __init__(
        self,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,  # Default to single-line
    ):
        super().__init__(
            width=700,
            expand=True,
            multiline=multiline,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
            max_lines=6,
            min_lines=1,
        )


class DpdDropdown(ft.Dropdown):
    def __init__(
        self,
        options=None,
        on_focus=None,
        on_change=None,
        on_blur=None,
    ):
        if not options:
            raise ValueError("Options must be provided for DpdDropdown")
        super().__init__(
            width=700,
            expand=True,
            options=[ft.dropdown.Option(o) for o in options],
            on_focus=on_focus,
            on_change=on_change,
            on_blur=on_blur,
            editable=True,
            enable_filter=True,
        )


# Predefined field configurations for all DPD database columns


class DpdFields:
    def __init__(self, ui, db: DatabaseManager):
        self.ui = ui
        self.db = db
        self.spellchecker = CustomSpellChecker()
        self.fields = {}
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
            FieldConfig("meaning_1"),
            FieldConfig("meaning_lit"),
            FieldConfig(
                "meaning_2",
                on_focus=self.meaning_2_change,
                on_blur=self.meaning_2_change,
            ),
            FieldConfig("non_ia"),
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
            FieldConfig("stem", on_submit=self.stem_submit, on_blur=self.stem_blur),
            FieldConfig("pattern"),
        ]

        # flags
        self.flag_construction_done: bool = False
        self.flag_stem_pattern_done: bool = False

        self.create_fields()

    def create_fields(self):
        for config in self.field_configs:
            if config.field_type == "text":
                self.fields[config.name] = DpdTextField(
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_submit=config.on_submit,
                    on_blur=config.on_blur,
                    multiline=config.multiline,
                )
            elif config.field_type == "dropdown":
                self.fields[config.name] = DpdDropdown(
                    options=config.options,
                    on_focus=config.on_focus,
                    on_change=config.on_change,
                    on_blur=config.on_blur,
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

    # automations

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

    def lemma_2_blur(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        new_value = self.get_field("lemma_1").value
        field.value = clean_lemma_1(new_value)
        self.ui.page.update()

    def pos_blur(self, e: ft.ControlEvent):
        # update lemma_2 based on lemma_1 and pos
        field, value = self.get_field_value(e)
        lemma_1 = self.get_field("lemma_1").value
        lemma_2_field = self.get_field("lemma_2")
        lemma_2 = make_lemma_2(lemma_1, value)
        lemma_2_field.value = lemma_2
        self.ui.page.update()

    def grammar_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        pos = self.get_field("pos").value
        if pos in VERBS or pos in PARTICIPLES:
            field.value = f"{pos} of "
        elif pos in NOUNS:
            field.value = f"{pos}, "
        else:
            field.value = f"{pos}, "
        self.ui.page.update()
        field.focus()

    def meaning_2_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
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
        self.ui.page.update()
        if e.name != "blur":  # only focus on submit, not on blur
            field.focus()

    def root_key_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
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
        self.ui.page.update()

    def root_sign_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

        # show all possible signs
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_sign(root_key)
            self.ui.page.update()
            field.focus()

    def root_sign_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        root_key = self.get_field("root_key").value
        if value and not root_key:
            field.error_text = "no root_key"
        elif not value and root_key:
            field.error_text = "no root_sign"
        else:
            field.error_text = None
        self.ui.page.update()

    def root_base_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_root_base(root_key)
            self.ui.page.update()
            field.focus()

    def family_root_submit(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

        # show all possible bases
        root_key = self.get_field("root_key").value
        if root_key:
            field.value = self.db.get_next_family_root(root_key)
            self.ui.page.update()
            field.focus()

    def family_root_blur(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

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
            self.ui.page.update()

    def family_word_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
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
        self.ui.page.update()

    def family_compound_change(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

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
        self.ui.page.update()

    def construction_blur(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)

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
            self.ui.page.update()
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
            self.ui.page.update()

    def stem_submit(self, e: ft.ControlEvent):
        self.update_stem(e)

    def stem_blur(self, e: ft.ControlEvent):
        if not self.flag_stem_pattern_done:
            self.update_stem(e)
            self.flag_stem_pattern_done = True

    def update_stem(self, e: ft.ControlEvent):
        field, value = self.get_field_value(e)
        pos = self.get_field("pos").value
        grammar = self.get_field("grammar").value
        lemma_1 = self.get_field("lemma_1").value
        stem, pattern = find_stem_pattern(pos, grammar, lemma_1)
        field.value = stem
        pattern_field = self.get_field("pattern")
        pattern_field.value = pattern

        self.ui.page.update()
        if e.name == "submit":
            field.focus()
