import re
import time

from bs4 import BeautifulSoup
from rich import print
from typing import Tuple, List

from tools.paths import ProjectPaths
from tools.pali_text_files import cst_texts
from tools.tokenizer import split_sentences

"""This code relies completely on tools.pali_text_files."""

sn_peyyalas = [

    # payyalas is a list of tuples of books found in saṃyutta nikāya
    # (samyutta_no, sutta, start_sutta_no, final sutta_no)
    # they all contain multiple suttas which mess up the 
    # sequential numbering system and need to be handled individually

    # sn2
    (12, "2-11. Jātisuttādidasakaṃ", 72, 81),
    (12, "2-11. Dutiyasatthusuttādidasakaṃ", 83, 92),
    (12, "2-12. Sikkhāsuttādipeyyālaekādasakaṃ", 93, 103),
    (17, "2-12. Sikkhāsuttādipeyyālaekādasakaṃ", 13, 20),
    (17, "2-12. Sikkhāsuttādipeyyālaekādasakaṃ", 38, 43),
    (18, "2-12. Sikkhāsuttādipeyyālaekādasakaṃ", 12, 20),
    
    # sn3
    (23, "1-11. Mārādisuttaekādasakaṃ", 23, 33),
    (23, "1-11. Mārādisuttaekādasakaṃ", 35, 45),
    (29, "11-20. Aṇḍajadānūpakārasuttadasakaṃ", 11, 20),
    (29, "21-50. Jalābujādidānūpakārasuttattiṃsakaṃ", 21, 50),
    (20, "4-6. Dutiyādidvayakārīsuttattikaṃ", 4, 6),
    (20, "7-16. Aṇḍajadānūpakārasuttadasakaṃ", 11, 20),
    (20, "17-46. Jalābujādidānūpakārasuttatiṃsakaṃ", 17, 46),
    (31, "4-12. Sāragandhādidātāsuttanavakaṃ", 4, 12),
    (31, "13-22. Mūlagandhadānūpakārasuttadasakaṃ", 13, 22),
    (31, "23-112. Sāragandhādidānūpakārasuttanavutikaṃ", 23, 112),
    (32, "3-12. Sītavalāhakadānūpakārasuttadasakaṃ", 3, 12),
    (32, "13-52. Uṇhavalāhakadānūpakārasuttacālīsakaṃ", 13, 52),
    (33, "6-10. Rūpaadassanādisuttapañcakaṃ", 6, 10),
    (33, "11-15. Rūpaanabhisamayādisuttapañcakaṃ", 11, 15),
    (33, "16-20. Rūpaananubodhādisuttapañcakaṃ", 16, 20),
    (33, "21-25. Rūpaappaṭivedhādisuttapañcakaṃ", 21, 25),
    (33, "26-30. Rūpaasallakkhaṇādisuttapañcakaṃ", 26, 30),
    (33, "31-35. Rūpaanupalakkhaṇādisuttapañcakaṃ", 31, 35),
    (33, "36-40. Rūpaappaccupalakkhaṇādisuttapañcakaṃ", 36, 40),
    (33, "41-45. Rūpaasamapekkhaṇādisuttapañcakaṃ", 41, 45),
    (33, "46-50. Rūpaappaccupekkhaṇādisuttapañcakaṃ", 46, 50),
    (33, "51-54. Rūpaappaccakkhakammādisuttacatukkaṃ", 51, 55),    
    (34, "20-27. Ṭhitimūlakavuṭṭhānasuttādiaṭṭhakaṃ", 20, 27),
    (34, "28-34. Vuṭṭhānamūlakakallitasuttādisattakaṃ", 28, 34),
    (34, "35-40. Kallitamūlakaārammaṇasuttādichakkaṃ", 35, 40),
    (34, "41-45. Ārammaṇamūlakagocarasuttādipañcakaṃ", 41, 45),
    (34, "46-49. Gocaramūlakaabhinīhārasuttādicatukkaṃ", 46, 49),
    (34, "50-52. Abhinīhāramūlakasakkaccasuttāditikaṃ", 50, 52),
    (34, "53-54. Sakkaccamūlakasātaccakārīsuttādidukaṃ", 53, 54),
    
    # sn4
    (35, "1-10. Jātidhammādisuttadasakaṃ", 33, 42),
    (35, "1-9. Aniccādisuttanavakaṃ", 43, 51),
    (35, "4-6. Dukkhachandādisuttaṃ", 171, 173),
    (35, "7-9. Anattachandādisuttaṃ", 174, 176),
    (35, "10-12. Bāhirāniccachandādisuttaṃ", 177, 179),
    (35, "13-15. Bāhiradukkhachandādisuttaṃ", 180, 182),
    (35, "16-18. Bāhirānattachandādisuttaṃ", 183, 185),
    (35, "22-24. Ajjhattātītādidukkhasuttaṃ", 189, 191),
    (35, "25-27. Ajjhattātītādianattasuttaṃ", 192, 194),
    (35, "28-30. Bāhirātītādianiccasuttaṃ", 195, 197),
    (35, "31-33. Bāhirātītādidukkhasuttaṃ", 198, 200),
    (35, "34-36. Bāhirātītādianattasuttaṃ", 201, 203),
    (35, "40-42. Ajjhattātītādiyaṃdukkhasuttaṃ", 207, 209),
    (35, "43-45. Ajjhattātītādiyadanattasuttaṃ", 210, 212),
    (35, "46-48. Bāhirātītādiyadaniccasuttaṃ", 213, 215),
    (35, "49-51. Bāhirātītādiyaṃdukkhasuttaṃ", 216, 218),
    (35, "52-54. Bāhirātītādiyadanattasuttaṃ", 219, 221),
    (43, "3-32. Anāsavādisuttaṃ", 14, 43),
    
    # sn5
    (45, "2-7. Saṃyojanappahānādisuttachakkaṃ", 42, 47),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 50, 54),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 57, 61),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 64, 68),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 71, 75),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 78, 82),
    (45, "2-6. Sīlasampadādisuttapañcakaṃ", 85, 89),
    (45, "2-5. Dutiyādipācīnaninnasuttacatukkaṃ", 92, 95),
    (45, "2-6. Dutiyādisamuddaninnasuttapañcakaṃ", 98, 102),
    (45, "2-6. Dutiyādipācīnaninnasuttapañcakaṃ", 104, 108),
    (45, "2-6. Dutiyādisamuddaninnasuttapañcakaṃ", 110, 114),
    (45, "2-6. Dutiyādipācīnaninnasuttapañcakaṃ", 116, 120),
    (45, "2-6. Dutiyādisamuddaninnasuttapañcakaṃ", 122, 126),
    (45, "2-6. Dutiyādipācīnaninnasuttapañcakaṃ", 128, 132),
    (45, "2-6. Dutiyādisamuddaninnasuttapañcakaṃ", 134, 138),
    (45, "3-7. Kūṭādisuttapañcakaṃ", 141, 145),
    (45, "8-10. Candimādisuttatatiyakaṃ", 146, 148),
    (46, "1-12. Gaṅgānadīādisuttaṃ", 77, 88),
    (46, "1-10. Tathāgatādisuttaṃ", 89, 98),
    (46, "1-12. Balādisuttaṃ", 99, 110),
    (46, "1-10. Esanādisuttaṃ", 111, 120),
    (46, "1-8. Oghādisuttaṃ", 121, 128),
    (47, "1-12. Gaṅgānadīādisuttadvādasakaṃ", 51, 62),
    (47, "1-10. Tathāgatādisuttadasakaṃ", 63, 72),
    (47, "1-12. Balādisuttadvādasakaṃ", 73, 84),
    (47, "1-10. Esanādisuttadasakaṃ", 85, 94),
    (47, "1-10. Uddhambhāgiyādisuttadasakaṃ", 95, 104),
    (48, "1-12. Pācīnādisuttadvādasakaṃ", 71, 82),
    (48, "1-10. Oghādisuttadasakaṃ", 83, 92),
    (48, "1-12. Pācīnādisuttadvādasakaṃ", 93, 104),
    (48, "1-10. Oghādisuttadasakaṃ", 105, 114),
    (49, "1-12. Pācīnādisuttadvādasakaṃ", 1, 12),
    (49, "1-12. Balakaraṇīyādisuttadvādasakaṃ", 14, 25),
    (49, "1-10. Esanādisuttadasakaṃ", 26, 35),
    (49, "1-10. Oghādisuttadasakaṃ", 36, 35),
    (50, "1-12. Balādisuttadvādasakaṃ", 1, 12),
    (50, "1-10. Oghādisuttadasakaṃ", 14, 23),
    (50, "1-12. Pācīnādisuttadvādasakaṃ", 24, 35),
    (50, "1-12. Esanādisuttadvādasakaṃ", 36, 47),
    (50, "1-10. Oghādisuttadasakaṃ", 48, 57),
    (51, "1-12. Gaṅgānadīādisuttadvādasakaṃ", 33, 44),
    (51, "1-10. Oghādisuttadasakaṃ", 45, 54),
    (53, "1-12. Jhānādisuttadvādasakaṃ", 1, 12),
    (53, "1-10. Oghādisuttaṃ", 13, 22),
    (56, "6-11. Chedanādisuttaṃ", 96, 101),
    (56, "4-5-6. Manussacutidevanirayādisuttaṃ", 105, 107),
    (56, "7-9. Devacutinirayādisuttaṃ", 108, 110),
    (56, "10-12. Devamanussanirayādisuttaṃ", 111, 113),
    (56, "13-15. Nirayamanussanirayādisuttaṃ", 114, 116),
    (56, "16-18. Nirayadevanirayādisuttaṃ", 117, 119),
    (56, "19-21. Tiracchānamanussanirayādisuttaṃ", 120, 122),
    (56, "22-24. Tiracchānadevanirayādisuttaṃ", 123, 125),
    (56, "25-27. Pettimanussanirayādisuttaṃ", 126, 128),
    (56, "28-29. Pettidevanirayādisuttaṃ", 129, 130),
]


def get_cst_filenames(books: list[str] | str)-> list[str]:
    """Take a single book OR a list of books 
    and return the relevant filenames."""

    filenames: list[str] = []
    
    if type(books) is list:
        for book in books:
            if book in cst_texts:
                filenames.extend(cst_texts[book])
    
    elif type(books) is str:
        if books in cst_texts:
                filenames.extend(cst_texts[books])

    return filenames


