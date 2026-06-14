import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.text_utils import (
    get_text_and_number,
    get_text_and_number_with_brackets1,
    get_text_and_number_with_sqaure_brackets,
    is_int,
    split_sutta_number,
)


def ana_formatter(text: str) -> str:
    """an2_4 > AN2.4"""
    return text.replace("an", "").replace("_", ".")


class VinaParser(BookParser):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # section   <p rend="chapter">Verañjakaṇḍavaṇṇanā</p>
    # section   <p rend="chapter">4. Nissaggiyakaṇḍaṃ</p>
    # vagga     <p rend="title">1. Paṭhamapārājikaṃ</p>
    # vagga     <p rend="title">1. Cīvaravaggo</p>
    # <p rend="subhead">Sudinnabhāṇavāravaṇṇanā</p>

    books = ("vina",)

    def update(self, x: element.Tag) -> None:
        if x["rend"] == "book":
            if x.text == "Pārājikakaṇḍa-aṭṭhakathā (paṭhamo bhāgo)":
                self.vin_book = "VINa1"
            elif x.text == "Pācittiya-aṭṭhakathā":
                self.vin_book = "VINa2"
            elif x.text == "Bhikkhunīvibhaṅgavaṇṇanā":
                self.vin_book = "BHI VINa"
                self.section_counter = 0
            elif x.text == "Mahāvagga-aṭṭhakathā":
                self.vin_book = "VINa3"
                self.section_counter = 0
            elif x.text == "Cūḷavagga-aṭṭhakathā":
                self.vin_book = "VINa4"
                self.section_counter = 0
            elif x.text == "Parivāra-aṭṭhakathā":
                self.vin_book = "VINa5"
                self.section_counter = 0

        if x["rend"] in ["chapter", "subsubhead"]:
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter += 1

            self.source = f"{self.vin_book}.{self.section_counter}"
            self.sutta = section.lower()

            self.sutta_counter = 0
            self.vagga = ""
            self.vagga_counter = 0

            # exceptions
            if x.text in ["Verañjakaṇḍavaṇṇanā", "Ganthārambhakathā"]:
                self.section_counter = 0
                self.vagga_counter += 1
                self.source = f"{self.vin_book}.{self.section_counter}"

            if "bhikkhunīvibhaṅgavaṇṇanā" in x.text:
                section = section.replace(" (bhikkhunīvibhaṅgavaṇṇanā)", "")
                self.source = f"{self.vin_book}{self.section_counter}"
                self.sutta = section.lower()

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga

            if is_int(vagga_no):
                self.vagga_counter = vagga_no

            self.source = f"{self.vin_book}.{self.section_counter}.{self.vagga_counter}"
            self.sutta = self.vagga.lower()
            self.sutta_counter = 0

            # exceptions
            if self.vin_book == "BHI VINa":
                self.source = f"{self.vin_book}{self.section_counter}.{self.vagga_counter}"
            if x.text == "Bāhiranidānakathā":
                self.source = f"{self.vin_book}.0"
            if x.text == "Nigamanakathā":
                self.source = f"{self.vin_book}"

        elif x["rend"] == "subhead":
            if "(" not in x.text:
                sutta, sutta_no = get_text_and_number(x.text)
            else:
                sutta, sutta_no = get_text_and_number_with_brackets1(x.text)

            if self.vin_book != "BHI VINa":
                if is_int(sutta_no):
                    self.sutta_counter = int(sutta_no)

                    if self.vagga_counter:
                        self.source = f"{self.vin_book}.{self.section_counter}.{self.vagga_counter}.{self.sutta_counter}"
                        self.sutta = f"{self.vagga}, {sutta}".lower()

                    else:
                        self.source = f"{self.vin_book}.{self.section_counter}.{self.sutta_counter}"
                        self.sutta = f"{self.section}, {sutta}".lower()

                else:
                    if self.vin_book == "VINa1":
                        # intro
                        if self.section_counter == 0:
                            self.source = f"{self.vin_book}.{self.section_counter}"
                            self.sutta = sutta.lower()

                        # pārājika
                        elif self.section_counter == 1:
                            self.source = f"{self.vin_book}.{self.section_counter}.{self.vagga_counter}"
                            self.sutta = f"{self.vagga}, {sutta}".lower()

                    else:
                        self.sutta_counter += 1
                        self.source = f"{self.vin_book}.{self.section_counter}.{self.sutta_counter}"
                        self.sutta = f"{self.section}, {sutta}".lower()

            else:
                self.sutta_counter += 1
                self.source = f"{self.vin_book}{self.section_counter}.{self.sutta_counter}"
                self.sutta = sutta.lower()
                if self.vagga_counter:
                    self.source = (
                        f"{self.vin_book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                    )
                    self.sutta = f"{self.vagga}, {self.sutta}".lower()


class DnaParser(BookParser):
    # vagga   <head rend="subsubhead">Ganthārambhakathā</head>
    # vagga     <head rend="chapter">1. Brahmajālasuttavaṇṇanā</head>
    # sutta  <p rend="subhead">Paribbājakakathāvaṇṇanā</p>

    books = ("dna",)

    def update(self, x: element.Tag) -> None:
        book = "DNa"

        if x["rend"] == "subsubhead":
            self.source = f"{book}0"
            self.source_alt = f"{book}0"
            self.vagga = x.text.lower()

        elif x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga_alt_counter = vagga_no

            if vagga_no == "1":
                self.section_counter += 1
                match self.section_counter:
                    case 1:
                        self.vagga_counter = 0
                    case 2:
                        self.vagga_counter = 13
                    case 3:
                        self.vagga_counter = 23

            self.vagga = vagga.lower()
            self.vagga_counter += 1
            self.source = f"{book}{self.vagga_counter}"
            self.source_alt = f"{book}{self.section_counter}.{vagga_no}"
            self.sutta = vagga.lower()
            self.sutta_counter = 0

        if x["rend"] == "subhead":
            sutta, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.source_alt = (
                f"{book}{self.section_counter}.{self.vagga_alt_counter}.{self.sutta_counter}"
            )
            self.sutta = f"{self.vagga}, {sutta}".lower()


class DntParser(BookParser):
    # Mirrors DnaParser, plus a switch into the
    # Sīlakkhandhavaggaabhinavaṭīkā (s0104t/s0105t) detected on the book heading.
    # Regular ṭīkā: prefix DNt. Nava-ṭīkā (Sādhuvilāsinī): prefix DNnt
    # (CPD-style "n" marker for nava/abhinava; see abbreviations.tsv).

    books = ("dnt",)

    def update(self, x: element.Tag) -> None:
        is_abhinava: bool = self.is_abhinava

        if x["rend"] == "book":
            is_abhinava_now = "abhinava" in x.text.lower()
            if is_abhinava_now != is_abhinava:
                self.is_abhinava = is_abhinava_now
                self.section_counter = 0
                self.vagga_counter = 0
                self.sutta_counter = 0
            return

        book = "DNnt" if is_abhinava else "DNt"

        if x["rend"] == "subsubhead":
            self.source = f"{book}0"
            self.source_alt = f"{book}0"
            self.vagga = x.text.lower()

        elif x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga_alt_counter = vagga_no

            if vagga_no == "1":
                self.section_counter += 1
                if not is_abhinava:
                    match self.section_counter:
                        case 1:
                            self.vagga_counter = 0
                        case 2:
                            self.vagga_counter = 13
                        case 3:
                            self.vagga_counter = 23
                else:
                    self.vagga_counter = 0

            self.vagga = vagga.lower()
            self.vagga_counter += 1
            self.source = f"{book}{self.vagga_counter}"
            self.source_alt = f"{book}{self.section_counter}.{vagga_no}"
            self.sutta = vagga.lower()
            self.sutta_counter = 0

        if x["rend"] == "subhead":
            sutta, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.source_alt = (
                f"{book}{self.section_counter}.{self.vagga_alt_counter}.{self.sutta_counter}"
            )
            self.sutta = f"{self.vagga}, {sutta}".lower()


class MnaParser(BookParser):
    # ignore    <p rend="subhead">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subsubhead">Ganthārambhakathā</p>
    # vagga     <head rend="chapter">1. Mūlapariyāyavaggo</head>
    # sutta     <p rend="subhead">1. Mūlapariyāyasuttavaṇṇanā</p>

    books = ("mna",)

    def update(self, x: element.Tag) -> None:
        book = "MNa"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text.strip())
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text.strip())
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text):
                sutta, sutta_no = get_text_and_number(x.text.strip())
                self.sutta_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = sutta.lower()
            elif x.text == "Suttanikkhepavaṇṇanā":
                subtitle, _ = get_text_and_number(x.text.strip())
                self.subtitle_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()
            else:
                subtitle, subtitle_no = get_text_and_number(x.text.strip())
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class MntParser(BookParser):
    books = ("mnt",)

    def update(self, x: element.Tag) -> None:
        book = "MNt"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text.strip())
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text.strip())
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text):
                sutta, sutta_no = get_text_and_number(x.text.strip())
                self.sutta_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = sutta.lower()
            elif x.text == "Suttanikkhepavaṇṇanā":
                subtitle, _ = get_text_and_number(x.text.strip())
                self.subtitle_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()
            else:
                subtitle, subtitle_no = get_text_and_number(x.text.strip())
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class SnaParser(BookParser):
    # sutta     <head rend="subsubhead">Ganthārambhakathā</head>
    # samyutta  <head rend="chapter">1. Nidānasaṃyuttaṃ</head>
    # vagga     <p rend="title">1. Buddhavaggo</p>
    # sutta     <p rend="subhead">1. Paṭiccasamuppādasuttavaṇṇanā</p>

    books = ("sna",)

    def update(self, x: element.Tag) -> None:
        book = "SNa"

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}0"
            self.sutta = x.text.lower()

        elif x["rend"] == "chapter":
            samyutta, samyutta_no = get_text_and_number(x.text)
            self.samyutta = samyutta
            self.samyutta_counter += 1
            self.source = f"{book}{self.samyutta_counter}"
            self.sutta = samyutta.lower()
            self.sutta_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            if x.text == "Nigamanakathā":
                self.source = f"{book}{self.samyutta_counter}.{self.vagga_counter}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = (
                    f"{book}{self.samyutta_counter}.{self.vagga_counter}.{sutta_no}"
                )
                self.sutta = sutta.lower()


