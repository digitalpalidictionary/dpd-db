import flet as ft

from gui2.dpd_fields_classes import DpdTextField

from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)
from tools.sandhi_contraction import SandhiContractionDict
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
    ):
        from gui2.dpd_fields import DpdFields
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass1AddView | Pass2AddView = ui
        self.page: ft.Page = ui.page
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields
        self.sandhi_dict: SandhiContractionDict = sandhi_dict
        super().__init__(
            expand=True,
        )

        self.text_field = DpdTextField(
            multiline=True,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        self.book_options = [
            ft.dropdown.Option(key=item, text=item) for item in book_codes.keys()
        ]

        self.book_dropdown = ft.Dropdown(
            options=self.book_options,
            width=300,
            text_size=14,
            # border_color=HIGHLIGHT_COLOUR,
            editable=True,
            enable_filter=True,
        )

        self.word_to_find_field = ft.TextField(
            "",
            width=240,
            hint_text="word to find",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            on_submit=self.click_book_and_word,
        )
        self.bold_field = ft.TextField(
            "",
            width=240,
            hint_text="bold",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            on_submit=self.click_bold_example,
        )

        self.controls = [
            self.text_field,
            ft.Row(
                [
                    self.book_dropdown,
                    self.word_to_find_field,
                ],
                spacing=0,
            ),
            ft.Row(
                [
                    self.bold_field,
                    ft.ElevatedButton("Clean", on_click=self.click_clean_example),
                    ft.ElevatedButton("Delete", on_click=self.click_delete_example),
                    ft.ElevatedButton("Swap", on_click=self.click_swap_example),
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

    def click_book_and_word(self, e: ft.ControlEvent):
        if self.book_dropdown.value and self.word_to_find_field.value:
            self.cst_examples = find_cst_source_sutta_example(
                book_codes[self.book_dropdown.value],
                self.word_to_find_field.value,
            )
            if self.cst_examples:
                self.choose_example()
            else:
                self.field.error_text = "no example found"

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