class GlobalData():

    def __init__(
        self, book: str, text_to_find: str
    )-> None:
        self.debug: bool = True
        self.pth = ProjectPaths()
        
        self.book: str = book
        self.text_to_find: str = text_to_find
        self.source_sutta_examples: list[tuple[str, str, str]] = []
        self.filenames: list[str] = get_cst_filenames(self.book)
        self.soups: list[BeautifulSoup] = self.make_cst_soup(self.filenames)
        self.x = None # current soup item
        
        self.source: str = ""
        self.source_alt: str = ""
        
        self.sutta: str = ""
        self.sutta_counter: int = self.init_sutta_counter()
        self.sutta_counter_alt: int = 0      
        
        self.example: str = ""

        self.samyutta: str = ""
        self.samyutta_counter: int = self.init_samyutta_counter()
        self.anguttara_counter: int = 0
        self.vin_book: str
        
        self.section = ""
        self.section_counter: int = 0
        
        self.vagga: str = ""
        self.vagga_counter: int = 0
        self.vagga_alt_counter: int = 0

        self.subtitle: str = ""
        self.subtitle_counter: int = 0
        self.subtitlecoutner_alt: int = 0

        self.soup_tag_list = set()
        
        self.text: str = ""
        self.source_sutta_list: list[tuple[str, str]] = []

        self.is_api: bool = False
        self.is_bhikkhuni: bool = False
    
    @property
    def sutta_clean(self):
        return re.sub(",.+", "", self.sutta)

    def make_cst_soup(self, unwrap_notes=True) -> list[BeautifulSoup]:
        """Take a list of filenames and return a list of soups."""
        
        soups: list[BeautifulSoup] = []
        
        for filename in self.filenames:
            filename = filename.replace(".txt", ".xml")

            with open(
                self.pth.cst_xml_roman_dir.joinpath(filename), "r", encoding="UTF-16"
            ) as f:
                xml = f.read()

            soup = BeautifulSoup(xml, "xml")

            # remove all the "pb" tags
            pbs = soup.find_all("pb")
            for pb in pbs:
                pb.decompose()

            if unwrap_notes:
                # unwrap all the notes (variant readings)
                notes = soup.find_all("note")
                for note in notes:
                    note.replace_with(fr" [{note.text}] ")

            # unwrap all the hi parunum dot tags (paragraphy numbers)
            his = soup.find_all("hi", rend=["paranum", "dot"])
            for hi in his:
                hi.unwrap()

            soups.append(soup)
        
        return soups
    

    def init_sutta_counter(self) -> int:
        """Initialize the sutta counter depending on the book."""
        match self.book:   
            case "dn2":
                return 13
            case "dn3":
                return 23
            case "mn2":
                return 50
            case "mn3":
                 return 100
            case "kn11":
                return 422
            case _:
                return 0

    
    def init_samyutta_counter(self):
        match self.book:
            case "sn2":
                return 11
            case "sn3":
                return 21
            case "sn4":
                return 34
            case "sn5":
                return 44
            case _:
                return 0


def find_gatha_example(g: GlobalData):
    """Find an example in a gāthā."""
    
    x = g.x
    example = ""

    start_time = time.time()
    while True:
        if x.text == "\n":
            x = x.previous_sibling
        elif x["rend"] == "gatha1":
            break
        elif x["rend"] == "gatha2":
            x = x.previous_sibling
        elif x["rend"] == "gatha3":
            x = x.previous_sibling
        elif x["rend"] == "gathalast":
            x = x.previous_sibling
        if time.time() - start_time > 1:
            print(f"[bright_red]{g.text_to_find} [red]is stuck in a loop")
            break

    text = clean_gatha(x.text)
    example += text

    while True:
        try:
            if x is not None:
                x = x.next_sibling
                if x.text == "\n":
                    pass
                elif x["rend"] == "gatha2":
                    text = clean_gatha(x.text)
                    text = text.replace(".", ",")
                    example += text
                elif x["rend"] == "gatha3":
                    text = clean_gatha(x.text)
                    text = text.replace(".", ",")
                    example += text
                elif x["rend"] == "gathalast":
                    text = clean_gatha(x.text)
                    text = re.sub(",$", ".", text)
                    example += text
                    break
            else:
                break
        except AttributeError as e:
            print(f"[red]{e}")
            print(g.text_to_find)
            print(x)
            break
    
    if example:
        g.example = example


def find_sentence_example(g: GlobalData): 
    sentences = split_sentences(g.text)
    for i, sentence in enumerate(sentences):
        if re.findall(g.text_to_find, sentence):
            prev_sentence = sentences[i - 1] if i > 0 else ""
            next_sentence = sentences[i + 1] if i < len(sentences)-1 else ""
            example = f"{prev_sentence}{sentence}{next_sentence}"
    
    if example:
        g.example = example


def get_text_and_number(text: str):
    """
    '2. Appamādavaggo' > ('Appamādavaggo', 2)
    """
    clean = re.sub(r"^\d.*\. *", "", text)
    clean_no = re.sub(r"\. .+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets1(text: str):
    """
    '(1) Mahāvaggo' > ('Mahāvaggo', 1)
    """
    clean = re.sub(r"^\(\d*\) *", "", text)
    clean_no = re.sub(r"\(|\).+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets2(text: str):
    """
    '(7) 2. Sukhavaggo' > ('Sukhavaggo', 2)
    """
    text = re.sub(r"^\(\d*\)\.* *", "", text)
    clean, clean_no = get_text_and_number(text)
    return clean, clean_no


def get_text_and_number_with_brackets3(text: str):
    """
    '(12) 3. Kaṅkhākathā' > ('Kaṅkhākathā', 12)
    """
    clean = re.sub(r"^.+\. ", "", text)
    clean_no = re.sub(r"\(|\).+", "", text)
    return clean, clean_no


def get_text_and_number_with_brackets_end(text: str):
    """
    '153. Sūkarajātakaṃ (2-1-3)' > ('Sūkarajātakaṃ', 153)
    """
    text = re.sub(r" \(\d.*\)", "", text)
    clean, clean_no = get_text_and_number(text)
    return clean, clean_no

def get_text_and_number_with_brackets_abhidhamma(text: str):
    """
    '(26. Ka) dovacassatā' > ('dovacassatā', 26)

    """
    clean = re.sub(r"^\(.*\) *", "", text)
    clean_no = re.sub(r"\(|[^0-9]|\).+", "", text)
    return clean, clean_no

def get_text_and_number_ana(text: str):
    sutta = re.sub(r"^.+\. ", "", text)
    sutta_no = re.sub(r"^\(|\).+|\..+", "", text)
    return sutta, sutta_no


def get_text_and_number_with_sqaure_brackets(text: str):
    """
    '[111] 1. Gadrabhapañhajātakavaṇṇanā' > ('Gadrabhapañhajātakavaṇṇanā', 111)
    """
    sutta = re.sub(r".+\. ", "", text)
    sutta_no = re.sub(r"\[|\].+", "", text)
    return sutta, sutta_no


def clean_subtitle(text: str):
    """
    '(7-8) Karacaraṇamudujālatālakkhaṇāni' > 
    'Karacaraṇamudujālatālakkhaṇāni'
    """
    return re.sub(r"\(.*\) ", "", text)


def clean_example(text):
    text = text.strip()
    text = text.lower()
    text = text.replace("‘", "")
    text = text.replace(" – ", ", ")
    text = text.replace("’", "")
    text = text.replace("…pe॰…", " … ")
    text = text.replace("…pe…", " … ")
    text = text.replace(";", ",")
    text = text.replace("  ", " ")
    text = text.replace("..", ".")
    text = text.replace(" ,", ",")
    
    # remove abbreviations in brackets, no more than 20 characters
    text = re.sub(r" \([^)]{0,20}\.\)", "", text)
    
    return text


def clean_gatha(text):
    text = clean_example(text)
    text = text.strip()
    text = text.replace(" ,", ",")
    text = text.replace(" .", ".")
    text = text.replace(", ", ",\n")
    text = re.sub(",$", ",\n", text)
    return text


def assert_type_int(text):
    try:
        int(text)
        return text
    except (ValueError, TypeError):
        return ""


def is_int(text):
    try:
        if isinstance(int(text), int):
            return True
        else:
            return False
    except:
        return False


def assert_no_space(sutta_name: str):
    try:
        assert " " not in sutta_name
        return sutta_name
    except (TypeError, AssertionError):
        return ""


def split_sutta_number(text: str):
    """1-4 > (1, 4, 4)"""
    start = int(re.sub("-.*", "", text))
    end = int(re.sub(r"^\d*-|\.*", "", text))
    return start, end, end - start + 1


def vin1_parajika(g:GlobalData):
    # there are four subdivisions
    # 1. chapter of rules = pārājika, saṅghādisesa, aniyata, nissaggiya, etc. 
    # 2. vagga: in some cases, if more than 13 rules
    # 3. rule: name of the rule
    # 4. subhead: subsection of the rule
    # and corresponding chapter, vagga and title numbers

    book = "VIN1"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        if section == "Verañjakaṇḍaṃ":
            section_no = "0"
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}.{section_no}"
        g.sutta = section.lower()

        g.vagga = ""
        g.vagga_counter = 0

    elif x["rend"] == "title" and "vaggo" in x.text:
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}.{g.section_counter}.{vagga_no}"
        g.sutta = f"{g.section}, {vagga}".lower()

    elif x["rend"] == "title" and "vaggo" not in x.text:
        sutta, sutta_no = get_text_and_number(x.text)
        if g.vagga:
            g.source = g.source = f"{book}.{g.section_counter}.{g.vagga_counter}.{sutta_no}"
        else:
            g.source = g.source = f"{book}.{g.section_counter}.{sutta_no}"
        g.sutta = sutta.lower()
        g.sutta_counter = sutta_no

    elif x["rend"] == "subhead":
        subtitle, subtitle_no = get_text_and_number(x.text)
        g.sutta = f"{g.sutta_clean}, {subtitle}".lower()
    