class SntParser(BookParser):
    books = ("snt",)

    def update(self, x: element.Tag) -> None:
        book = "SNt"

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}0"
            self.sutta = x.text.lower()

        elif x["rend"] == "chapter":
            samyutta, samyutta_no = get_text_and_number(x.text)
            self.samyutta = samyutta
            self.samyutta_counter += 1
            self.source = f"{book}{self.samyutta_counter}"
            self.sutta = samyutta.lower()
            self.sutta_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            if x.text == "Nigamanakathā":
                self.source = f"{book}{self.samyutta_counter}.{self.vagga_counter}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = (
                    f"{book}{self.samyutta_counter}.{self.vagga_counter}.{sutta_no}"
                )
                self.sutta = sutta.lower()


class AnaParser(BookParser):
    # div       <div id="an2_4" n="an2_4" type="peyyala">
    # book      <head rend="book">Dukanipāta-aṭṭhakathā</head>
    # sutta     <head rend="subsubhead">Ganthārambhakathā</head>
    # section   <p rend="title">Saṃkhepakathā</p>
    # vagga     <head rend="chapter">1. Rūpādivaggavaṇṇanā</head>
    # sutta     <p rend="subhead">Nidānavaṇṇanā</p>

    books = ("ana",)

    def update(self, x: element.Tag) -> None:
        book = "ANa"

        # find the book number
        try:
            self.anguttara_counter = ana_formatter(x.parent["id"])
            self.section_counter = re.sub(r"\..+", "", self.anguttara_counter)
        except KeyError:
            pass

        # find the sutta number using bodytext "n"
        if x["rend"] == "bodytext":
            try:
                self.sutta_counter = x.attrs["n"]
                self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            except KeyError:
                pass

        if x["rend"] == "subsubhead":
            self.sutta = x.text.lower()

        elif x["rend"] == "subhead":
            if x.text == "Nigamanakathā":
                self.source = "ANa"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta = sutta.lower()


