import flet as ft

from gui2.dpd_fields_classes import DpdTextField

from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)
from tools.sandhi_contraction import SandhiContractionDict
from gui2.example_stash_manager import ExampleStashManager  # Import the new manager
from gui2.flet_functions import (
    highlight_word_in_sentence,
)
from gui2.dpd_fields_functions import clean_example

book_codes: dict[str, str] = {
    # vinaya
    "VIN1 Pārājika": "vin1",
    "VIN2 Pācittiya": "vin2",
    "VIN3 Mahāvagga": "vin3",
    "VIN4 Cūlavagga": "vin4",
    # dn
    "DN1 Sīlakkhandhavagga": "dn1",
    "DN2 Mahāvagga": "dn2",
    "DN3 Cūlavagga": "dn3",
    # mn
    "MN1 Mūlapaṇṇāsa": "mn1",
    "MN2 Majjhimapaṇṇāsa": "mn2",
    "MN3 Uparipaṇṇāsa": "mn3",
    # sn
    "SN1 sagāthāvagga": "sn1",
    "SN2 nidānavagga": "sn2",
    "SN3 khandhavagga": "sn3",
    "SN4 saḷāyatanavagga": "sn4",
    "SN5 mahāvagga": "sn5",
    # an
    "AN1 ekakanipāta": "an1",
    "AN2 dukanipāta": "an2",
    "AN3 tikanipāta": "an3",
    "AN4 catukkanipāta": "an4",
    "AN5 pañcakanipāta": "an5",
    "AN6 chakkanipāta": "an6",
    "AN7 sattakanipāta": "an7",
    "AN8 aṭṭhakanipāta": "an8",
    "AN9 navakanipāta": "an9",
    "AN10 dasakanipāta": "an10",
    "AN11 ekādasakanipāta": "an11",
    # kn
    "KP khuddakapāṭha": "kn1",
    "DHP dhammapada": "kn2",
    "UD udāna": "kn3",
    "ITI itivuttaka": "kn4",
    "SNP suttanipāta": "kn5",
    "VV vimanavatthu": "kn6",
    "PV petavatthu": "kn7",
    "TH theragāthā": "kn8",
    "THI therīgāthā": "kn9",
    "APA therāpadāna": "kn10",
    "API therīapadāna": "kn11",
    "BV buddhavaṃsa": "kn12",
    "CP cariyapitaka": "kn13",
    "JA jataka": "kn14",
    "NIDD1 mahaniddesa": "kn15",
    "NIDD2 culaniddesa": "kn16",
    "PM patisambhidamagga": "kn17",
    "MIL milindapañha": "kn18",
    "NP nettippakaraṇa": "kn19",
    "PTP peṭakopadesa": "kn20",
    # abhidhamma
    "ABH1 dhammasaṅgaṇī": "abh1",
    "ABH2 vibhaṅga": "abh2",
    "ABH3 dhātukathā": "abh3",
    "ABH4 puggalapaññatti": "abh4",
    "ABH5 kathāvatthu": "abh5",
    "ABH6 yamaka": "abh6",
    "ABH7 paṭṭhāna": "abh7",
    "VINa Aṭṭhakathā": "vina",
    # commentaries
    "DNa": "dna",
    "MNa": "mna",
    "SNa": "sna",
    "ANa": "ana",
    "KPa": "kn1a",
    "DHPa": "kn2a",
    "UDa": "kn3a",
    "ITIa": "kn4a",
    "SNPa": "kn5a",
    "VVa": "kn6a",
    "PVa": "kn7a",
    "THa": "kn8a",
    "THIa": "kn9a",
    "APAa": "kn10a",
    "BVa": "kn12a",
    "CPa": "kn13a",
    "JAa": "kn14a",
    "NIDD1a": "kn15a",
    "NIDD2a": "kn16a",
    "PMa": "kn17a",
    "NPa": "kn19a",
    "Visuddhimagga": "vism",
    "Visuddhimagga Ṭīkā": "visma",
    # aññā
    "abhidhānappadīpikā": "ap",
    "abhidhānappadīpikāṭīkā": "apt",
}