def vin2_pacittiya(g: GlobalData):

    x = g.x

    if (        
        # this switches is_bhikkhuni to True at the start of the Bhikkhunīvibhaṅgo
        # because bhikkhuni vinaya has its own logical sequence 
        not g.is_bhikkhuni
        and x["rend"] == "book"
        and x.text == "Bhikkhunīvibhaṅgo"
    ):
        g.is_bhikkhuni = True
        g.source = ""
        g.sutta = ""
        
    if not g.is_bhikkhuni:
        book = "VIN2"

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text.strip())
            g.section = section
            g.section_counter = section_no
            g.source = f"{book}.{section_no}"
            g.sutta = section.lower()
            g.vagga = ""
            g.vagga_counter = 0
        

        elif x["rend"] == "title" and "vaggo" in x.text:
            vagga, vagga_no = get_text_and_number(x.text.strip())
            g.vagga = vagga
            g.vagga_counter = vagga_no
            g.source = f"{book}.{g.section_counter}.{vagga_no}"
            g.sutta = f"{g.section}, {vagga}".lower()
            
        elif x["rend"] == "title" and "vaggo" not in x.text:
            sutta, sutta_no = get_text_and_number(x.text.strip())
            if g.vagga:
                g.source = f"{book}.{g.section_counter}.{g.vagga_counter}.{sutta_no}"
            else:
                g.source = f"{book}.{g.section_counter}.{sutta_no}"
            g.sutta = sutta.lower()

        elif x["rend"] == "subhead":
            sutta, sutta_no = get_text_and_number(x.text.strip())
            if g.vagga:
                g.source = f"{book}.{g.section_counter}.{g.vagga_counter}.{sutta_no}"
            else:
                g.source = f"{book}.{g.section_counter}.{sutta_no}"
            g.sutta = sutta.lower()

    # bhikkhuni vinaya
    elif g.is_bhikkhuni:
        book = "BHI VIN"

        def bhikkhuni_cleaner(text):
            return text.replace(" (bhikkhunīvibhaṅgo)", "")

        if x["rend"] == "chapter":
            section, section_no = get_text_and_number(x.text.strip())
            section = bhikkhuni_cleaner(section)
            g.section = section
            g.section_counter = section_no
            g.source = f"{book}{section_no}"
            g.sutta = section.lower()

            g.vagga = ""
            g.vagga_counter = 0
        

        elif x["rend"] == "title" and "vaggo" in x.text:
            vagga, vagga_no = get_text_and_number(x.text.strip())
            g.vagga = vagga
            g.vagga_counter = vagga_no
            g.source = f"{book}.{g.section_counter}.{g.vagga_counter}"
            g.sutta = f"{g.section}, {vagga}".lower()

        elif x["rend"] == "subhead" and "vaggo" not in x.text: # there's only one exception "1. Pattavaggo"
            sutta, sutta_no = get_text_and_number(x.text.strip())
            if g.vagga:
                g.source = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
            else:
                g.source = f"{book}{g.section_counter}.{sutta_no}"

            if g.vagga:
                g.sutta = f"{g.vagga}, {sutta}".lower()
            else:
                if int(g.section_counter) == 3:   # only for nissaggiyakaṇḍaṃ
                    g.sutta = f"{g.section}, {sutta}".lower()
                else:
                    g.sutta = f"{sutta}".lower()


def vin3_vin4_maha_culavagga(g: GlobalData):
    # <head rend="chapter">1. Mahākhandhako</head>
    # <p rend="subhead">1. Bodhikathā</p>
    
    if g.book == "vin3":
        book = "VIN3"
    elif g.book == "vin4":
        book = "VIN4"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text.strip())
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}.{g.section_counter}"
        g.sutta = f"{section}".lower()
    
    
    elif x["rend"] == "subhead": 
        if re.findall(r"^\d", x.text):
            sutta, sutta_mo = get_text_and_number(x.text.strip())
            if sutta.lower() not in [
                "soṇassa pabbajjā", "abhiññātānaṃ pabbajjā" # these are bad subheads
            ]: 
                g.sutta_counter = sutta_mo
                g.source = f"{book}.{g.section_counter}.{sutta_mo}"
                g.sutta = f"{g.section}, {sutta}".lower()
        # else:
        #     subtitle, _ = get_text_and_number(x.text.strip())
        #     g.source = f"{book}.{g.section_counter}.{g.sutta_counter}"
        #     g.sutta = f"{g.sutta_clean}, {subtitle}".lower()


def dn_digha_nikaya(g: GlobalData):
    # sutta     <head rend="chapter">1. Brahmajālasuttaṃ</head>
    # subtitle  <p rend="subhead">Paribbājakakathā</p>
    
    x = g.x
    book = "DN"

    if x["rend"] == "chapter":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "subhead":
        subtitle = clean_subtitle(x.text)
        g.sutta = f"{g.sutta_clean}, {subtitle}".lower()


def mn_majjhima_nikaya(g: GlobalData):
    # vagga     <head rend="chapter">1. Mūlapariyāyavaggo</head>
    # sutta     <p rend="subhead">1. Mūlapariyāyasuttaṃ</p>
    
    x = g.x
    book = "MN"

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif x["rend"] == "subhead":
        if re.findall(r"^\d", x.text):
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.source = f"{book}{g.sutta_counter}"
            g.source_alt = f"{g.book.upper()}.{g.vagga_counter}.{sutta_no}"
            g.sutta = sutta.lower()
        else:
            subtitle = x.text
            g.sutta = f"{g.sutta_clean}, {subtitle}".lower()


def sn_samyutta_nikaya(g: GlobalData):

# main_vagga    <head rend="book">Sagāthāvaggo</head>
# samyutta      <head rend="chapter">1. Devatāsaṃyuttaṃ</head>
# vagga         <p rend="title">1. Naḷavaggo</p>
# sutta         <p rend="subhead">1. Oghataraṇasuttaṃ</p>

    x = g.x
    sutta_name: str = ""
    book = "SN"

    if x["rend"] == "chapter":
        g.samyutta, _ = get_text_and_number(x.text)
        g.samyutta_counter += 1
        g.sutta = ""
        g.sutta_counter = 0
        g.vagga = ""
        g.vagga_counter = 0

    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif (
        x["rend"] == "subhead"
        and re.findall(r"^\d", x.text)
        and "-" not in x.text   # a "-" in the sutta means it contains multiple suttas
    ):
        sutta_name, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        sutta_counter_special = ""

    # deal with peyyāla suttas individually
    elif (
        x["rend"] == "subhead"
        and "-" in x.text                           # a "-" in the sutta means it contains multiple suttas
    ):
        for peyyala in  sn_peyyalas:
            p_samyutta_counter, p_sutta_name, p_start, p_end = peyyala
            if (
                p_samyutta_counter == g.samyutta_counter
                and x.text == p_sutta_name
                and g.sutta_counter == p_start-1
            ):
                sutta_name = re.sub(r"^\d.*\. ", "", x.text)
                sutta_counter_special = f"{p_start}-{p_end}"
                g.sutta_counter = p_end
                break
                
    if sutta_name:
        if sutta_counter_special:
            g.source = f"{book}{g.samyutta_counter}.{sutta_counter_special}"
        else:
            g.source = f"{book}{g.samyutta_counter}.{g.sutta_counter}"        
        g.sutta = f"{g.samyutta}, {sutta_name}".lower()


def an_anguttara_nikaya(g: GlobalData):
    # vagga     <head rend="chapter">1. Rūpādivaggo</head>
    # subtitle  <p rend="subhead">1. Paṭhamavaggo</p>

    book_name = g.book.upper()

    x = g.x
    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number_with_brackets2(x.text)
        g.sutta = vagga.lower()
        g.vagga = vagga.lower()
        g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":
        subtitle, sutta_no = get_text_and_number(x.text)
        g.sutta = f"{g.sutta_clean}, {subtitle}".lower()
        g.sutta_counter = sutta_no
    
    elif (
        x["rend"] == "bodytext"
        and x.has_attr("n")
    ):
        g.sutta_counter = x["n"]
        g.source = f"{book_name}.{g.sutta_counter}"
        # g.source_alt = f"{book_name}.{g.vagga_counter}.{g.sutta_counter}"


def kn1_khuddakapāṭha(g: GlobalData):
    # sutta   <head rend="chapter">1. Saraṇattayaṃ</head>

    x = g.x
    if x["rend"] == "chapter":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"KP{sutta_no}"
        g.sutta = sutta.lower()


def kn2_dhammpada(g: GlobalData):
    # vagga         <head rend="chapter">1. Yamakavaggo</head>
    # sutta no      <p rend="hangnum" n="1"><hi rend="paranum">1</hi><hi rend="dot">.</hi></p>

    x = g.x
    book = "DHP"

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.sutta = f"{vagga}".lower()
        g.vagga_counter = vagga_no
        g.section_counter = 0
    
    elif x["rend"] == "hangnum":
        g.sutta_counter += 1
        g.section_counter +=1
        g.source = f"{book}{g.sutta_counter}"
        g.source_alt = f"{book}{g.vagga_counter}.{g.section_counter}"


def kn3_udana(g:GlobalData):
    # vagga     <head rend="chapter">1. Bodhivaggo</head>
    # sutta     <p rend="subhead">1. Paṭhamabodhisuttaṃ</p>

    book = "UD"

    x = g.x
    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter +=1
        g.source = f"{book}{g.sutta_counter}"
        g.source_alt = f"{book}{g.vagga_counter}.{sutta_no}"
        g.sutta = sutta.lower()


def kn4_itivuttaka(g:GlobalData):
    # section   <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Lobhasuttaṃ</p>

    book = "ITI"
    x = g.x

    if x["rend"] == "chapter":
        section, g.section_counter = get_text_and_number(x.text)
        g.section = section
        g.section_counter = g.section_counter
        g.vagga = ""
        g.vagga_counter = 0
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter +=1
        g.source = f"{book}{g.sutta_counter}"
        if g.vagga_counter:
            g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
        else:
            g.source_alt = f"{book}{g.section_counter}.{sutta_no}"
        g.sutta = sutta.lower()