class AntParser(BookParser):
    books = ("ant",)

    def update(self, x: element.Tag) -> None:
        book = "ANt"

        try:
            self.anguttara_counter = ana_formatter(x.parent["id"])
            self.section_counter = re.sub(r"\..+", "", self.anguttara_counter)
        except KeyError:
            pass

        if x["rend"] == "bodytext":
            try:
                self.sutta_counter = x.attrs["n"]
                self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            except KeyError:
                pass

        if x["rend"] == "subsubhead":
            self.sutta = x.text.lower()

        elif x["rend"] == "subhead":
            if x.text == "Nigamanakathā":
                self.source = book
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta = sutta.lower()


class AbhaParser(BookParser):
    # book      <p rend="book">Dhammasaṅgaṇī-aṭṭhakathā</p>  (volume marker, 3 vols)
    # intro     <p rend="subsubhead">Ganthārambhakathā</p>
    # chapter   <p rend="chapter">1. Cittuppādakaṇḍo</p>  (sometimes unnumbered)
    # title     <p rend="title">Sumedhakathā</p>           (sub-section context only)
    # sutta     <p rend="subhead">Kāyakammadvārakathā</p>

    books = ("abha",)

    def update(self, x: element.Tag) -> None:
        book = "ADha"

        if x["rend"] == "book":
            if "aṭṭhakathā" not in x.text:
                return
            self.vagga_counter += 1
            self.sutta_counter = 0
            self.vagga = x.text.lower()

        elif x["rend"] == "subsubhead":
            self.source = f"{book}0"
            self.sutta = x.text.lower()

        elif x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text.strip())
            if is_int(vagga_no):
                self.section_counter = int(vagga_no)
            else:
                self.section_counter += 1
            self.vagga = vagga.lower()
            self.sutta_counter = 0
            self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
            self.sutta = self.vagga

        elif x["rend"] == "title":
            subtitle, _ = get_text_and_number(x.text.strip())
            self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
            self.sutta = f"{self.vagga}, {subtitle}".lower()

        elif x["rend"] == "subhead":
            sutta, _ = get_text_and_number(x.text.strip())
            self.sutta_counter += 1
            self.source = (
                f"{book}{self.vagga_counter}.{self.section_counter}.{self.sutta_counter}"
            )
            self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn1aParser(BookParser):
    # <p rend="chapter">Ganthārambhakathā</p>

    books = ("kn1a",)

    def update(self, x: element.Tag) -> None:
        book = "KPa"

        if x["rend"] == "chapter":
            if x.text == "Ganthārambhakathā":
                section, section_no = get_text_and_number(x.text)
                self.section = section
                self.section_counter = 0
            else:
                section, section_no = get_text_and_number(x.text)
                self.section = section
                self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = f"{self.section}".lower()
            self.sutta_counter = 0

        elif x["rend"] == "subhead":
            sutta, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = f"{self.section}, {sutta}".lower()