class DpdExampleField(ft.Column):
    def __init__(
        self,
        ui,
        field_name,
        dpd_fields,
        sandhi_dict,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        simple_mode: bool = False,  # Add simple_mode flag
    ):
        from gui2.dpd_fields import DpdFields
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass1AddView | Pass2AddView = ui
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields
        self.sandhi_dict: SandhiContractionDict = sandhi_dict
        self.simple_mode = simple_mode  # Store the flag
        self.stash_manager = ExampleStashManager()  # Instantiate the stash manager
        super().__init__(
            expand=True,
        )
        self.page: ft.Page = ui.page  # Assign page AFTER super().__init__

        self.text_field = DpdTextField(
            name=field_name,
            multiline=True,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        # --- Controls for Toggle Visibility ---
        if not self.simple_mode:
            self.book_options = [
                ft.dropdown.Option(key=item, text=item) for item in book_codes.keys()
            ]

            self.book_dropdown = ft.Dropdown(
                options=self.book_options,
                width=300,
                text_size=14,
                label="book",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
                editable=True,
                enable_filter=True,
                # autofocus=True, # Maybe not needed if hidden initially
            )

            self.word_to_find_field = ft.TextField(
                "",
                width=240,
                label="word to find",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
                on_submit=self._click_search_dialog_ok,
            )  # Keep on_submit for now, might need adjustment if dialog logic changes
            self.bold_field = ft.TextField(
                "",
                width=240,
                label="bold",
                label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
                on_submit=self.click_bold_example,
            )

            # Toggle Button
            self._toggle_tools_button = ft.IconButton(
                icon=ft.icons.VISIBILITY_OFF_OUTLINED,
                tooltip="Show Tools",
                on_click=self._toggle_tools_visibility,
                icon_color=ft.colors.BLUE_GREY_300,
            )

            # Search row (initially hidden)
            self._search_row = ft.Row(
                [
                    self.book_dropdown,
                    self.word_to_find_field,
                    self.bold_field,
                ],
                spacing=0,
                visible=False,  # Initially hidden
            )

            # Action buttons row (initially hidden)
            self._actions_row = ft.Row(
                [
                    ft.ElevatedButton("Clean", on_click=self.click_clean_example),
                    ft.ElevatedButton("Delete", on_click=self.click_delete_example),
                    ft.ElevatedButton("Swap", on_click=self.click_swap_example),
                    ft.ElevatedButton(
                        "Stash", on_click=self._click_stash_example
                    ),  # Add Stash button
                    ft.ElevatedButton(
                        "Reload", on_click=self._click_reload_example
                    ),  # Add Reload button
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                visible=False,  # Initially hidden
            )
        # --- End Toggle Visibility Controls ---

        self.controls = [
            self.text_field,
        ]
        # Add toggle button and hidden rows if not in simple mode
        if not self.simple_mode:
            self.controls.append(
                ft.Row(
                    [self._toggle_tools_button]
                )  # Button in its own row for alignment
            )
            self.controls.append(self._search_row)
            self.controls.append(self._actions_row)

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

    # --- Toggle Visibility Handling ---
    def _toggle_tools_visibility(self, e: ft.ControlEvent):
        """Toggles the visibility of the search and action rows."""
        are_visible = not self._search_row.visible  # Check current state
        self._search_row.visible = are_visible
        self._actions_row.visible = are_visible

        # Update button icon and tooltip
        if are_visible:
            self._toggle_tools_button.icon = ft.icons.VISIBILITY_OUTLINED
            self._toggle_tools_button.tooltip = "Hide Tools"
        else:
            self._toggle_tools_button.icon = ft.icons.VISIBILITY_OFF_OUTLINED
            self._toggle_tools_button.tooltip = "Show Tools"

        self.page.update()

    def _click_search_dialog_ok(self, e: ft.ControlEvent):
        """Handles search submission (e.g., from word_to_find_field on_submit)."""
        self.click_book_and_word(e)  # Call the search logic

    # --- End Dialog Handling ---

    def click_book_and_word(self, e: ft.ControlEvent):
        self.word_to_find_field.error_text = None
        if self.book_dropdown.value and self.word_to_find_field.value:
            self.cst_examples = find_cst_source_sutta_example(
                book_codes[self.book_dropdown.value],
                self.word_to_find_field.value,
            )
            if self.cst_examples:
                self.choose_example()
            else:
                self.word_to_find_field.focus()
                self.word_to_find_field.error_text = "no example found"
                self.page.update()
        self.word_to_find_field.focus()

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
                                ft.Text(
                                    spans=highlight_word_in_sentence(
                                        self.word_to_find_field.value, example
                                    ),
                                    expand=True,
                                    selectable=True,
                                ),
                            ]
                        ),
                    ],
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
                ft.TextButton("OK", on_click=self.click_choose_example_ok),
                ft.TextButton("Cancel", on_click=self.click_choose_example_cancel),
            ],
        )

        self.page.open(self.choose_example_dialog)
        self.page.update()

    def update_example_index(self, e):
        self.example_index = e.control.value

    def click_choose_example_cancel(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

    def get_fields(self):
        """Return fields for example 1 or 2"""

        if self.field_name == "example_1":
            i = 1
        else:
            i = 2
        source = self.dpd_fields.get_field(f"source_{i}")
        sutta = self.dpd_fields.get_field(f"sutta_{i}")
        example = self.dpd_fields.get_field(f"example_{i}")

        return source, sutta, example

    def click_choose_example_ok(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

        # add back into page
        cst_example = self.cst_examples[int(self.example_index)]
        source, sutta, example = self.get_fields()
        source.value = cst_example.source
        sutta.value = cst_example.sutta
        example.value = clean_example(cst_example.example, self.sandhi_dict)
        self.page.update()

    def click_bold_example(self, e: ft.ControlEvent):
        bold_word = e.control.value
        if self.value:
            self.value = self.value.replace(bold_word, f"<b>{bold_word}</b>")
        self.update()

    def click_clean_example(self, e: ft.ControlEvent):
        if self.value:
            self.value = self.value.replace("<b>", "").replace("</b>", "")
            self.update()

    def click_swap_example(self, e: ft.ControlEvent):
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

    def click_delete_example(self, e: ft.ControlEvent):
        source, sutta, example = self.get_fields()
        source.value = ""
        sutta.value = ""
        example.value = ""

        self.page.update()

    def _click_stash_example(self, e: ft.ControlEvent):
        """Stashes the current source, sutta, and example values."""
        source, sutta, example = self.get_fields()
        self.stash_manager.stash(
            source.value or "", sutta.value or "", example.value or ""
        )
        self.ui.update_message("Stashed current example data")

    def _click_reload_example(self, e: ft.ControlEvent):
        """Reloads stashed data into the source, sutta, and example fields."""
        stashed_data = self.stash_manager.reload()
        if stashed_data:
            source_val, sutta_val, example_val = stashed_data
            source, sutta, example = self.get_fields()
            source.value = source_val
            sutta.value = sutta_val
            example.value = example_val
            self.page.update()
            self.ui.update_message("Reloaded stashed example data")
        else:
            self.ui.update_message("No stashed data found")