def kn5_suttanipata(g: GlobalData):
    # vagga <head rend="chapter">1. Uragavaggo</head>
    # sutta <p rend="subhead">1. Uragasuttaṃ</p>

    book = "SNP"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    if x["rend"] == "subhead":
        
        if x.text in ["Vatthugāthā", "Pārāyanatthutigāthā", "Pārāyanānugītigāthā"]:
            if x.text == "Vatthugāthā":
                sutta_no = 0
            elif x.text == "Pārāyanatthutigāthā":
                sutta_no = 17
            elif x.text == "Pārāyanānugītigāthā":
                sutta_no = 18
            sutta, _ = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.source = f"{book}{g.sutta_counter}"
            g.source_alt = f"{book}{g.vagga_counter}.{sutta_no}"
            g.sutta = f"{g.vagga}, {sutta}".lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.source = f"{book}{g.sutta_counter}"
            g.source_alt = f"{book}{g.vagga_counter}.{sutta_no}"
            g.sutta = f"{g.vagga}, {sutta}".lower()


def kn6_vimanavatthu(g: GlobalData):
    # <head rend="chapter">1. Itthivimānaṃ</head>
    # <p rend="title">1. Pīṭhavaggo</p>
    # <p rend="subhead">1. Paṭhamapīṭhavimānavatthu</p>

    book = "VV"
    x = g.x

    if x["rend"] == "chapter":
        section, g.section_counter = get_text_and_number(x.text)
        g.section = section
        g.section_counter = g.section_counter
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = f"{g.vagga}, {sutta}".lower()


def kn7_petavatthu(g: GlobalData):
    # <head rend="chapter">1. Uragavaggo</head>
    # <p rend="subhead">1. Khettūpamapetavatthu</p>

    book = "PV"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source_alt = f"{book}{g.vagga_counter}.{sutta_no}"
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = f"{g.vagga}, {sutta}".lower()


def kn8_9_thera_therigatha(g: GlobalData):
    # sutta0    <p rend="subsubhead">Nidānagāthā</p>
    # section    <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Subhūtittheragāthā</p>

    match g.book:
        case "kn8":
            book = "TH"
        case "kn9":
            book = "THI"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}0"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, g.section_counter = get_text_and_number(x.text)
        g.section = section
        g.section_counter = g.section_counter
        g.vagga = ""
        g.vagga_counter = 0
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        sutta_no = sutta_no.replace("-", ".")
        g.sutta_counter += 1
        if g.vagga_counter == 0:
            g.source_alt = f"{book}{g.section_counter}.{sutta_no}"
        else:
            g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = sutta.lower()


def kn10_11_thera_theriapadana(g: GlobalData):
    # sutta0    <p rend="subsubhead">Nidānagāthā</p>
    # section    <head rend="chapter">1. Ekakanipāto</head>
    # vagga     <p rend="title">1. Paṭhamavaggo</p>
    # sutta     <p rend="subhead">1. Subhūtittheragāthā</p>

    x = g.x

    if x["rend"] == "book" and x.text == "Therīapadānapāḷi":
        g.is_api = True
        g.sutta_counter = 0
    
    if g.is_api:
        book = "API"
    else:
        book = "APA"

    if x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}0"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, g.section_counter = get_text_and_number(x.text)
        g.section = section
        g.section_counter = g.section_counter
        g.vagga = ""
        g.vagga_counter = 0
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
    
    if x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        sutta_no = sutta_no.replace("-", ".")
        g.sutta_counter += 1
        if g.vagga_counter == 0:
            g.source_alt = f"{book}{g.section_counter}.{sutta_no}"
        else:
            g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = sutta.lower()


def kn12_buddhavamsa(g: GlobalData):
    # sutta     <head rend="chapter">1. Ratanacaṅkamanakaṇḍaṃ</head>

    book = "BV"
    x = g.x

    if x["rend"] == "chapter":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter +=1
        g.source = f"{book}{sutta_no}"
        g.sutta = sutta.lower()


def kn13_cariyapitaka(g: GlobalData):
    #   <head rend="chapter">1. Akittivaggo</head>
    #   <p rend="subhead">1. Akitticariyā</p>

    book = "CP"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}{g.sutta_counter}"
        g.source_alt = f"{book}{g.vagga_counter}.{sutta_no}"
        g.sutta = sutta.lower()


def kn14_jataka(g: GlobalData):
    # <head rend="chapter">1. Ekakanipāto</head>
    # <p rend="title">1. Apaṇṇakavaggo</p>
    # <p rend="subhead">1. Apaṇṇakajātakaṃ</p>

    book = "JA"
    x = g.x

    if x["rend"] == "chapter":
        section, g.section_counter = get_text_and_number(x.text)
        g.section = section
        g.section_counter = g.section_counter
    
    elif x["rend"] == "title":
        if x.text == "(Dutiyo bhāgo)":
            g.vagga = ""
        else:
            vagga, vagga_no = get_text_and_number(x.text)
            g.vagga = vagga
            g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":
        if re.findall("^\d", x.text.strip()):
            sutta, sutta_no = get_text_and_number_with_brackets_end(x.text.strip())
            g.sutta_counter += 1
            # g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
            g.source = f"{book}{g.sutta_counter}"
            g.sutta = f"{sutta}".lower()
        else:
            subtitle, _ = get_text_and_number_with_brackets_end(x.text.strip())
            g.sutta = f"{g.sutta_clean}, {subtitle}".lower()


def kn15_mahaniddesa(g: GlobalData):
    # <p rend="title">1. Aṭṭhakavaggo</p>
    # <head rend="chapter">1. Kāmasuttaniddeso</head>
    
    book = "NIDD1"
    x = g.x

    if x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    if x["rend"] == "chapter":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}.{g.sutta_counter}"
        g.sutta = f"{sutta}".lower()
    

def kn16_culaniddesa(g: GlobalData):
    # <p rend="subsubhead">Pārāyanavaggo</p>
    # <p rend="subhead">Vatthugāthā</p>
    # <p rend="title">Khaggavisāṇasuttaniddeso</p>
    # <p rend="subhead">Paṭhamavaggo</p>
    # <head rend="chapter">Pārāyanavagganiddeso</head>
    # <p rend="subhead">1. Ajitamāṇavapucchāniddeso</p>

    book = "NIDD2"
    x = g.x

    if (
        x["rend"] == "subsubhead"
        or x["rend"] == "title"
        or x["rend"] == "chapter"
    ):
        if x.text == "Khaggavisāṇasutto":
            pass
        else:
            vagga, vagga_no = get_text_and_number(x.text)
            g.vagga = vagga
            g.vagga_counter += 1
            g.sutta_counter = 0
    
    elif x["rend"] == "subhead":
        if x.text == "Vatthugāthā":
            sutta, _ = get_text_and_number(x.text)
            g.source = f"{book}.{g.vagga_counter}.0"
            g.sutta = sutta.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.source = f"{book}.{g.vagga_counter}.{g.sutta_counter}"
            g.sutta = f"{g.vagga}, {sutta}".lower()


def kn17_patisambhidamagga(g: GlobalData):
    #         # vagga     <head rend="chapter">1. Mahāvaggo</head>
    #         # section   <p rend="title">1. Ñāṇakathā</p>
    #         # sutta     <p rend="subhead">Mātikā</p>
    #         # plus some subheads which needs to be pypassed

    book = "PM"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = assert_type_int(vagga_no)
        
        g.section = ""
        g.section_counter = 0
        g.sutta = ""
        g.sutta_counter = 0
    
    elif x["rend"] == "title":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = assert_type_int(section_no)

        g.source = f"{book}{g.vagga_counter}.{g.section_counter}"
        g.sutta= f"{g.vagga}, {g.section}".lower()
        g.sutta_counter = 0

    elif (
        x["rend"] == "subhead"
        and x.text not in [
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
        ]
    ):
        sutta_name, sutta_no = get_text_and_number(x.text)
    
        if g.vagga and g.section and sutta_name:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}.{sutta_no}"
            g.sutta = f"{g.section}, {sutta_name}".lower()
        elif g.vagga and not g.section and sutta_name:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}"
            g.sutta = f"{g.vagga}, {sutta_name}".lower()
        elif g.vagga and g.section and not sutta_name:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}"
            g.sutta = f"{vagga}, {section}".lower()
    

def kn18_milindapanha(g: GlobalData):            
    #         # section   <p rend="subsubhead">1. Bāhirakathā</p>
    #         # section   <head rend="chapter">2-3. Milindapañho</head>
    #         # vagga     <p rend="title">1. Mahāvaggo</p>
    #         # sutta     <p rend="subhead">1. Paññattipañho</p>
    #         # plus some stray cats which needs to be handled individually

    book = "MIL"
    x = g.x

    if x["rend"] == "chapter":
        if x.text == "Milindapañhapāḷi":
            g.section = "Milindapañhapāḷi"
            g.vagga = "Ārambhakathā"
            g.section_counter += 1
            g.vagga_counter += 1
        else:
            section, _ = get_text_and_number(x.text)
            g.section = section
            g.section_counter += 1
            g.vagga = ""
            g.vagga_counter = 0
            g.sutta = ""
            g.sutta_counter = 0
        g.source = f"{book}{g.section_counter}"
        g.sutta = g.section.lower()
    
    elif x["rend"] == "subsubhead":
        vagga, _ = get_text_and_number(x.text)
        g.vagga_counter += 1
        g.sutta_counter = 0
        g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {vagga}".lower()
    
    elif x["rend"] == "title":
        if x.text == "Meṇḍakapañhārambhakathā":
            g.section = x.text
            g.section_counter += 1
            g.vagga = ""
            g.vagga_counter = 0
            g.sutta_counter = 0
            g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
            g.sutta = g.section.lower()
        else:
            vagga, _ = get_text_and_number(x.text)
            g.vagga = vagga
            g.vagga_counter += 1
            g.sutta_counter = 0
            g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
            g.sutta = f"{g.section}, {vagga}".lower()
    
    elif x["rend"] == "subhead":
        sutta_name, _ = get_text_and_number(x.text)
        g.sutta_counter += 1
        if g.vagga_counter:
            g.source = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter}"            
        else:
            g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = sutta_name.lower()
    
    elif x["rend"] == "nikaya":
        if x.text == "Mātikā":
            vagga = x.text
            g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
            g.sutta = f"{g.section}, {vagga}".lower()

        elif x.text == "Nigamanaṃ":
            g.section_counter += 1
            g.source = f"{book}{g.section_counter}"
            g.sutta = x.text.lower()


