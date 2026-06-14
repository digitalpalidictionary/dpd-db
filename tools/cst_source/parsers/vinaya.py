import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.text_utils import (
    get_text_and_number,
    is_int,
)


class Vin1Parser(BookParser):
    # there are four subdivisions
    # 1. chapter of rules = pārājika, saṅghādisesa, aniyata, nissaggiya, etc.
    # 2. vagga: in some cases, if more than 13 rules
    # 3. rule: name of the rule
    # 4. subhead: subsection of the rule
    # and corresponding chapter, vagga and title numbers

    books = ("vin1",)

    def update(self, x: element.Tag) -> None:
        book = "VIN1"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            if section == "Verañjakaṇḍaṃ":
                section_no = "0"
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}.{section_no}"
            self.sutta = section.lower()

            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title" and "vaggo" in x.text:
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}.{self.section_counter}.{vagga_no}"
            self.sutta = f"{self.section}, {vagga}".lower()

        elif x["rend"] == "title" and "vaggo" not in x.text:
            sutta, sutta_no = get_text_and_number(x.text)
            if self.vagga:
                self.source = self.source = (
                    f"{book}.{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                )
            else:
                self.source = self.source = f"{book}.{self.section_counter}.{sutta_no}"
            self.sutta = sutta.lower()
            self.sutta_counter = sutta_no

        elif x["rend"] == "subhead":
            subtitle, subtitle_no = get_text_and_number(x.text)
            self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class Vin2Parser(BookParser):
    books = ("vin2",)

    def update(self, x: element.Tag) -> None:
        if (
            # this switches is_bhikkhuni to True at the start of the Bhikkhunīvibhaṅgo
            # because bhikkhuni vinaya has its own logical sequence
            not self.is_bhikkhuni
            and x["rend"] == "book"
            and x.text == "Bhikkhunīvibhaṅgo"
        ):
            self.is_bhikkhuni = True
            self.source = ""
            self.sutta = ""

        if not self.is_bhikkhuni:
            book = "VIN2"

            if x["rend"] == "chapter":
                section, section_no = get_text_and_number(x.text.strip())
                self.section = section
                self.section_counter = section_no
                self.source = f"{book}.{section_no}"
                self.sutta = section.lower()
                self.vagga = ""
                self.vagga_counter = 0

            elif x["rend"] == "title" and "vaggo" in x.text:
                vagga, vagga_no = get_text_and_number(x.text.strip())
                self.vagga = vagga
                self.vagga_counter = vagga_no
                self.source = f"{book}.{self.section_counter}.{vagga_no}"
                self.sutta = f"{self.section}, {vagga}".lower()

            elif (
                x["rend"] == "title"
                and "vaggo" not in x.text
                or x["rend"] == "subhead"
            ):
                sutta, sutta_no = get_text_and_number(x.text.strip())
                if self.vagga:
                    self.source = (
                        f"{book}.{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                    )
                else:
                    self.source = f"{book}.{self.section_counter}.{sutta_no}"
                self.sutta = sutta.lower()

        # bhikkhuni vinaya
        elif self.is_bhikkhuni:
            book = "BHI VIN"

            def bhikkhuni_cleaner(text):
                return text.replace(" (bhikkhunīvibhaṅgo)", "")

            if x["rend"] == "chapter":
                section, section_no = get_text_and_number(x.text.strip())
                section = bhikkhuni_cleaner(section)
                self.section = section
                self.section_counter = section_no
                self.source = f"{book}{section_no}"
                self.sutta = section.lower()

                self.vagga = ""
                self.vagga_counter = 0

            elif x["rend"] == "title" and "vaggo" in x.text:
                vagga, vagga_no = get_text_and_number(x.text.strip())
                self.vagga = vagga
                self.vagga_counter = vagga_no
                self.source = f"{book}.{self.section_counter}.{self.vagga_counter}"
                self.sutta = f"{self.section}, {vagga}".lower()

            elif (
                x["rend"] == "subhead" and "vaggo" not in x.text
            ):  # there's only one exception "1. Pattavaggo"
                sutta, sutta_no = get_text_and_number(x.text.strip())
                if self.vagga:
                    self.source = (
                        f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                    )
                else:
                    self.source = f"{book}{self.section_counter}.{sutta_no}"

                if self.vagga:
                    self.sutta = f"{self.vagga}, {sutta}".lower()
                else:
                    if int(self.section_counter) == 3:  # only for nissaggiyakaṇḍaṃ
                        self.sutta = f"{self.section}, {sutta}".lower()
                    else:
                        self.sutta = f"{sutta}".lower()


class Vin3Vin4Parser(BookParser):
    # <head rend="chapter">1. Mahākhandhako</head>
    # <p rend="subhead">1. Bodhikathā</p>

    books = ("vin3", "vin4")

    def update(self, x: element.Tag) -> None:
        if self.book == "vin3":
            book = "VIN3"
        elif self.book == "vin4":
            book = "VIN4"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text.strip())
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}.{self.section_counter}"
            self.sutta = f"{section}".lower()

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text):
                sutta, sutta_mo = get_text_and_number(x.text.strip())
                if sutta.lower() not in [
                    "soṇassa pabbajjā",
                    "abhiññātānaṃ pabbajjā",  # these are bad subheads
                ]:
                    self.sutta_counter = sutta_mo
                    self.source = f"{book}.{self.section_counter}.{sutta_mo}"
                    self.sutta = f"{self.section}, {sutta}".lower()
            # else:
            #     subtitle, _ = get_text_and_number(x.text.strip())
            #     self.source = f"{book}.{self.section_counter}.{self.sutta_counter}"
            #     self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class Vin5Parser(BookParser):
    # <head rend="chapter">Soḷasamahāvāro</head>
    # <p rend="subhead">1. Anuvijjakaanuyogo</p>

    books = ("vin5",)

    def update(self, x: element.Tag) -> None:
        book_code = "VIN5"

        # Extract text and number once for the current element
        current_text, current_number = get_text_and_number(x.text.strip())
        self.section_counter = 0

        if x["rend"] == "chapter":  # Handles <head rend="chapter">Soḷasamahāvāro</head>
            self.vagga = current_text
            if is_int(current_number):
                self.vagga_counter = int(current_number)
            else:
                self.vagga_counter += 1
            # Reset lower-level counters when a new chapter starts
            self.source = f"{book_code}.{self.vagga_counter}"
            self.sutta = current_text.lower()

        elif x["rend"] == "subhead":
            self.sutta = f"{self.vagga}, {current_text}".lower()
