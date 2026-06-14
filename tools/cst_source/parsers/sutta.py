import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.peyyala_data import sn_collapsed_vagga_counts, sn_peyyalas
from tools.cst_source.text_utils import (
    clean_subtitle,
    get_text_and_number,
    get_text_and_number_with_brackets2,
)


class DighaParser(BookParser):
    # sutta     <head rend="chapter">1. Brahmajālasuttaṃ</head>
    # subtitle  <p rend="subhead">Paribbājakakathā</p>

    books = ("dn1", "dn2", "dn3")

    def __init__(self, book: str) -> None:
        super().__init__(book)
        match book:
            case "dn2":
                self.sutta_counter = 13
            case "dn3":
                self.sutta_counter = 23

    def update(self, x: element.Tag) -> None:
        book = "DN"

        if x["rend"] == "chapter":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            subtitle = clean_subtitle(x.text)
            self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class MajjhimaParser(BookParser):
    # vagga     <head rend="chapter">1. Mūlapariyāyavaggo</head>
    # sutta     <p rend="subhead">1. Mūlapariyāyasuttaṃ</p>

    books = ("mn1", "mn2", "mn3")

    def __init__(self, book: str) -> None:
        super().__init__(book)
        match book:
            case "mn2":
                self.sutta_counter = 50
            case "mn3":
                self.sutta_counter = 100

    def update(self, x: element.Tag) -> None:
        book = "MN"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text):
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.source_alt = f"{self.book.upper()}.{self.vagga_counter}.{sutta_no}"
                self.sutta = sutta.lower()
            else:
                subtitle = x.text
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class SamyuttaParser(BookParser):
    # main_vagga    <head rend="book">Sagāthāvaggo</head>
    # samyutta      <head rend="chapter">1. Devatāsaṃyuttaṃ</head>
    # vagga         <p rend="title">1. Naḷavaggo</p>
    # sutta         <p rend="subhead">1. Oghataraṇasuttaṃ</p>

    books = ("sn1", "sn2", "sn3", "sn4", "sn5")

    def __init__(self, book: str) -> None:
        super().__init__(book)
        match book:
            case "sn2":
                self.samyutta_counter = 11
            case "sn3":
                self.samyutta_counter = 21
            case "sn4":
                self.samyutta_counter = 34
            case "sn5":
                self.samyutta_counter = 44

    def update(self, x: element.Tag) -> None:
        sutta_name: str = ""
        book = "SN"

        if x["rend"] == "chapter":
            self.samyutta, _ = get_text_and_number(x.text)
            self.samyutta_counter += 1
            self.sutta = ""
            self.sutta_counter = 0
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "centre":
            text_lower = x.text.strip().lower()
            if "vitthāretabb" in text_lower:
                for (
                    samyutta_no,
                    vagga_pattern,
                ), sutta_count in sn_collapsed_vagga_counts.items():
                    if (
                        samyutta_no == self.samyutta_counter
                        and vagga_pattern in text_lower
                    ):
                        self.sutta_counter += sutta_count
                        break

        elif x["rend"] == "subhead":
            sutta_counter_special = ""
            peyyala_matched = False

            for peyyala in sn_peyyalas:
                p_samyutta_counter, p_sutta_name, p_start, p_end = peyyala
                if (
                    p_samyutta_counter == self.samyutta_counter
                    and x.text == p_sutta_name
                    and self.sutta_counter == p_start - 1
                ):
                    sutta_name = re.sub(r"^\d.*\. ", "", x.text).strip()
                    if p_start != p_end:
                        sutta_counter_special = f"{p_start}-{p_end}"
                    self.sutta_counter = p_end
                    peyyala_matched = True
                    break

            if not peyyala_matched and re.findall(r"^\d", x.text) and "-" not in x.text:
                sutta_name, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1

        if sutta_name:
            if sutta_counter_special:
                self.source = f"{book}{self.samyutta_counter}.{sutta_counter_special}"
            else:
                self.source = f"{book}{self.samyutta_counter}.{self.sutta_counter}"
            self.sutta = f"{self.samyutta}, {sutta_name}".lower()


class AnguttaraParser(BookParser):
    # vagga     <head rend="chapter">1. Rūpādivaggo</head>
    # subtitle  <p rend="subhead">1. Paṭhamavaggo</p>

    books = ("an1", "an2", "an3", "an4", "an5", "an6", "an7", "an8", "an9", "an10", "an11")

    def update(self, x: element.Tag) -> None:
        book_name = self.book.upper()

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number_with_brackets2(x.text)
            self.sutta = vagga.lower()
            self.vagga = vagga.lower()
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            subtitle, sutta_no = get_text_and_number(x.text)
            self.sutta = f"{self.sutta_clean}, {subtitle}".lower()
            self.sutta_counter = sutta_no

        elif x["rend"] == "bodytext" and x.has_attr("n"):
            self.sutta_counter = x["n"]
            self.source = f"{book_name}.{self.sutta_counter}"
            # self.source_alt = f"{book_name}.{self.vagga_counter}.{self.sutta_counter}"