def kn19_netti(g: GlobalData):
    # <head rend="chapter">1. Saṅgahavāro</head>
    # <p rend="subhead">Tassānugīti</p>

    book = "NP"
    x = g.x

    if x["rend"] == "chapter":
        vagga, _ = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter += 1
        g.sutta_counter = 0
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()   
    
    elif x["rend"] == "subhead":
        if x.text == "1. Desanāhāravibhaṅgo":
            g.section_counter += 1
        elif x.text == "1. Desanāhārasampāto":
            g.section_counter += 1
            g.sutta_counter = 0
        sutta_name, _ = get_text_and_number(x.text)
        g.sutta_counter += 1
        if g.section_counter > 0:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}.{g.sutta_counter}"            
        else:
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"            
        g.sutta = sutta_name.lower()


def kn20_petakopadesa(g: GlobalData):
    # section   <head rend="chapter">1. Ariyasaccappakāsanapaṭhamabhūmi</head>
    # sutta     <p rend="subhead">Tatthāyaṃ <pb ed="V" n="0.0167" /> uddānagāthā</p>

    book = "PTP"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.sutta_counter = 0
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()
    
    # elif x["rend"] == "subhead":
    #     sutta, sutta_no = get_text_and_number(x.text)
    #     g.sutta_counter += 1
    #     g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
    #     g.sutta = f"{g.section}, {sutta}".lower()
           



def abh1_dhammasangani(g: GlobalData):
    # <p rend="chapter">Mātikā</p>
    # <p rend="chapter">1. Cittuppādakaṇḍaṃ</p>
    # <p rend="title">Kāmāvacarakusalaṃ</p>
    # <p rend="subhead">Padabhājanī</p>
    # <p rend="subhead">1. Tikamātikā</p>

    book = "DHS"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        
        if is_int(section_no):
            g.section_counter = section_no
        else:
            g.section_counter = 0
        
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()

        # reset vagga
        g.vagga = ""
        g.vagga_counter = 0
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter += 1

        g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {g.vagga}".lower()

        g.sutta_counter = 0
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1

        g.source = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter}"
        if not g.vagga:
            g.sutta = f"{g.section}, {sutta}".lower()
        else:
            g.sutta = f"{g.vagga}, {sutta}".lower()


def abh2_vibhanga(g: GlobalData):
    # <p rend="chapter">1. Khandhavibhaṅgo</p>
    # <p rend="title">1. Suttantabhājanīyaṃ</p>
    # <p rend="subhead">1. Rūpakkhandho</p>

    book = "VIBH"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()

        # reset vagga
        g.vagga = ""
        g.vagga_counter = 0

    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter += 1

        g.source = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {g.vagga}".lower()

        g.sutta_counter = 0


    elif x["rend"] == "subhead":
        if "(" in x.text:
            sutta, sutta_no = get_text_and_number_with_brackets_abhidhamma(x.text)
            if re.findall(r"\d", sutta_no):
                g.sutta_counter = sutta_no
                g.source = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter}"
                g.sutta = f"{g.section}, {g.vagga}, {sutta}".lower()
            else:
                g.sutta = f"{g.section}, {g.vagga}, {sutta}".lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1

            g.source = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter}"
            if not g.vagga:
                g.sutta = f"xxxxxxx, {sutta}".lower()
            else:
                g.sutta = f"{g.section}, {g.vagga}, {sutta}".lower()

# TODO abhidhamma books


def abh3_dhatukatha(g: GlobalData):
    # <p rend="chapter">Uddeso</p>
    # <p rend="subhead">1. Nayamātikā</p>
    # <p rend="chapter">1. Paṭhamanayo</p>
    # <p rend="title">1. Saṅgahāsaṅgahapadaniddeso</p>
    # <p rend="subhead">1. Khandho</p>
    # <p rend="subhead">2. Āyatanaṃ</p>

    book = "DHK"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        if is_int(section_no):
            g.section_counter = section_no
        else:
            g.section_counter = 0
        
        g.source = f"{book}{g.section_counter}"
        g.sutta = f"{g.section}".lower()
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = f"{g.vagga}".lower()

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter = sutta_no
        
        g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        if g.section_counter == 0:
            g.sutta = f"{g.section}, {sutta}".lower()
        else:
            g.sutta = f"{g.vagga}, {sutta}".lower()


def abh4_puggalapannati(g: GlobalData):
    # <p rend="chapter">Mātikā</p>
    # <p rend="subhead">1. Ekakauddeso</p>

    book = "PP"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)

        g.section = section
        g.section_counter += 1 
        
        g.source = f"{book}{g.section_counter}"
        g.sutta = f"{g.section}".lower()

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter = sutta_no
        
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = f"{g.section}, {sutta}".lower()


def abh5_kathavatthu(g: GlobalData):
    # <p rend="chapter">1. Puggalakathā</p>
    # <p rend="title">1. Suddhasaccikaṭṭho</p>
    # <p rend="subhead">1. Anulomapaccanīkaṃ</p>

    book = "KV"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        
        if g.section_counter < 9:
            g.section_counter = int(section_no)
            g.source = f"{book}{g.section_counter}"
            g.sutta = f"{g.section}".lower()
    
    elif x["rend"] == "title":
        if x.text == "2. Dutiyavaggo":
            g.section_counter = 10


    if x["rend"] == "subhead":
        if g.section_counter >= 9:
            section, section_no = get_text_and_number_with_brackets3(x.text)
            g.section = section
            g.section_counter_alt = section_no

            g.source = f"{book}{g.section_counter_alt}"
            g.sutta = f"{g.section}".lower()


def abh6_yamaka(g: GlobalData):
    pass


def abh7_patthana(g: GlobalData):
    pass


def vina_commentary(g: GlobalData):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # section   <p rend="chapter">Verañjakaṇḍavaṇṇanā</p>
    # section   <p rend="chapter">4. Nissaggiyakaṇḍaṃ</p>
    # vagga     <p rend="title">1. Paṭhamapārājikaṃ</p>
    # vagga     <p rend="title">1. Cīvaravaggo</p>
    # <p rend="subhead">Sudinnabhāṇavāravaṇṇanā</p>

    # book = "VINa"
    x = g.x

    if x["rend"] == "book":
        if x.text == "Pārājikakaṇḍa-aṭṭhakathā (paṭhamo bhāgo)":
            g.vin_book = "VINa1"
        elif x.text == "Pācittiya-aṭṭhakathā":
            g.vin_book = "VINa2"
        elif x.text == "Bhikkhunīvibhaṅgavaṇṇanā":
            g.vin_book = "BHI VINa"
            g.section_counter = 0
        elif x.text == "Mahāvagga-aṭṭhakathā":
            g.vin_book = "VINa3"
            g.section_counter = 0
        elif x.text == "Cūḷavagga-aṭṭhakathā":
            g.vin_book = "VINa4"
            g.section_counter = 0
        elif x.text == "Parivāra-aṭṭhakathā":
            g.vin_book = "VINa5"
            g.section_counter = 0

    if x["rend"] in ["chapter", "subsubhead"]:
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter += 1
        
        g.source = f"{g.vin_book}.{g.section_counter}"
        g.sutta = section.lower()
        
        g.sutta_counter = 0
        g.vagga = ""
        g.vagga_counter = 0

        # exceptions
        if x.text in [
            "Verañjakaṇḍavaṇṇanā",
            "Ganthārambhakathā"
        ]:
            g.section_counter = 0
            g.vagga_counter += 1
            g.source = f"{g.vin_book}.{g.section_counter}"
            
        if "bhikkhunīvibhaṅgavaṇṇanā" in x.text:
            section = section.replace(" (bhikkhunīvibhaṅgavaṇṇanā)", "")
            g.source = f"{g.vin_book}{g.section_counter}"
            g.sutta = section.lower()
        
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        
        if is_int(vagga_no):
            g.vagga_counter = vagga_no
        
        g.source = f"{g.vin_book}.{g.section_counter}.{g.vagga_counter}"
        g.sutta = g.vagga.lower()
        g.sutta_counter = 0

        # exceptions
        if g.vin_book == "BHI VINa":
            g.source = f"{g.vin_book}{g.section_counter}.{g.vagga_counter}"
        if x.text == "Bāhiranidānakathā":
            g.source = f"{g.vin_book}.0"
        if x.text == "Nigamanakathā":
            g.source = f"{g.vin_book}"
    
    elif x["rend"] == "subhead":
        if "(" not in x.text:
            sutta, sutta_no = get_text_and_number(x.text)
        else:
            sutta, sutta_no = get_text_and_number_with_brackets1(x.text)

        if g.vin_book != "BHI VINa":
            if is_int(sutta_no):
                g.sutta_counter = int(sutta_no)
                
                if g.vagga_counter:
                    g.source = f"{g.vin_book}.{g.section_counter}.{g.vagga_counter}.{g.sutta_counter}"
                    g.sutta = f"{g.vagga}, {sutta}".lower()
                
                else:
                    g.source = f"{g.vin_book}.{g.section_counter}.{g.sutta_counter}"
                    g.sutta = f"{g.section}, {sutta}".lower()
            
            else:
                if g.vin_book == "VINa1":
                    
                    # intro
                    if g.section_counter == 0: 
                        g.source = f"{g.vin_book}.{g.section_counter}"
                        g.sutta = sutta.lower()
                    
                    # pārājika
                    elif g.section_counter == 1: 
                        g.source = f"{g.vin_book}.{g.section_counter}.{g.vagga_counter}"
                        g.sutta = f"{g.vagga}, {sutta}".lower()
                
                else:
                    g.sutta_counter += 1
                    g.source = f"{g.vin_book}.{g.section_counter}.{g.sutta_counter}"
                    g.sutta = f"{g.section}, {sutta}".lower()
        
        else:
            g.sutta_counter += 1
            g.source = f"{g.vin_book}{g.section_counter}.{g.sutta_counter}"
            g.sutta = sutta.lower()
            if g.vagga_counter:
                g.source = f"{g.vin_book}{g.section_counter}.{g.vagga_counter}.{sutta_no}"
                g.sutta = f"{g.vagga}, {g.sutta}".lower()


