import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.text_utils import (
    get_text_and_number,
    get_text_and_number_with_brackets3,
    get_text_and_number_with_brackets_abhidhamma,
    is_int,
)


class Abh1Parser(BookParser):
    # <p rend="chapter">Mātikā</p>
    # <p rend="chapter">1. Cittuppādakaṇḍaṃ</p>
    # <p rend="title">Kāmāvacarakusalaṃ</p>
    # <p rend="subhead">Padabhājanī</p>
    # <p rend="subhead">1. Tikamātikā</p>

    books = ("abh1",)

    def update(self, x: element.Tag) -> None:
        book = "DHS"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section

            if is_int(section_no):
                self.section_counter = section_no
            else:
                self.section_counter = 0

            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

            # reset vagga
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter += 1

            self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {self.vagga}".lower()

            self.sutta_counter = 0

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1

            self.source = (
                f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter}"
            )
            if not self.vagga:
                self.sutta = f"{self.section}, {sutta}".lower()
            else:
                self.sutta = f"{self.vagga}, {sutta}".lower()


class Abh2Parser(BookParser):
    # <p rend="chapter">1. Khandhavibhaṅgo</p>
    # <p rend="title">1. Suttantabhājanīyaṃ</p>
    # <p rend="subhead">1. Rūpakkhandho</p>

    books = ("abh2",)

    def update(self, x: element.Tag) -> None:
        book = "VIBH"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section

            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

            # reset vagga
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter += 1

            self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {self.vagga}".lower()

            self.sutta_counter = 0

        elif x["rend"] == "subhead":
            if "(" in x.text:
                sutta, sutta_no = get_text_and_number_with_brackets_abhidhamma(x.text)
                if re.findall(r"\d", sutta_no):
                    self.sutta_counter = sutta_no
                    self.source = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter}"
                    self.sutta = f"{self.section}, {self.vagga}, {sutta}".lower()
                else:
                    self.sutta = f"{self.section}, {self.vagga}, {sutta}".lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1

                self.source = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter}"
                if not self.vagga:
                    self.sutta = f"xxxxxxx, {sutta}".lower()
                else:
                    self.sutta = f"{self.section}, {self.vagga}, {sutta}".lower()


class Abh3Parser(BookParser):
    # <p rend="chapter">Uddeso</p>
    # <p rend="subhead">1. Nayamātikā</p>
    # <p rend="chapter">1. Paṭhamanayo</p>
    # <p rend="title">1. Saṅgahāsaṅgahapadaniddeso</p>
    # <p rend="subhead">1. Khandho</p>
    # <p rend="subhead">2. Āyatanaṃ</p>

    books = ("abh3",)

    def update(self, x: element.Tag) -> None:
        book = "DHK"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            if is_int(section_no):
                self.section_counter = section_no
            else:
                self.section_counter = 0

            self.source = f"{book}{self.section_counter}"
            self.sutta = f"{self.section}".lower()

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

            self.source = f"{book}{self.vagga_counter}"
            self.sutta = f"{self.vagga}".lower()

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no

            self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            if self.section_counter == 0:
                self.sutta = f"{self.section}, {sutta}".lower()
            else:
                self.sutta = f"{self.vagga}, {sutta}".lower()


class Abh4Parser(BookParser):
    # <p rend="chapter">Mātikā</p>
    # <p rend="subhead">1. Ekakauddeso</p>

    books = ("abh4",)

    def update(self, x: element.Tag) -> None:
        book = "PP"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)

            self.section = section
            self.section_counter += 1

            self.source = f"{book}{self.section_counter}"
            self.sutta = f"{self.section}".lower()

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no

            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = f"{self.section}, {sutta}".lower()


class Abh5Parser(BookParser):
    # <p rend="chapter">1. Puggalakathā</p>
    # <p rend="title">1. Suddhasaccikaṭṭho</p>
    # <p rend="subhead">1. Anulomapaccanīkaṃ</p>

    books = ("abh5",)

    def update(self, x: element.Tag) -> None:
        book = "KV"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section

            if self.section_counter < 9:
                self.section_counter = int(section_no)
                self.source = f"{book}{self.section_counter}"
                self.sutta = f"{self.section}".lower()

        elif x["rend"] == "title":
            if x.text == "2. Dutiyavaggo":
                self.section_counter = 10

        if x["rend"] == "subhead" and self.section_counter >= 9:
            section, section_no = get_text_and_number_with_brackets3(x.text)
            self.section = section
            self.section_counter_alt = section_no

            self.source = f"{book}{self.section_counter_alt}"
            self.sutta = f"{self.section}".lower()


class Abh6Parser(BookParser):
    books = ("abh6",)

    def update(self, x: element.Tag) -> None:
        pass


class Abh7Parser(BookParser):
    books = ("abh7",)

    def update(self, x: element.Tag) -> None:
        pass