class Kn2aParser(BookParser):
    # <p rend="title">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subhead">Ganthārambhakathā</p>
    # vagga     <p rend="chapter">1. Yamakavaggo</p>
    # sutta     <p rend="subhead">1. Cakkhupālattheravatthu</p>

    books = ("kn2a",)

    def update(self, x: element.Tag) -> None:
        book = "DHPa"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()

        if x["rend"] == "subhead":
            if x.text == "Ganthārambhakathā":
                self.source = f"{book}0"
                self.sutta = x.text.lower()
            elif x.text == "Nigamanakathā":
                self.source = f"{book}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter = sutta_no
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
                self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn3aParser(BookParser):
    # <p rend="chapter">Ganthārambhakathā</p>
    # <p rend="chapter">1. Bodhivaggo</p>
    # <p rend="subhead">1. Paṭhamabodhisuttavaṇṇanā</p>

    books = ("kn3a",)

    def update(self, x: element.Tag) -> None:
        book = "UDa"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            if x.text == "Ganthārambhakathā":
                self.source = f"{book}0"
                self.sutta = x.text.lower()
            elif x.text == "Nigamanakathā":
                self.source = f"{book}"
                self.sutta = x.text.lower()
            else:
                self.source = f"{book}{self.vagga_counter}"
                self.sutta = vagga.lower()

        if x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.sutta_counter_alt = sutta_no
            self.source = f"{book}{self.sutta_counter}"
            self.source_alt = f"{book}{self.vagga_counter}.{self.sutta_counter_alt}"
            self.sutta = f"{sutta}".lower()


