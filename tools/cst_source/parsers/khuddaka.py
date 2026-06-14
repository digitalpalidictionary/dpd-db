import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.text_utils import (
    assert_type_int,
    get_text_and_number,
    get_text_and_number_with_brackets_end,
)


class Kn1Parser(BookParser):
    # sutta   <head rend="chapter">1. Saraṇattayaṃ</head>

    books = ("kn1",)

    def update(self, x: element.Tag) -> None:
        if x["rend"] == "chapter":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"KP{sutta_no}"
            self.sutta = sutta.lower()


class Kn2Parser(BookParser):
    # vagga         <head rend="chapter">1. Yamakavaggo</head>
    # sutta no      <p rend="hangnum" n="1"><hi rend="paranum">1</hi><hi rend="dot">.</hi></p>

    books = ("kn2",)

    def update(self, x: element.Tag) -> None:
        book = "DHP"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.sutta = f"{vagga}".lower()
            self.vagga_counter = vagga_no
            self.section_counter = 0

        elif x["rend"] == "hangnum":
            self.sutta_counter += 1
            self.section_counter += 1
            self.source = f"{book}{self.sutta_counter}"
            self.source_alt = f"{book}{self.vagga_counter}.{self.section_counter}"


class Kn3Parser(BookParser):
    # vagga     <head rend="chapter">1. Bodhivaggo</head>
    # sutta     <p rend="subhead">1. Paṭhamabodhisuttaṃ</p>

    books = ("kn3",)

    def update(self, x: element.Tag) -> None:
        book = "UD"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.sutta_counter}"
            self.source_alt = f"{book}{self.vagga_counter}.{sutta_no}"
            self.sutta = sutta.lower()


class Kn4Parser(BookParser):
    # section   <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Lobhasuttaṃ</p>

    books = ("kn4",)

    def update(self, x: element.Tag) -> None:
        book = "ITI"

        if x["rend"] == "chapter":
            section, self.section_counter = get_text_and_number(x.text)
            self.section = section
            self.section_counter = self.section_counter
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.sutta_counter}"
            if self.vagga_counter:
                self.source_alt = (
                    f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                )
            else:
                self.source_alt = f"{book}{self.section_counter}.{sutta_no}"
            self.sutta = sutta.lower()


class Kn5Parser(BookParser):
    # vagga <head rend="chapter">1. Uragavaggo</head>
    # sutta <p rend="subhead">1. Uragasuttaṃ</p>

    books = ("kn5",)

    def update(self, x: element.Tag) -> None:
        book = "SNP"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        if x["rend"] == "subhead":
            if x.text in ["Vatthugāthā", "Pārāyanatthutigāthā", "Pārāyanānugītigāthā"]:
                if x.text == "Vatthugāthā":
                    sutta_no = 0
                elif x.text == "Pārāyanatthutigāthā":
                    sutta_no = 17
                elif x.text == "Pārāyanānugītigāthā":
                    sutta_no = 18
                sutta, _ = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.source_alt = f"{book}{self.vagga_counter}.{sutta_no}"
                self.sutta = f"{self.vagga}, {sutta}".lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = f"{book}{self.sutta_counter}"
                self.source_alt = f"{book}{self.vagga_counter}.{sutta_no}"
                self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn6Parser(BookParser):
    # <head rend="chapter">1. Itthivimānaṃ</head>
    # <p rend="title">1. Pīṭhavaggo</p>
    # <p rend="subhead">1. Paṭhamapīṭhavimānavatthu</p>

    books = ("kn6",)

    def update(self, x: element.Tag) -> None:
        book = "VV"

        if x["rend"] == "chapter":
            section, self.section_counter = get_text_and_number(x.text)
            self.section = section
            self.section_counter = self.section_counter

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source_alt = (
                f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
            )
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn7Parser(BookParser):
    # <head rend="chapter">1. Uragavaggo</head>
    # <p rend="subhead">1. Khettūpamapetavatthu</p>

    books = ("kn7",)

    def update(self, x: element.Tag) -> None:
        book = "PV"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source_alt = f"{book}{self.vagga_counter}.{sutta_no}"
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn8Kn9Parser(BookParser):
    # sutta0    <p rend="subsubhead">Nidānagāthā</p>
    # section    <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Subhūtittheragāthā</p>

    books = ("kn8", "kn9")

    def update(self, x: element.Tag) -> None:
        match self.book:
            case "kn8":
                book = "TH"
            case "kn9":
                book = "THI"

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, self.section_counter = get_text_and_number(x.text)
            self.section = section
            self.section_counter = self.section_counter
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            sutta_no = sutta_no.replace("-", ".")
            self.sutta_counter += 1
            if self.vagga_counter == 0:
                self.source_alt = f"{book}{self.section_counter}.{sutta_no}"
            else:
                self.source_alt = (
                    f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                )
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = sutta.lower()