def dna_digha_nikaya_commentary(g: GlobalData):
    # vagga   <head rend="subsubhead">Ganthārambhakathā</head>
    # vagga     <head rend="chapter">1. Brahmajālasuttavaṇṇanā</head>
    # sutta  <p rend="subhead">Paribbājakakathāvaṇṇanā</p>

    book = "DNa"
    x = g.x

    if x["rend"] == "subsubhead":
        g.source = f"{book}0"
        g.source_alt = f"{book}0"
        g.vagga = x.text.lower()
    
    elif x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga_alt_counter = vagga_no

        if vagga_no == "1":
            g.section_counter += 1
            match g.section_counter:
                case 1:
                    g.vagga_counter = 0
                case 2:
                    g.vagga_counter = 13
                case 3:
                    g.vagga_counter = 23

        g.vagga = vagga.lower()
        g.vagga_counter += 1
        g.source = f"{book}{g.vagga_counter}"
        g.source_alt = f"{book}{g.section_counter}.{vagga_no}"
        g.sutta = vagga.lower()
        g.sutta_counter = 0
    
    if x["rend"] == "subhead":
        sutta, _ = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        g.source_alt = f"{book}{g.section_counter}.{g.vagga_alt_counter}.{g.sutta_counter}"
        g.sutta = f"{g.vagga}, {sutta}".lower()


def mna_majjhima_nikaya_commentary(g: GlobalData):
    # ignore    <p rend="subhead">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subsubhead">Ganthārambhakathā</p>
    # vagga     <head rend="chapter">1. Mūlapariyāyavaggo</head>
    # sutta     <p rend="subhead">1. Mūlapariyāyasuttavaṇṇanā</p>

    book = "MNa"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text.strip())
        g.vagga = vagga
        g.vagga_counter = vagga_no
        
    elif x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text.strip())
        g.source = f"{book}0"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "subhead":
        if re.findall(r"^\d", x.text):               
            sutta, sutta_no = get_text_and_number(x.text.strip())
            g.sutta_counter += 1
            g.source = f"{book}{g.sutta_counter}"
            g.sutta = sutta.lower()
        elif x.text == "Suttanikkhepavaṇṇanā":
            subtitle, _ = get_text_and_number(x.text.strip())
            g.subtitle_counter += 1
            g.source = f"{book}{g.sutta_counter}"
            g.sutta = f"{g.sutta_clean}, {subtitle}".lower()
        else:
            subtitle, subtitle_no = get_text_and_number(x.text.strip())
            g.source = f"{book}{g.sutta_counter}"
            g.sutta = f"{g.sutta_clean}, {subtitle}".lower()


def sna_samyutta_nikaya_commentary(g: GlobalData):
    # sutta     <head rend="subsubhead">Ganthārambhakathā</head>
    # samyutta  <head rend="chapter">1. Nidānasaṃyuttaṃ</head>
    # vagga     <p rend="title">1. Buddhavaggo</p>
    # sutta     <p rend="subhead">1. Paṭiccasamuppādasuttavaṇṇanā</p>

    book = "SNa"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}0"
        g.sutta = x.text.lower()
    
    elif x["rend"] == "chapter":
        samyutta, samyutta_no = get_text_and_number(x.text)
        g.samyutta = samyutta
        g.samyutta_counter += 1
        g.source = f"{book}{g.samyutta_counter}"
        g.sutta = samyutta.lower()
        g.sutta_counter = 0

    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
    
    elif x["rend"] == "subhead":

        if x.text == "Nigamanakathā":
            g.source = f"{book}{g.samyutta_counter}.{g.vagga_counter}"
            g.sutta = x.text.lower()
        else: 
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.source = f"{book}{g.samyutta_counter}.{g.vagga_counter}.{sutta_no}"
            g.sutta = sutta.lower()


def ana_formatter(text: str):
    """an2_4 > AN2.4"""
    return text \
        .replace("an", "") \
        .replace("_", ".")


def ana_anguttara_nikaya_commentary(g: GlobalData):
    # div       <div id="an2_4" n="an2_4" type="peyyala">
    # book      <head rend="book">Dukanipāta-aṭṭhakathā</head>
    # sutta     <head rend="subsubhead">Ganthārambhakathā</head>
    # section   <p rend="title">Saṃkhepakathā</p>
    # vagga     <head rend="chapter">1. Rūpādivaggavaṇṇanā</head>
    # sutta     <p rend="subhead">Nidānavaṇṇanā</p>

    book = "ANa"
    x = g.x

    # find the book number
    try:
        g.anguttara_counter = ana_formatter(x.parent["id"])
        g.section_counter = re.sub("\..+", "", g.anguttara_counter)
    except KeyError:
        pass

    # find the sutta number using bodytext "n"
    if x["rend"] == "bodytext":
        try:
            g.sutta_counter = x.attrs["n"]
            g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        except KeyError:
            pass
    
    if x["rend"] == "subsubhead":
        g.sutta = x.text.lower()
    
    elif x["rend"] == "subhead":
        if x.text == "Nigamanakathā":
            g.source = "ANa"
            g.sutta = x.text.lower()
        else: 
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta = sutta.lower()


def kn1a_khuddakapāṭha_commentary(g: GlobalData):
    # <p rend="chapter">Ganthārambhakathā</p>
    pass

    book = "KPa"
    x = g.x

    if x["rend"] == "chapter":
        if x.text == "Ganthārambhakathā":
            section, section_no = get_text_and_number(x.text)
            g.section = section
            g.section_counter = 0
        else:
            section, section_no = get_text_and_number(x.text)
            g.section = section
            g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = f"{g.section}".lower()
        g.sutta_counter = 0
    
    elif x["rend"] == "subhead":
        sutta, _ = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = f"{g.section}, {sutta}".lower()   


def kn2a_dhammpada_commentary(g: GlobalData):
    # <p rend="title">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subhead">Ganthārambhakathā</p>
    # vagga     <p rend="chapter">1. Yamakavaggo</p>
    # sutta     <p rend="subhead">1. Cakkhupālattheravatthu</p>

    book = "DHPa"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()

    if x["rend"] == "subhead":
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}0"
            g.sutta = x.text.lower()
        elif x.text == "Nigamanakathā":
            g.source = f"{book}"
            g.sutta = x.text.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter = sutta_no
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
            g.sutta = f"{g.vagga}, {sutta}".lower()


def kn3a_udana_commentary(g: GlobalData):
    # <p rend="chapter">Ganthārambhakathā</p>
    # <p rend="chapter">1. Bodhivaggo</p>
    # <p rend="subhead">1. Paṭhamabodhisuttavaṇṇanā</p>

    book = "UDa"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}0"
            g.sutta = x.text.lower()
        elif x.text == "Nigamanakathā":
            g.source = f"{book}"
            g.sutta = x.text.lower()
        else:
            g.source = f"{book}{g.vagga_counter}"
            g.sutta = vagga.lower()

    if x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.sutta_counter_alt = sutta_no
        g.source = f"{book}{g.sutta_counter}"
        g.source_alt = f"{book}{g.vagga_counter}.{g.sutta_counter_alt}"
        g.sutta = f"{sutta}".lower()


def kn4a_itivuttaka_commentary(g: GlobalData):
    # <p rend="subhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Ekakanipāto</p>
    # <p rend="title">1. Paṭhamavaggo</p>
    # <p rend="subhead">1. Lobhasuttavaṇṇanā</p>

    book = "ITIa"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}"
        g.sutta = section.lower()

        g.vagga = ""

    if x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {g.vagga}".lower()

    if x["rend"] == "subhead":
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}0"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Nidānavaṇṇanā":
            g.source = f"{book}0"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()  
        elif x.text == "Nigamanakathā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            if "-" in sutta_no:
                start, end, diff = split_sutta_number(sutta_no)
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter+1}-{g.sutta_counter+diff}"
                g.sutta_counter += diff
            else:
                g.sutta_counter += 1
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter}"
                g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter_alt}"
                g.sutta = f"{sutta}".lower()


def kn5a_suttanipata_commentary(g: GlobalData):
    pass
    # ignore    <p rend="title">(Paṭhamo bhāgo)</p>
    # sutta     <p rend="subhead">Ganthārambhakathā</p>
    # vagga     <p rend="chapter">1. Uragavaggo</p>
    # sutta     <p rend="subhead">1. Uragasuttavaṇṇanā</p>

    book = "SNPa"
    x = g.x

    if x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.vagga_counter}"
        g.sutta = f"{g.vagga}".lower()

    if x["rend"] == "subhead":
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}0"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Nidānavaṇṇanā":
            g.source = f"{book}0"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()  
        elif x.text == "Nigamanakathā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Vatthugāthāvaṇṇanā":
            g.source = f"{book}55"
            g.source_alt = f"{book}5.0"
            g.sutta = x.text.lower()
        elif x.text == "Pārāyanatthutigāthāvaṇṇanā":
            g.source = f"{book}72"
            g.source_alt = f"{book}5.17"
            g.sutta = x.text.lower()
        elif x.text == "Pārāyanānugītigāthāvaṇṇanā":
            g.source = f"{book}73"
            g.source_alt = f"{book}5.18"
            g.sutta = x.text.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter += 1
            g.sutta_counter_alt = sutta_no
            g.source = f"{book}{g.sutta_counter}"
            g.source_alt = f"{book}{g.vagga_counter}.{g.sutta_counter_alt}"
            g.sutta = f"{sutta}".lower()


def kn6a_vimanavatthu_commentary(g: GlobalData):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Itthivimānaṃ</p>
    # <p rend="title">1. Pīṭhavaggo</p>
    # <p rend="subhead">1. Paṭhamapīṭhavimānavaṇṇanā</p>
    # <p rend="subhead">Nigamanakathā</p>

    book = "VVa"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}"
        g.sutta = section.lower()
        g.vagga = ""

    if x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {g.vagga}".lower()

    if x["rend"] in["subhead", "subsubhead"]:
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}0"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Nigamanakathā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            if "-" in sutta_no:
                start, end, diff = split_sutta_number(sutta_no)
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter+1}-{g.sutta_counter+diff}"
                g.sutta_counter += diff
            else:
                g.sutta_counter += 1
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter}"
                g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter_alt}"
                g.sutta = f"{sutta}".lower()

   