class Kn4aParser(BookParser):
    # <p rend="subhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Ekakanipāto</p>
    # <p rend="title">1. Paṭhamavaggo</p>
    # <p rend="subhead">1. Lobhasuttavaṇṇanā</p>

    books = ("kn4a",)

    def update(self, x: element.Tag) -> None:
        book = "ITIa"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}"
            self.sutta = section.lower()

            self.vagga = ""

        if x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {self.vagga}".lower()

        if x["rend"] == "subhead":
            if x.text == "Ganthārambhakathā" or x.text == "Nidānavaṇṇanā":
                self.source = f"{book}0"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            elif x.text == "Nigamanakathā":
                self.source = f"{book}"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                if "-" in sutta_no:
                    start, end, diff = split_sutta_number(sutta_no)
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter + 1}-{self.sutta_counter + diff}"
                    self.sutta_counter += diff
                else:
                    self.sutta_counter += 1
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter}"
                    self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter_alt}"
                    self.sutta = f"{sutta}".lower()


class Kn5aParser(BookParser):
    # ignore    <p rend="title">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subhead">Ganthārambhakathā</p>
    # vagga     <p rend="chapter">1. Uragavaggo</p>
    # sutta     <p rend="subhead">1. Uragasuttavaṇṇanā</p>

    books = ("kn5a",)

    def update(self, x: element.Tag) -> None:
        book = "SNPa"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.vagga_counter}"
            self.sutta = f"{self.vagga}".lower()

        if x["rend"] == "subhead":
            if x.text == "Ganthārambhakathā" or x.text == "Nidānavaṇṇanā":
                self.source = f"{book}0"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            elif x.text == "Nigamanakathā":
                self.source = f"{book}"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            elif x.text == "Vatthugāthāvaṇṇanā":
                self.source = f"{book}55"
                self.source_alt = f"{book}5.0"
                self.sutta = x.text.lower()
            elif x.text == "Pārāyanatthutigāthāvaṇṇanā":
                self.source = f"{book}72"
                self.source_alt = f"{book}5.17"
                self.sutta = x.text.lower()
            elif x.text == "Pārāyanānugītigāthāvaṇṇanā":
                self.source = f"{book}73"
                self.source_alt = f"{book}5.18"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.sutta_counter_alt = sutta_no
                self.source = f"{book}{self.sutta_counter}"
                self.source_alt = f"{book}{self.vagga_counter}.{self.sutta_counter_alt}"
                self.sutta = f"{sutta}".lower()


class Kn6aParser(BookParser):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Itthivimānaṃ</p>
    # <p rend="title">1. Pīṭhavaggo</p>
    # <p rend="subhead">1. Paṭhamapīṭhavimānavaṇṇanā</p>
    # <p rend="subhead">Nigamanakathā</p>

    books = ("kn6a",)

    def update(self, x: element.Tag) -> None:
        book = "VVa"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}"
            self.sutta = section.lower()
            self.vagga = ""

        if x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {self.vagga}".lower()

        if x["rend"] in ["subhead", "subsubhead"]:
            if x.text == "Ganthārambhakathā":
                self.source = f"{book}0"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            elif x.text == "Nigamanakathā":
                self.source = f"{book}"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                if "-" in sutta_no:
                    start, end, diff = split_sutta_number(sutta_no)
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter + 1}-{self.sutta_counter + diff}"
                    self.sutta_counter += diff
                else:
                    self.sutta_counter += 1
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter}"
                    self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter_alt}"
                    self.sutta = f"{sutta}".lower()