class Kn10Kn11Parser(BookParser):
    # sutta0    <p rend="subsubhead">Nidānagāthā</p>
    # section    <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Subhūtittheragāthā</p>

    books = ("kn10", "kn11")

    def __init__(self, book: str) -> None:
        super().__init__(book)
        if book == "kn11":
            self.sutta_counter = 422

    def update(self, x: element.Tag) -> None:
        if x["rend"] == "book" and x.text == "Therīapadānapāḷi":
            self.is_api = True
            self.sutta_counter = 0

        if self.is_api:
            book = "API"
        else:
            book = "APA"

        if x["rend"] == "subsubhead":
            sutta, _ = get_text_and_number(x.text)
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, self.section_counter = get_text_and_number(x.text)
            self.section = section
            self.section_counter = self.section_counter
            self.vagga = ""
            self.vagga_counter = 0

        elif x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        if x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            sutta_no = sutta_no.replace("-", ".")
            self.sutta_counter += 1
            if self.vagga_counter == 0:
                self.source_alt = f"{book}{self.section_counter}.{sutta_no}"
            else:
                self.source_alt = (
                    f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                )
            self.source = f"{book}{self.sutta_counter}"
            self.sutta = sutta.lower()


class Kn12Parser(BookParser):
    # sutta     <head rend="chapter">1. Ratanacaṅkamanakaṇḍaṃ</head>

    books = ("kn12",)

    def update(self, x: element.Tag) -> None:
        book = "BV"

        if x["rend"] == "chapter":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{sutta_no}"
            self.sutta = sutta.lower()


class Kn13Parser(BookParser):
    #   <head rend="chapter">1. Akittivaggo</head>
    #   <p rend="subhead">1. Akitticariyā</p>

    books = ("kn13",)

    def update(self, x: element.Tag) -> None:
        book = "CP"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}{self.sutta_counter}"
            self.source_alt = f"{book}{self.vagga_counter}.{sutta_no}"
            self.sutta = sutta.lower()


class Kn14Parser(BookParser):
    # <head rend="chapter">1. Ekakanipāto</head>
    # <p rend="title">1. Apaṇṇakavaggo</p>
    # <p rend="subhead">1. Apaṇṇakajātakaṃ</p>

    books = ("kn14",)

    def update(self, x: element.Tag) -> None:
        book = "JA"

        if x["rend"] == "chapter":
            section, self.section_counter = get_text_and_number(x.text)
            self.section = section
            self.section_counter = self.section_counter

        elif x["rend"] == "title":
            if x.text == "(Dutiyo bhāgo)":
                self.vagga = ""
            else:
                vagga, vagga_no = get_text_and_number(x.text)
                self.vagga = vagga
                self.vagga_counter = vagga_no

        elif x["rend"] == "subhead":
            if re.findall(r"^\d", x.text.strip()):
                sutta, sutta_no = get_text_and_number_with_brackets_end(x.text.strip())
                self.sutta_counter += 1
                # self.source_alt = f"{book}{self.section_counter}.{self.vagga_counter}.{sutta_no}"
                self.source = f"{book}{self.sutta_counter}"
                self.sutta = f"{sutta}".lower()
            else:
                subtitle, _ = get_text_and_number_with_brackets_end(x.text.strip())
                self.sutta = f"{self.sutta_clean}, {subtitle}".lower()


class Kn15Parser(BookParser):
    # <p rend="title">1. Aṭṭhakavaggo</p>
    # <head rend="chapter">1. Kāmasuttaniddeso</head>

    books = ("kn15",)

    def update(self, x: element.Tag) -> None:
        book = "NIDD1"

        if x["rend"] == "title":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = vagga_no

        if x["rend"] == "chapter":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter += 1
            self.source = f"{book}.{self.sutta_counter}"
            self.sutta = f"{sutta}".lower()