def kn7a_petavatthu_commentary(g: GlobalData):

    # vagga     <p rend="chapter">1. Uragavaggo</p>
    # sutta     <p rend="subhead">1. Khettūpamapetavatthuvaṇṇanā</p>

    book = "PVa"
    x = g.x

    if x["rend"] == "subsubhead":
        g.source = f"{book}"
        g.sutta = x.text.lower()
    
    elif x["rend"] == "chapter":
        vagga, vagga_no = get_text_and_number(x.text)
        vagga_no = re.sub(r"\. *.+", "", x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()
    
    elif x["rend"] == "subhead":
        if re.findall(r"^\d", x.text):
            sutta, sutta_no = get_text_and_number(x.text)
            g.source = f"{book}{g.vagga_counter}.{sutta_no}"
            g.sutta = f"{sutta}".lower()
        else:
            g.source = f"{book}"
            g.sutta = x.text.lower()


def kn8a_9a_thera_therigatha_commentary(g: GlobalData):
    # <p rend="title">(Paṭhamo bhāgo)</p>
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Ekakanipāto</p>
    # <p rend="title">1. Paṭhamavaggo</p>
    # <p rend="subhead">1. Subhūtittheragāthāvaṇṇanā</p>

    match g.book:
        case "kn8a":
            book = "THa"
        case "kn9a":
            book = "THIa"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}"
        g.sutta = section.lower()
        g.vagga = ""
        g.vagga_counter = 0

    if x["rend"] == "title" and not x.text.startswith("("): # eg (Paṭhamo bhāgo)
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}"
        g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}"
        g.sutta = f"{g.section}, {g.vagga}".lower()

    if x["rend"] in["subhead", "subsubhead"]:
        if x.text == "Ganthārambhakathā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Nigamanagāthā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        elif x.text == "Nidānagāthāvaṇṇanā":
            g.source = f"{book}"
            g.source_alt = f"{book}"
            g.sutta = x.text.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            if "-" in sutta_no:
                start, end, diff = split_sutta_number(sutta_no)
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter+1}-{g.sutta_counter+diff}"
                if g.vagga:
                    g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter_alt}"
                else:
                    g.source_alt = f"{book}{g.section_counter}.{g.sutta_counter_alt}"
                g.sutta_counter += diff
            else:
                g.sutta_counter += 1
                g.sutta_counter_alt = sutta_no
                g.source = f"{book}{g.sutta_counter}"
                if g.vagga:
                    g.source_alt = f"{book}{g.section_counter}.{g.vagga_counter}.{g.sutta_counter_alt}"
                else:
                    g.source_alt = f"{book}{g.section_counter}.{g.sutta_counter_alt}"
                g.sutta = f"{sutta}".lower()


def kn10a_therapadana_commentary(g: GlobalData):
    # vagga     <p rend="subsubhead">Ganthārambhakathā</p>
    # vagga     <p rend="subsubhead">1. Dūrenidānakathā</p>
    # sutta  <p rend="subhead">Sumedhakathā</p>     
    # vagga     <p rend="chapter">1. Buddhavaggo</p>
    # sutta     <p rend="subhead">Abbhantaranidānavaṇṇanā</p>

    book = "APAa"
    x = g.x

    if x["rend"] in ["subsubhead"]:
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = 0
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()
    
    elif x["rend"] in ["subhead"] and g.vagga_counter == 0:
        sutta, sutta_no = get_text_and_number(x.text)
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = sutta.lower() 

    elif x["rend"] in ["chapter"]:
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()
    
    elif x["rend"] in ["subhead"]:
        if "-" in x.text and g.vagga_counter == "1":
            sutta, sutta_no = get_text_and_number(x.text)
            sutta_no = sutta_no.replace("-", ".")
            g.sutta_counter = sutta_no
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        elif x.text in ["Abbhantaranidānavaṇṇanā"]:
            sutta = x.text
            g.sutta_counter = 0
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        elif x.text in ["Nigamanakathā"]:
            sutta = x.text
            g.sutta_counter = ""
            g.source = f"{book}"
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter = sutta_no
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        g.sutta = f"{sutta}".lower()


def kn12a_buddhavamsa_commentary(g: GlobalData):
    # sutta         <p rend="subsubhead">Ganthārambhakathā</p>
    # section       <p rend="chapter">27. Gotamabuddhavaṃsavaṇṇanā</p>
    # sutta         <p rend="subhead">Dūrenidānakathā</p>
    
    book = "BVa"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.section_counter = 0
        g.source = f"{book}{g.section_counter}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = g.section.lower()
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta = f"{g.section}, {sutta}".lower()


def kn13a_cariyapitaka_commentary(g: GlobalData):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="chapter">1. Akittivaggo</p>
    # <p rend="subhead">1. Akitticariyāvaṇṇanā</p>
    
    book = "CPa"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.section_counter = 0
        g.source = f"{book}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = g.section.lower()
        g.sutta_counter = 0
    
    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = f"{sutta}".lower()


def kn14a_jataka_commentary(g: GlobalData):
    # bhaga     <p rend="title">(Paṭhamo bhāgo)</p>
    # nipāta    <p rend="chapter">1. Ekakanipāto</p>
    # vagga     <p rend="title">1. Apaṇṇakavaggo</p>
    # sutta     <p rend="bodytext"> 1. Apaṇṇakajātakavaṇṇanā</p>
    # sutta     <p rend="subhead">[111] 1. Gadrabhapañhajātakavaṇṇanā</p>
    # sutta     <p rend="subsubhead">Ganthārambhakathā</p>

    book = "JAa"
    x = g.x

    if x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
    
    elif x["rend"] == "title":
        vagga, vagga_no = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter = vagga_no

    elif (
        x["rend"] == "bodytext"
        and "jātakavaṇṇanā" in x.text
    ):
        if x.text.strip().startswith("["):
            sutta, sutta_no = get_text_and_number_with_sqaure_brackets(x.text.strip())
            g.sutta_counter = sutta_no
            g.source = f"{book}{sutta_no}"
            g.sutta = sutta.lower()
        elif re.findall(r"^\d", x.text.strip()):
            sutta, sutta_no = get_text_and_number(x.text.strip())
            g.source = f"{book}{sutta_no}"
            g.sutta = sutta.lower()
    
    elif x["rend"] == "subhead":
        if "jātakavaṇṇanā" in x.text:
            sutta, sutta_no = get_text_and_number_with_sqaure_brackets(x.text.strip())
            g.sutta = sutta.lower()
        else:
            subtitle, subtitle_no = get_text_and_number(x.text.strip())
            g.source = f"{book}{g.sutta_counter}"
            g.sutta = f"{g.sutta_clean}, {subtitle}".lower()
    
    elif x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = sutta.lower()


def kn15a_mahaniddesa_commentary(g: GlobalData):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <p rend="title">1. Aṭṭhakavaggo</p>
    # <p rend="chapter">1. Kāmasuttaniddesavaṇṇanā</p>

    book = "NIDD1a"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter = sutta_no
        g.source = f"{book}{g.sutta_counter}"
        g.sutta = sutta.lower()


def kn16a_culaniddesa_commentary(g: GlobalData):
    # <p rend="chapter">Pārāyanavagganiddeso</p>
    # <p rend="subhead">1. Ajitamāṇavasuttaniddesavaṇṇanā</p>

    book = "NIDD2a"
    x = g.x

    if x["rend"] == "chapter":
        section, _ = get_text_and_number(x.text)
        g.section = section
        g.section_counter += 1
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()
    
    if x["rend"] == "subhead":
        if x.text == "Nigamanakathā":
            sutta, _ = get_text_and_number(x.text)
            g.source = book
            g.sutta = sutta.lower()
        else:
            sutta, sutta_no = get_text_and_number(x.text)
            g.sutta_counter = sutta_no
            g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
            if g.section_counter == 1:
                g.sutta = sutta.lower()
            else:
                g.sutta = f"{g.section}, {sutta}".lower()


def kn17a_patisambhidamagga_commentary(g: GlobalData):
    # vagga     <p rend="chapter">(1) Mahāvaggo</p>
    # section   <p rend="chapter">1. Ñāṇakathā</p>
    # ignore    <p rend="title">(Dutiyo bhāgo)</p>
    # sutta     <p rend="title">70. Yamakapāṭihīrañāṇaniddesavaṇṇanā</p>
    # ignore    <p rend="subhead">Dutiyacchakkaṃ</p>

    book = "PMa"
    x = g.x

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
        "Gha-ṅa. pariyādānaṭṭhapatiṭṭhāpakaṭṭhaniddesavaṇṇanā"
        "Gatikathāvaṇṇanā",
        "Kammakathāvaṇṇanā",
        "Vipallāsakathāvaṇṇanā",
        "Maggakathāvaṇṇanā",
        "Maṇḍapeyyakathāvaṇṇanā",
        "Mahāpaññākathāvaṇṇanā",
        "Iddhikathāvaṇṇanā",
    ]

    if x["rend"] == "subsubhead":
        sutta, _ = get_text_and_number(x.text)
        g.source = f"{book}0"
        g.sutta = sutta.lower()

    elif x["rend"] == "chapter":
        if x.text.startswith("("):  # (1) Mahāvaggo
            vagga, vagga_no = get_text_and_number_with_brackets1(x.text)
            g.vagga = vagga
            g.vagga_counter = vagga_no
            g.source = f"{book}{g.vagga_counter}"
            g.sutta = g.vagga.lower()
            g.section_counter = 0
        else:   # 6. Pāṭihāriyakathā
            section, section_no = get_text_and_number(x.text)
            g.section = section
            g.section_counter = section_no
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}"
            g.sutta = section.lower()
            g.sutta_counter = 0

    elif x["rend"] == "title" and x.text not in ignore_list:
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter  = sutta_no
        if int(g.section_counter) > 0:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}.{g.sutta_counter}"
        else:
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"
        g.sutta = sutta.lower()
        g.subtitle_counter = 0
    
    # elif x["rend"] == "subhead" and x.text not in ignore_list:
    #     subtitle, subtitle_no = get_text_and_number(x.text)
    #     g.subtitle_counter +=1
    #     g.source = f"{book}{g.vagga_counter}.{g.section_counter}.{g.sutta_counter}.{g.subtitle_counter}"
    #     g.sutta = subtitle.lower()