class Kn7aParser(BookParser):
    # vagga     <p rend="chapter">1. Uragavaggo</p>
    # sutta     <p rend="subhead">1. Khettūpamapetavatthuvaṇṇanā</p>

    books = ("kn7a",)

    def update(self, x: element.Tag) -> None:
        book = "PVa"

        if x["rend"] == "subsubhead":
            self.source = f"{book}"
            self.sutta = x.text.lower()

        elif x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            vagga_no = re.sub(r"\. *.+", "", x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text):
                sutta, sutta_no = get_text_and_number(x.text)
                self.source = f"{book}{self.vagga_counter}.{sutta_no}"
                self.sutta = f"{sutta}".lower()
            else:
                self.source = f"{book}"
                self.sutta = x.text.lower()


class Kn8aKn9aParser(BookParser):
    # <p rend="title">(Paṭhamo bhāgo)</p>
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Ekakanipāto</p>
    # <p rend="title">1. Paṭhamavaggo</p>
    # <p rend="subhead">1. Subhūtittheragāthāvaṇṇanā</p>

    books = ("kn8a", "kn9a")

    def update(self, x: element.Tag) -> None:
        match self.book:
            case "kn8a":
                book = "THa"
            case "kn9a":
                book = "THIa"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}"
            self.sutta = section.lower()
            self.vagga = ""
            self.vagga_counter = 0

        if x["rend"] == "title" and not x.text.startswith("("):  # eg (Paṭhamo bhāgo)
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}"
            self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {self.vagga}".lower()

        if x["rend"] in ["subhead", "subsubhead"]:
            if (
                x.text == "Ganthārambhakathā"
                or x.text == "Nigamanagāthā"
                or x.text == "Nidānagāthāvaṇṇanā"
            ):
                self.source = f"{book}"
                self.source_alt = f"{book}"
                self.sutta = x.text.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                if "-" in sutta_no:
                    start, end, diff = split_sutta_number(sutta_no)
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter + 1}-{self.sutta_counter + diff}"
                    if self.vagga:
                        self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter_alt}"
                    else:
                        self.source_alt = (
                            f"{book}{self.section_counter}.{self.sutta_counter_alt}"
                        )
                    self.sutta_counter += diff
                else:
                    self.sutta_counter += 1
                    self.sutta_counter_alt = sutta_no
                    self.source = f"{book}{self.sutta_counter}"
                    if self.vagga:
                        self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter_alt}"
                    else:
                        self.source_alt = (
                            f"{book}{self.section_counter}.{self.sutta_counter_alt}"
                        )
                    self.sutta = f"{sutta}".lower()


class Kn10aParser(BookParser):
    # vagga     <p rend="subsubhead">Ganthārambhakathā</p>
    # vagga     <p rend="subsubhead">1. Dūrenidānakathā</p>
    # sutta  <p rend="subhead">Sumedhakathā</p>
    # vagga     <p rend="chapter">1. Buddhavaggo</p>
    # sutta     <p rend="subhead">Abbhantaranidānavaṇṇanā</p>

    books = ("kn10a",)

    def update(self, x: element.Tag) -> None:
        book = "APAa"

        if x["rend"] in ["subsubhead"]:
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = 0
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()

        elif x["rend"] in ["subhead"] and self.vagga_counter == 0:
            sutta, sutta_no = get_text_and_number(x.text)
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = sutta.lower()

        elif x["rend"] in ["chapter"]:
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()

        elif x["rend"] in ["subhead"]:
            if "-" in x.text and self.vagga_counter == "1":
                sutta, sutta_no = get_text_and_number(x.text)
                sutta_no = sutta_no.replace("-", ".")
                self.sutta_counter = sutta_no
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            elif x.text in ["Abbhantaranidānavaṇṇanā"]:
                sutta = x.text
                self.sutta_counter = 0
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            elif x.text in ["Nigamanakathā"]:
                sutta = x.text
                self.sutta_counter = ""
                self.source = f"{book}"
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter = sutta_no
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.sutta = f"{sutta}".lower()


