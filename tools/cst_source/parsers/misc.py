import re

from bs4 import element

from tools.cst_source.parsers.base import BookParser
from tools.cst_source.text_utils import (
    get_text_and_number,
    is_int,
)


class KvaParser(BookParser):
    # Handles dvemātikāpāḷi (bhikkhu + bhikkhunī pātimokkha) and
    # kaṅkhāvitaraṇī-aṭṭhakathā (commentary on both).
    #
    # Pātimokkha structure:
    #   book "Dvemātikāpāḷi"
    #     chapter "Bhikkhupātimokkhapāḷi" / "Bhikkhunīpātimokkhapāḷi"
    #       subhead = uddesa (Pārājikuddeso, Saṅghādisesuddeso, ...)
    #         centre/bodytext ending "sikkhāpadaṃ" = rule name
    #
    # Commentary structure:
    #   chapter "Kaṅkhāvitaraṇī-aṭṭhakathā"  (transition marker)
    #     subsubhead "Ganthārambhakathā"
    #     chapter = kaṇḍa (Pārājikakaṇḍo, ...)
    #       title = vagga (1. Cīvaravaggo, Sādhāraṇapārājikaṃ, ...)
    #       subhead = sikkhāpada commentary entry
    #   chapter "Bhikkhunīpātimokkhavaṇṇanā"  (bhikkhunī flip)
    #     chapter = kaṇḍa ...

    books = ("kva",)

    def update(self, x: element.Tag) -> None:
        text = x.get_text().strip()
        rend = x["rend"]

        if not self.is_api:
            # === PĀTIMOKKHA (mātikā) mode ===

            if rend == "chapter":
                if "Bhikkhupātimokkhapāḷi" in text:
                    self.is_bhikkhuni = False
                    self.section_counter = 0
                    self.section = "bhikkhupātimokkha"
                    self.vagga_counter = 0
                    self.source = "KVA1.1"
                    self.sutta = "bhikkhupātimokkha"

                elif "Bhikkhunīpātimokkhapāḷi" in text:
                    self.is_bhikkhuni = True
                    self.section_counter = 0
                    self.section = "bhikkhunīpātimokkha"
                    self.vagga_counter = 0
                    self.source = "KVA1.2"
                    self.sutta = "bhikkhunīpātimokkha"

                elif "Kaṅkhāvitaraṇī-aṭṭhakathā" in text:
                    self.is_api = True
                    self.is_bhikkhuni = False
                    self.section_counter = 0
                    self.vagga_counter = 0
                    self.section = ""
                    self.vagga = ""
                    self.source = "KVA2"
                    self.sutta = "kaṅkhāvitaraṇī-aṭṭhakathā"

            elif rend == "subhead":
                uddesa = text
                self.section = uddesa.lower()
                self.section_counter += 1
                prefix = "KVA1.1" if not self.is_bhikkhuni else "KVA1.2"
                bhikkhu_label = (
                    "bhikkhupātimokkha"
                    if not self.is_bhikkhuni
                    else "bhikkhunīpātimokkha"
                )
                self.source = f"{prefix}.{self.section_counter}"
                self.sutta = f"{bhikkhu_label}, {uddesa}".lower()

            elif (
                rend in ["centre", "bodytext"]
                and (text.endswith("sikkhāpadaṃ") or text.endswith("sikkhāpadāni"))
                and not re.match(r"^\d", text)
            ):
                bhikkhu_label = (
                    "bhikkhupātimokkha"
                    if not self.is_bhikkhuni
                    else "bhikkhunīpātimokkha"
                )
                self.sutta = f"{bhikkhu_label}, {self.section}, {text}".lower()

        else:
            # === COMMENTARY (kaṅkhāvitaraṇī-aṭṭhakathā) mode ===

            if rend == "subsubhead":
                self.section_counter = 0
                self.section = text.lower()
                self.source = "KVA2.1.0"
                self.sutta = text.lower()

            elif rend == "chapter":
                if "Bhikkhunīpātimokkhavaṇṇanā" in text:
                    self.is_bhikkhuni = True
                    self.section_counter = 0
                    self.vagga_counter = 0
                    self.vagga = ""
                    self.section = "bhikkhunīpātimokkhavaṇṇanā"
                    self.source = "KVA2.2"
                    self.sutta = "bhikkhunīpātimokkhavaṇṇanā"
                else:
                    self.section_counter += 1
                    self.vagga_counter = 0
                    self.vagga = ""
                    self.section = text.lower()
                    prefix = "KVA2.1" if not self.is_bhikkhuni else "KVA2.2"
                    bhikkhu_label = (
                        "bhikkhupātimokkhavaṇṇanā"
                        if not self.is_bhikkhuni
                        else "bhikkhunīpātimokkhavaṇṇanā"
                    )
                    self.source = f"{prefix}.{self.section_counter}"
                    self.sutta = f"{bhikkhu_label}, {self.section}".lower()

            elif rend == "title":
                vagga, vagga_no = get_text_and_number(text)
                if is_int(vagga_no):
                    self.vagga_counter = int(vagga_no)
                else:
                    self.vagga_counter += 1
                self.vagga = vagga.lower()
                prefix = "KVA2.1" if not self.is_bhikkhuni else "KVA2.2"
                bhikkhu_label = (
                    "bhikkhupātimokkhavaṇṇanā"
                    if not self.is_bhikkhuni
                    else "bhikkhunīpātimokkhavaṇṇanā"
                )
                self.source = f"{prefix}.{self.section_counter}.{self.vagga_counter}"
                self.sutta = f"{bhikkhu_label}, {self.section}, {self.vagga}".lower()

            elif rend == "subhead":
                sutta_text, _ = get_text_and_number(text)
                prefix = "KVA2.1" if not self.is_bhikkhuni else "KVA2.2"
                bhikkhu_label = (
                    "bhikkhupātimokkhavaṇṇanā"
                    if not self.is_bhikkhuni
                    else "bhikkhunīpātimokkhavaṇṇanā"
                )
                if self.vagga_counter:
                    self.source = f"{prefix}.{self.section_counter}.{self.vagga_counter}"
                    self.sutta = (
                        f"{bhikkhu_label}, {self.section}, {self.vagga}, {sutta_text}".lower()
                    )
                else:
                    self.source = f"{prefix}.{self.section_counter}"
                    self.sutta = f"{bhikkhu_label}, {self.section}, {sutta_text}".lower()