def kn19a_netti_commentary(g: GlobalData):
    # <p rend="subsubhead">Ganthārambhakathā</p>
    # <head rend="chapter">1. Saṅgahavāro</head>
    # <p rend="subhead">Tassānugīti</p>

    book = "NPa"
    x = g.x

    if x["rend"] == "subsubhead":
        vagga, _ = get_text_and_number(x.text)
        g.vagga = vagga
        g.source = f"{book}"
        g.sutta = vagga.lower()  

    elif x["rend"] == "chapter":
        vagga, _ = get_text_and_number(x.text)
        g.vagga = vagga
        g.vagga_counter += 1
        g.sutta_counter = 0
        g.source = f"{book}{g.vagga_counter}"
        g.sutta = vagga.lower()
        g.section_counter = 0
    
    elif x["rend"] == "subhead":
        if x.text == "1. Desanāhāravibhaṅgavaṇṇanā":
            g.section_counter += 1
        elif x.text == "1. Desanāhārasampātavaṇṇanā":
            g.section_counter += 1
            g.sutta_counter = 0
        elif x.text == "14. Adhiṭṭhānahārasampātavaṇṇanā":
            g.sutta_counter = 13
        sutta_name, _ = get_text_and_number(x.text)
        g.sutta_counter += 1
        if g.section_counter > 0:
            g.source = f"{book}{g.vagga_counter}.{g.section_counter}.{g.sutta_counter}"            
        else:
            g.source = f"{book}{g.vagga_counter}.{g.sutta_counter}"            
        g.sutta = sutta_name.lower()


def vism_visuddhimagga_and_commentary(g: GlobalData):
    # section   <p rend="subsubhead">Nidānādikathā</p>
    # section   <p rend="title">Dukkhaniddesakathā</p>
    # section   <p rend="chapter">1. Sīlaniddeso</p>
    # sutta     <p rend="subhead">Sīlasarūpādikathā</p>

    match g.book:
        case "vism":
            book = "VISM"
        case "visma":
            book = "VISMa"
    x = g.x

    if x["rend"] in ["subsubhead"]:
        sutta, sutta_no = get_text_and_number(x.text.strip())
        g.source = f"{book}0"
        g.sutta = sutta.lower()

    elif x["rend"] in ["chapter"]:
        section, section_no = get_text_and_number(x.text.strip())
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()

        g.sutta_counter = 0
    
    elif x["rend"] in ["subhead"]:
        sutta, sutta_no = get_text_and_number(x.text.strip())
        g.sutta_counter += 1
        g.source = g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = f"{g.section}, {sutta}".lower()

# TODO grammar books


def ap_abhidhanapadipika(g: GlobalData):
    # vagga         <p rend="subhead">Buddhappaṇāmo</p>
    # kaṇḍa         <p rend="chapter">1. Saggakaṇḍa</p>
    # vagga         <p rend="title">1. Bhūmivagga</p>

    book = "APP"
    x = g.x

    if x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.section = ""
        g.section_counter = "0"
        g.sutta_counter += 1
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()

    elif x["rend"] == "title":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter = sutta_no
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = sutta.lower()


def apt_abhidhanapadipikatika(g: GlobalData):
    # sutta     <p rend="subsubhead">Ganthārambha</p>
    # sutta     <p rend="subhead">Paṇāmādivaṇṇanā</p>
    # kaṇḍa     <p rend="chapter">1. Saggakaṇḍavaṇṇanā</p>
    # sutta     <p rend="title">2<hi rend="dot">.</hi> Puravaggavaṇṇanā</p>
    # sutta     <p rend="subhead">Nigamanavaṇṇanā</p>


    book = "APt"
    x = g.x

    book = "AP"
    x = g.x

    if x["rend"] == "subsubhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.section = ""
        g.section_counter = "0"
        g.sutta_counter = 0 
        g.source = f"{book}"
        g.sutta = sutta.lower()

    elif x["rend"] == "subhead":
        sutta, sutta_no = get_text_and_number(x.text)
        g.section = ""
        if x.text == "Paṇāmādivaṇṇanā":
            g.source = f"{book}0"
        else:
            g.source = f"{book}"
        g.sutta = sutta.lower()
    
    elif x["rend"] == "chapter":
        section, section_no = get_text_and_number(x.text)
        g.section = section
        g.section_counter = section_no
        g.source = f"{book}{g.section_counter}"
        g.sutta = section.lower()

    elif x["rend"] == "title":
        sutta, sutta_no = get_text_and_number(x.text)
        g.sutta_counter = sutta_no
        g.source = f"{book}{g.section_counter}.{g.sutta_counter}"
        g.sutta = sutta.lower()


def find_source_sutta_example(
        book: str, 
        text_to_find: str
) -> List[Tuple[str, str, str]]:

    g: GlobalData = GlobalData(book, text_to_find)
    for soup in g.soups:
        soup_chunks = soup.find_all(["head", "p"])
        for x in soup_chunks:
            g.soup_tag_list.add(x["rend"])
            g.x = x
            g.example = ""
            g.text = clean_example(x.text)

            # find examples
            
            if (
                text_to_find is not None
                and re.findall(text_to_find, g.text)
            ):
                if "gatha" in x["rend"]:
                    find_gatha_example(g)
                else:
                    find_sentence_example(g)
            
            # find source and sutta

            match book:
                case "vin1":
                    vin1_parajika(g)
                case "vin2":
                    vin2_pacittiya(g)
                case "vin3" | "vin4":
                    vin3_vin4_maha_culavagga(g)
                
                case "dn1" | "dn2" | "dn3":
                    dn_digha_nikaya(g)
                case "mn1" | "mn2" | "mn3":
                    mn_majjhima_nikaya(g)
                case "sn1" | "sn2" | "sn3" | "sn4" | "sn5":
                    sn_samyutta_nikaya(g)
                case "an1" | "an2" | "an3" | "an4" | "an5" | "an6" | \
                    "an7" | "an8" | "an9" | "an10" | "an11":
                    an_anguttara_nikaya(g)
                case "kn1":
                    kn1_khuddakapāṭha(g)
                case "kn2":
                    kn2_dhammpada(g)
                case "kn3":
                    kn3_udana(g)
                case "kn4":
                    kn4_itivuttaka(g)
                case "kn5":
                    kn5_suttanipata(g)
                case "kn6":
                    kn6_vimanavatthu(g)
                case "kn7":
                    kn7_petavatthu(g)
                case "kn8" | "kn9":
                    kn8_9_thera_therigatha(g)
                case "kn10" | "kn11":
                    kn10_11_thera_theriapadana(g)
                case "kn12":
                    kn12_buddhavamsa(g)
                case "kn13":
                    kn13_cariyapitaka(g)
                case "kn14":
                    kn14_jataka(g)
                case "kn15":
                    kn15_mahaniddesa(g)
                case "kn16":
                    kn16_culaniddesa(g)
                case "kn17":
                    kn17_patisambhidamagga(g)
                case "kn18":
                    kn18_milindapanha(g)
                case "kn19":
                    kn19_netti(g)
                case "kn20":
                    kn20_petakopadesa(g)
                
                case "abh1":
                    abh1_dhammasangani(g)
                case "abh2":
                    abh2_vibhanga(g)
                case "abh3":
                    abh3_dhatukatha(g)
                case "abh4":
                    abh4_puggalapannati(g)
                case "abh5":
                    abh5_kathavatthu(g)
                case "abh6":
                    abh6_yamaka(g)
                case "abh7":
                    abh7_patthana(g)

                case "vina":
                    vina_commentary(g)
                case "dna":
                    dna_digha_nikaya_commentary(g)
                case "mna":
                    mna_majjhima_nikaya_commentary(g)
                case "sna":
                    sna_samyutta_nikaya_commentary(g)
                case "ana":
                    ana_anguttara_nikaya_commentary(g)
                case "kn1a":
                    kn1a_khuddakapāṭha_commentary(g)
                case "kn2a":
                    kn2a_dhammpada_commentary(g)
                case "kn3a":
                    kn3a_udana_commentary(g)
                case "kn4a":
                    kn4a_itivuttaka_commentary(g)
                case "kn5a":
                    kn5a_suttanipata_commentary(g)
                case "kn6a":
                    kn6a_vimanavatthu_commentary(g)
                case "kn7a":
                    kn7a_petavatthu_commentary(g)
                case "kn8a" | "kn9a":
                    kn8a_9a_thera_therigatha_commentary(g)
                case "kn10a":
                    kn10a_therapadana_commentary(g)
                # case "kn11a": doesnt exist
                case "kn12a":
                    kn12a_buddhavamsa_commentary(g)
                case "kn13a":
                    kn13a_cariyapitaka_commentary(g)
                case "kn14a":
                    kn14a_jataka_commentary(g)
                case "kn15a":
                    kn15a_mahaniddesa_commentary(g)
                case "kn16a":
                    kn16a_culaniddesa_commentary(g)
                case "kn17a":
                    kn17a_patisambhidamagga_commentary(g)
                case "kn19a":
                    kn19a_netti_commentary(g)
                
                case "vism" | "visma":
                    vism_visuddhimagga_and_commentary(g)
                case "ap":
                    ap_abhidhanapadipika(g)
                case "apt":
                    apt_abhidhanapadipikatika(g)


            if (
                g.source and g.sutta
                and (g.source, g.source_alt, g.sutta) not in g.source_sutta_list
            ):
                g.source_sutta_list.append((g.source, g.source_alt, g.sutta))
            
            if (
                g.source and g.sutta and g.example
                and (g.source, g.sutta, g.example) not in g.source_sutta_examples 
            ):
                g.source_sutta_examples.append((g.source, g.sutta, g.example))

    if g.debug:
        for sc in g.source_sutta_list:
            print(sc)
        print(f"tag list: {sorted(g.soup_tag_list)}")

        for sce in g.source_sutta_examples:
            print(sce)

    return g.source_sutta_examples


if __name__ == "__main__":
    book = "dna"
    text_to_find = "akatvā"
    sutta_examples = find_source_sutta_example(book, text_to_find)
    print(len(sutta_examples))