class Kn12aParser(BookParser):
    # sutta         <p rend="subsubhead">Ganthārambhakathā</p>
    # section       <p rend="chapter">27. Gotamabuddhavaṃsavaṇṇanā</p>
    # sutta         <p rend="subhead">Dūrenidānakathā</p>

    books = ("kn12a",)

    def update(self, x: element.Tag) -> None:
        book = "BVa"

        if x["rend"] == "subsubhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.section_counter = 0
            self.source = f"{book}{self.section_counter}"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = self.section.lower()

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta = f"{self.section}, {sutta}".lower()


class Kn13aParser(BookParser):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Akittivaggo</p>
    # <p rend="subhead">1. Akitticariyāvaṇṇanā</p>

    books = ("kn13a",)

    def update(self, x: element.Tag) -> None:
        book = "CPa"

        if x["rend"] == "subsubhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.section_counter = 0
            self.source = f"{book}"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = self.section.lower()
            self.sutta_counter = 0

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = f"{sutta}".lower()


class Kn14aParser(BookParser):
    # bhaga     <p rend="title">(Paṭhamo bhāgo)</p>
    # nipāta    <p rend="chapter">1. Ekakanipāto</p>
    # vagga     <p rend="title">1. Apaṇṇakavaggo</p>
    # sutta     <p rend="bodytext"> 1. Apaṇṇakajātakavaṇṇanā</p>
    # sutta     <p rend="subhead">[111] 1. Gadrabhapañhajātakavaṇṇanā</p>
    # sutta     <p rend="subsubhead">Ganthārambhakathā</p>

    books = ("kn14a",)

    def update(self, x: element.Tag) -> None:
        book = "JAa"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "bodytext" and "jātakavaṇṇanā" in x.text:
            if x.text.strip().startswith("["):
                sutta, sutta_no = get_text_and_number_with_sqaure_brackets(
                    x.text.strip()
                )
                self.sutta_counter = sutta_no
                self.source = f"{book}{sutta_no}"
                self.sutta = sutta.lower()
            elif re.findall(r"^\d", x.text.strip()):
                sutta, sutta_no = get_text_and_number(x.text.strip())
                self.source = f"{book}{sutta_no}"
                self.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            if "jātakavaṇṇanā" in x.text:
                sutta, sutta_no = get_text_and_number_with_sqaure_brackets(
                    x.text.strip()
                )
                self.sutta = sutta.lower()
            else:
                subtitle, subtitle_no = get_text_and_number(x.text.strip())
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()

        elif x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = sutta.lower()


class Kn15aParser(BookParser):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="title">1. Aṭṭhakavaggo</p>
    # <p rend="chapter">1. Kāmasuttaniddesavaṇṇanā</p>

    books = ("kn15a",)

    def update(self, x: element.Tag) -> None:
        book = "NIDD1a"

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = sutta.lower()


class Kn16aParser(BookParser):
    # <p rend="chapter">Pārāyanavagganiddeso</p>
    # <p rend="subhead">1. Ajitamāṇavasuttaniddesavaṇṇanā</p>

    books = ("kn16a",)

    def update(self, x: element.Tag) -> None:
        book = "NIDD2a"

        if x["rend"] == "chapter":
            section, _ = get_text_and_number(x.text)
            self.section = section
            self.section_counter += 1
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

        if x["rend"] == "subhead":
            if x.text == "Nigamanakathā":
                sutta, _ = get_text_and_number(x.text)
                self.source = book
                self.sutta = sutta.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter = sutta_no
                self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
                if self.section_counter == 1:
                    self.sutta = sutta.lower()
                else:
                    self.sutta = f"{self.section}, {sutta}".lower()