class VismParser(BookParser):
    # section   <p rend="subsubhead">Nidānādikathā</p>
    # section   <p rend="title">Dukkhaniddesakathā</p>
    # section   <p rend="chapter">1. Sīlaniddeso</p>
    # sutta     <p rend="subhead">Sīlasarūpādikathā</p>

    books = ("vism", "visma")

    def update(self, x: element.Tag) -> None:
        match self.book:
            case "vism":
                book = "VISM"
            case "visma":
                book = "VISMa"

        if x["rend"] in ["subsubhead"]:
            sutta, sutta_no = get_text_and_number(x.text.strip())
            self.source = f"{book}0"
            self.sutta = sutta.lower()

        elif x["rend"] in ["chapter"]:
            section, section_no = get_text_and_number(x.text.strip())
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

            self.sutta_counter = 0

        elif x["rend"] in ["subhead"]:
            sutta, sutta_no = get_text_and_number(x.text.strip())
            self.sutta_counter += 1
            self.source = self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = f"{self.section}, {sutta}".lower()


class ApParser(BookParser):
    # vagga         <p rend="subhead">Buddhappaṇāmo</p>
    # kaṇḍa         <p rend="chapter">1. Saggakaṇḍa</p>
    # vagga         <p rend="title">1. Bhūmivagga</p>

    books = ("ap",)

    def update(self, x: element.Tag) -> None:
        book = "APP"

        if x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.section = ""
            self.section_counter = "0"
            self.sutta_counter += 1
            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

        elif x["rend"] == "title":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no
            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = sutta.lower()


class AptParser(BookParser):
    # sutta     <p rend="subsubhead">Ganthārambha</p>
    # sutta     <p rend="subhead">Paṇāmādivaṇṇanā</p>
    # kaṇḍa     <p rend="chapter">1. Saggakaṇḍavaṇṇanā</p>
    # sutta     <p rend="title">2<hi rend="dot">.</hi> Puravaggavaṇṇanā</p>
    # sutta     <p rend="subhead">Nigamanavaṇṇanā</p>

    books = ("apt",)

    def update(self, x: element.Tag) -> None:
        book = "APt"

        book = "AP"

        if x["rend"] == "subsubhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.section = ""
            self.section_counter = "0"
            self.sutta_counter = 0
            self.source = f"{book}"
            self.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text)
            self.section = ""
            if x.text == "Paṇāmādivaṇṇanā":
                self.source = f"{book}0"
            else:
                self.source = f"{book}"
            self.sutta = sutta.lower()

        elif x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text)
            self.section = section
            self.section_counter = section_no
            self.source = f"{book}{self.section_counter}"
            self.sutta = section.lower()

        elif x["rend"] == "title":
            sutta, sutta_no = get_text_and_number(x.text)
            self.sutta_counter = sutta_no
            self.source = f"{book}{self.section_counter}.{self.sutta_counter}"
            self.sutta = sutta.lower()