class Kn16Parser(BookParser):
    # <p rend="subsubhead">Pārāyanavaggo</p>
    # <p rend="subhead">Vatthugāthā</p>
    # <p rend="title">Khaggavisāṇasuttaniddeso</p>
    # <p rend="subhead">Paṭhamavaggo</p>
    # <head rend="chapter">Pārāyanavagganiddeso</head>
    # <p rend="subhead">1. Ajitamāṇavapucchāniddeso</p>

    books = ("kn16",)

    def update(self, x: element.Tag) -> None:
        book = "NIDD2"

        if x["rend"] == "subsubhead" or x["rend"] == "title" or x["rend"] == "chapter":
            if x.text == "Khaggavisāṇasutto":
                pass
            else:
                vagga, vagga_no = get_text_and_number(x.text)
                self.vagga = vagga
                self.vagga_counter += 1
                self.sutta_counter = 0

        elif x["rend"] == "subhead":
            if x.text == "Vatthugāthā":
                sutta, _ = get_text_and_number(x.text)
                self.source = f"{book}.{self.vagga_counter}.0"
                self.sutta = sutta.lower()
            else:
                sutta, sutta_no = get_text_and_number(x.text)
                self.sutta_counter += 1
                self.source = f"{book}.{self.vagga_counter}.{self.sutta_counter}"
                self.sutta = f"{self.vagga}, {sutta}".lower()


class Kn17Parser(BookParser):
    #         # vagga     <head rend="chapter">1. Mahāvaggo</head>
    #         # section   <p rend="title">1. Ñāṇakathā</p>
    #         # sutta     <p rend="subhead">Mātikā</p>
    #         # plus some subheads which needs to be pypassed

    books = ("kn17",)

    def update(self, x: element.Tag) -> None:
        book = "PM"

        if x["rend"] == "chapter":
            vagga, vagga_no = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter = assert_type_int(vagga_no)

            self.section = ""
            self.section_counter = 0
            self.sutta = ""
            self.sutta_counter = 0

        elif x["rend"] == "title":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = assert_type_int(section_no)

            self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
            self.sutta = f"{self.vagga}, {self.section}".lower()
            self.sutta_counter = 0

        elif x["rend"] == "subhead" and x.text not in [
            "Paṭhamacchakkaṃ",
            "Dutiyacchakkaṃ",
            "Tatiyacchakkaṃ",
            "Paṭhamacatukkaniddeso",
            "Dutiyacatukkaniddeso",
            "Tatiyacatukkaniddeso",
            "Catutthacatukkaniddeso",
            "Ka. assādaniddeso",
            "Kha. ādīnavaniddeso",
            "Ga. nissaraṇaniddeso",
            "Ka. pabhedagaṇananiddeso",
            "Kha. cariyavāro",
            "Ga. cāravihāraniddeso",
            "Ka. ādhipateyyaṭṭhaniddeso",
            "Kha. ādivisodhanaṭṭhaniddeso",
            "Ga. adhimattaṭṭhaniddeso",
            "Gha. adhiṭṭhānaṭṭhaniddeso",
            "Ṅa. pariyādānaṭṭhaniddeso",
            "Ca. patiṭṭhāpakaṭṭhaniddeso",
            "Mūlamūlakādidasakaṃ",
            "Suttantaniddeso",
            "Dasaiddhiniddeso",
        ]:
            sutta_name, sutta_no = get_text_and_number(x.text)

            if self.vagga and self.section and sutta_name:
                self.source = (
                    f"{book}{self.vagga_counter}.{self.section_counter}.{sutta_no}"
                )
                self.sutta = f"{self.section}, {sutta_name}".lower()
            elif self.vagga and not self.section and sutta_name:
                self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
                self.sutta = f"{self.vagga}, {sutta_name}".lower()
            elif self.vagga and self.section and not sutta_name:
                self.source = f"{book}{self.vagga_counter}.{self.section_counter}"
                self.sutta = f"{vagga}, {section}".lower()