class Kn17aParser(BookParser):
    # vagga     <p rend="chapter">(1) Mahāvaggo</p>
    # section   <p rend="chapter">1. Ñāṇakathā</p>
    # ignore    <p rend="title">(Dutiyo bhāgo)</p>
    # sutta     <p rend="title">70. Yamakapāṭihīrañāṇaniddesavaṇṇanā</p>
    # ignore    <p rend="subhead">Dutiyacchakkaṃ</p>

    books = ("kn17a",)

    def update(self, x: element.Tag) -> None:
        book = "PMa"

        ignore_list = [
            "(Paṭhamo bhāgo)",
            "(Dutiyo bhāgo)",
            "Paṭhamacchakkaṃ",
            "Dutiyacchakkaṃ",
            "Tatiyacchakkaṃ",
            "Cariyākathāvaṇṇanā",
            "Gatikathāvaṇṇanā",
            "Ka. assādaniddesavaṇṇanā",
            "Kha. ādīnavaniddesavaṇṇanā",
            "Ga. nissaraṇaniddesavaṇṇanā",
            "Ka. pabhedagaṇananiddesavaṇṇanā",
            "Kha. cariyāvāravaṇṇanā",
            "Ka. ādhipateyyaṭṭhaniddesavaṇṇan",
            "Kha. ādivisodhanaṭṭhaniddesavaṇṇanā",
            "Ga. adhimattaṭṭhaniddesavaṇṇanā",
            "Gha-ṅa. pariyādānaṭṭhapatiṭṭhāpakaṭṭhaniddesavaṇṇanāGatikathāvaṇṇanā",
            "Kammakathāvaṇṇanā",
            "Vipallāsakathāvaṇṇanā",
            "Maggakathāvaṇṇanā",
            "Maṇḍapeyyakathāvaṇṇanā",
            "Mahāpaññākathāvaṇṇanā",
            "Iddhikathāvaṇṇanā",
        ]

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            if x.text.startswith("("):  # (1) Mahāvaggo
                vagga, vagga_no = get_text_and_number_with_brackets1(x.text)
                self.vagga = vagga
                self.vagga_counter = vagga_no
                self.source = f"{book}{self.vagga_counter}"
                self.sutta = self.vagga.lower()
                self.section_counter = 0
            else:  # 6. Pāṭihāriyakathā
                section, section_no = get_text_and_number(x.text)
                self.section = section
                self.section_counter = section_no
                self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
                self.sutta = section.lower()
                self.sutta_counter = 0

        elif x["rend"] == "title" and x.text not in ignore_list:
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no
            if int(self.section_counter) > 0:
                self.source = (
                    f"{book}{self.vagga_counter}.{self.section_counter}.{self.sutta_counter}"
                )
            else:
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.sutta = sutta.lower()
            self.subtitle_counter = 0

        # elif x["rend"] == "subhead" and x.text not in ignore_list:
        #     subtitle, subtitle_no = get_text_and_number(x.text)
        #     self.subtitle_counter +=1
        #     self.source = f"{book}{self.vagga_counter}.{self.section_counter}.{self.sutta_counter}.{self.subtitle_counter}"
        #     self.sutta = subtitle.lower()


class Kn19aParser(BookParser):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <head rend="chapter">1. Saṅgahavāro</head>
    # <p rend="subhead">Tassānugīti</p>

    books = ("kn19a",)

    def update(self, x: element.Tag) -> None:
        book = "NPa"

        if x["rend"] == "subsubhead":
            vagga, _ = get_text_and_number(x.text)
            self.vagga = vagga
            self.source = f"{book}"
            self.sutta = vagga.lower()

        elif x["rend"] == "chapter":
            vagga, _ = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter += 1
            self.sutta_counter = 0
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()
            self.section_counter = 0

        elif x["rend"] == "subhead":
            if x.text == "1. Desanāhāravibhaṅgavaṇṇanā":
                self.section_counter += 1
            elif x.text == "1. Desanāhārasampātavaṇṇanā":
                self.section_counter += 1
                self.sutta_counter = 0
            elif x.text == "14. Adhiṭṭhānahārasampātavaṇṇanā":
                self.sutta_counter = 13
            sutta_name, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            if self.section_counter > 0:
                self.source = (
                    f"{book}{self.vagga_counter}.{self.section_counter}.{self.sutta_counter}"
                )
            else:
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.sutta = sutta_name.lower()
