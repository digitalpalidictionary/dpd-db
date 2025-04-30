import flet as ft


from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)


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
        multiline=False,
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


class DpdText(ft.Text):
    def __init__(
        self,
    ):
        super().__init__(
            width=700,
            expand=True,
            selectable=True,
            color=ft.Colors.GREY_500,
            size=16,
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


class DpdExampleField(ft.Column):
    def __init__(
        self,
        page,
        field_name,
        dpd_fields,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
    ):
        from gui2.dpd_fields import DpdFields

        self.page: ft.Page = page
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields
        super().__init__(
            width=700,
            expand=True,
        )
        self.text_field = DpdTextField(
            multiline=True,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        self.bold_field = ft.TextField("", width=240, on_submit=self.click_bold_example)

        self.controls = [
            self.text_field,
            ft.Row(
                [
                    self.bold_field,
                    ft.ElevatedButton("Get", on_click=self.get_book_and_word),
                    ft.ElevatedButton("Clean", on_click=self.click_clean_example),
                    ft.ElevatedButton("Delete", on_click=self.click_delete_example),
                    ft.ElevatedButton("Swap", on_click=self.swap_example),
                ],
                spacing=0,
            ),
        ]
        self.spacing = 0
        self.cst_examples: list[CstSourceSuttaExample] = []
        self.example_index: str = ""

    @property
    def value(self):
        return self.text_field.value

    @property
    def field(self):
        return self.text_field

    @value.setter
    def value(self, value):
        self.text_field.value = value

    def click_bold_example(self, e: ft.ControlEvent):
        bold_word = e.control.value
        if self.value:
            self.value = self.value.replace(bold_word, f"<b>{bold_word}</b>")
        self.update()

    def click_delete_example(self, e: ft.ControlEvent):
        self.value = ""
        self.update()

    def get_book_and_word(self, e: ft.ControlEvent):
        self.book_input = ft.TextField(
            hint_text="book", autofocus=True
        )  # TODO how to make on_submit jump to the next word?
        self.word_input = ft.TextField(
            hint_text="word", on_submit=self.click_book_and_word_ok
        )

        self.get_book_and_word_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                height=150,
                controls=[self.book_input, self.word_input],
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=self.click_book_and_word_cancel),
                ft.TextButton("OK", on_click=self.click_book_and_word_ok),
            ],
        )
        self.page.open(self.get_book_and_word_dialog)
        self.page.update()

    def click_book_and_word_cancel(self, e: ft.ControlEvent):
        self.get_book_and_word_dialog.open = False
        self.page.update()

    def click_book_and_word_ok(self, e: ft.ControlEvent):
        self.get_book_and_word_dialog.open = False
        self.page.update()
        if self.book_input.value and self.word_input.value:
            self.cst_examples = find_cst_source_sutta_example(
                self.book_input.value,
                self.word_input.value,
            )
            if self.cst_examples:
                self.choose_example()
            else:
                print("no examples found - add to message updater")

    def choose_example(self):
        if not self.cst_examples:
            return

        example_list = []

        for counter, i in enumerate(self.cst_examples):
            source, sutta, example = i
            example_list.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Radio(width=30, value=str(counter)),
                                ft.Text(
                                    source,
                                    selectable=True,
                                    color=ft.Colors.BLUE_200,
                                ),
                                ft.Text(
                                    sutta,
                                    selectable=True,
                                    color=ft.Colors.BLUE_200,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("", width=30),
                                ft.Text(example, expand=True, selectable=True),
                            ]
                        ),
                    ]
                )
            )

        radio_group = ft.RadioGroup(
            content=ft.Column(
                controls=example_list,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            on_change=self.update_example_index,
        )

        self.choose_example_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[radio_group],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=self.click_choose_example_cancel),
                ft.TextButton("OK", on_click=self.click_choose_example_ok),
            ],
        )

        self.page.open(self.choose_example_dialog)
        self.page.update()

    def update_example_index(self, e):
        self.example_index = e.control.value

    def click_choose_example_cancel(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

    def click_choose_example_ok(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

        # add back into page
        cst_example = self.cst_examples[int(self.example_index)]
        if self.field_name == "example_1":
            i = 1
        else:
            i = 2
        source = self.dpd_fields.get_field(f"source_{i}")
        sutta = self.dpd_fields.get_field(f"sutta_{i}")
        example = self.dpd_fields.get_field(f"example_{i}")

        source.value = cst_example.source
        sutta.value = cst_example.sutta
        example.value = cst_example.example
        self.page.update()

        # load example

    def click_clean_example(self, e: ft.ControlEvent):
        if self.value:
            self.value = self.value.replace("<b>", "").replace("</b>", "")
            self.update()

    def swap_example(self, e: ft.ControlEvent):
        source_x = ""
        sutta_x = ""
        example_x = ""

        source_1 = self.dpd_fields.get_field("source_1")
        sutta_1 = self.dpd_fields.get_field("sutta_1")
        example_1 = self.dpd_fields.get_field("example_1")

        source_2 = self.dpd_fields.get_field("source_2")
        sutta_2 = self.dpd_fields.get_field("sutta_2")
        example_2 = self.dpd_fields.get_field("example_2")

        source_x = source_1.value
        sutta_x = sutta_1.value
        example_x = example_1.value

        source_1.value = source_2.value
        sutta_1.value = sutta_2.value
        example_1.value = example_2.value

        source_2.value = source_x
        sutta_2.value = sutta_x
        example_2.value = example_x

        self.page.update()