class Kn18Parser(BookParser):
    #         # section   <p rend="subsubhead">1. Bāhirakathā</p>
    #         # section   <head rend="chapter">2-3. Milindapañho</head>
    #         # vagga     <p rend="title">1. Mahāvaggo</p>
    #         # sutta     <p rend="subhead">1. Paññattipañho</p>
    #         # plus some stray cats which needs to be handled individually

    books = ("kn18",)

    def update(self, x: element.Tag) -> None:
        book = "MIL"

        if x["rend"] == "chapter":
            if x.text == "Milindapañhapāḷi":
                self.section = "Milindapañhapāḷi"
                self.vagga = "Ārambhakathā"
                self.section_counter += 1
                self.vagga_counter += 1
            else:
                section, _ = get_text_and_number(x.text)
                self.section = section
                self.section_counter += 1
                self.vagga = ""
                self.vagga_counter = 0
                self.sutta = ""
                self.sutta_counter = 0
            self.source = f"{book}{self.section_counter}"
            self.sutta = self.section.lower()

        elif x["rend"] == "subsubhead":
            vagga, _ = get_text_and_number(x.text)
            self.vagga_counter += 1
            self.sutta_counter = 0
            self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
            self.sutta = f"{self.section}, {vagga}".lower()

        elif x["rend"] == "title":
            if x.text == "Meṇḍakapañhārambhakathā":
                self.section = x.text
                self.section_counter += 1
                self.vagga = ""
                self.vagga_counter = 0
                self.sutta_counter = 0
                self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
                self.sutta = self.section.lower()
            else:
                vagga, _ = get_text_and_number(x.text)
                self.vagga = vagga
                self.vagga_counter += 1
                self.sutta_counter = 0
                self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
                self.sutta = f"{self.section}, {vagga}".lower()

        elif x["rend"] == "subhead":
            sutta_name, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            if self.vagga_counter:
                self.source = (
                    f"{book}{self.section_counter}.{self.vagga_counter}.{self.sutta_counter}"
                )
            else:
                self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = sutta_name.lower()

        elif x["rend"] == "nikaya":
            if x.text == "Mātikā":
                vagga = x.text
                self.source = f"{book}{self.section_counter}.{self.vagga_counter}"
                self.sutta = f"{self.section}, {vagga}".lower()

            elif x.text == "Nigamanaṃ":
                self.section_counter += 1
                self.source = f"{book}{self.section_counter}"
                self.sutta = x.text.lower()


class Kn19Parser(BookParser):
    # <head rend="chapter">1. Saṅgahavāro</head>
    # <p rend="subhead">Tassānugīti</p>

    books = ("kn19",)

    def update(self, x: element.Tag) -> None:
        book = "NP"

        if x["rend"] == "chapter":
            vagga, _ = get_text_and_number(x.text)
            self.vagga = vagga
            self.vagga_counter += 1
            self.sutta_counter = 0
            self.source = f"{book}{self.vagga_counter}"
            self.sutta = vagga.lower()

        elif x["rend"] == "subhead":
            if x.text == "1. Desanāhāravibhaṅgo":
                self.section_counter += 1
            elif x.text == "1. Desanāhārasampāto":
                self.section_counter += 1
                self.sutta_counter = 0
            sutta_name, _ = get_text_and_number(x.text)
            self.sutta_counter += 1
            if self.section_counter > 0:
                self.source = (
                    f"{book}{self.vagga_counter}.{self.section_counter}.{self.sutta_counter}"
                )
            else:
                self.source = f"{book}{self.vagga_counter}.{self.sutta_counter}"
            self.sutta = sutta_name.lower()


class Kn20Parser(BookParser):
    # section   <head rend="chapter">1. Ariyasaccappakāsanapaṭhamabhūmi</head>
    # sutta     <p rend="subhead">Tatthāyaṃ <pb ed="V" n="0.0167" /> uddānagāthā</p>

    books = ("kn20",)

    def update(self, x: element.Tag) -> None:
        book = "PTP"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.sutta_counter = 0
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

        # elif x["rend"] == "subhead":
        #     sutta, sutta_no = get_text_and_number(x.text)
        #     self.sutta_counter += 1
        #     self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
        #     self.sutta = f"{self.section}, {sutta}".lower()
