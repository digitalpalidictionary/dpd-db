import re
import time

from bs4 import BeautifulSoup
from nltk import sent_tokenize
from typing import Tuple, List

from tools.paths import ProjectPaths
from tools.pali_text_files import cst_texts


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


def make_cst_soup(
        pth: ProjectPaths,
        filenames: list[str],
        unwrap_notes=True
) -> list[BeautifulSoup]:
    
    """Take a list of filenames and return a list of soups."""
    
    soups: list[BeautifulSoup] = []

    for filename in filenames:
        filename = filename.replace(".txt", ".xml")

        with open(
            pth.cst_xml_roman_dir.joinpath(filename), "r", encoding="UTF-16"
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


def init_samyutta_counter(book: str) -> int:
    """Initialize the start of the samyutta_counter for each book."""
    if book == "sn2":
        return 11
    elif book == "sn3":
        return 21
    elif book == "sn4":
        return 34
    elif book == "sn5":
        return 44
    else:
        return 0


def find_source_sutta_example(
        pth: ProjectPaths,
        book: str, 
        text_to_find: str
        ) -> List[Tuple[str, str, str]]:

    sutta_examples: List[Tuple[str, str, str]] = []

    filenames: list[str] = get_cst_filenames(book)
    soups = make_cst_soup(pth, filenames)

    samyutta_counter = init_samyutta_counter(book)
    sutta_counter = 0
    kn_counter = 0

    for soup_counter, soup in enumerate(soups):

        ps = soup.find_all(["p", "head"])
        
        four_nikayas = [
            "dn1", "dn2", "dn3",
            "mn1", "mn2", "mn3",
            "sn1", "sn2", "sn3", "sn4", "sn5",
            "an1", "an2", "an3", "an4", "an5",
            "an6", "an7", "an8", "an9", "an10", "an11"]
        
        # variables
        source = None
        sutta = None

        chapter = None
        chapter_num = None
        vagga = None
        title = None
        title_no = None
        subhead = None
        rule = None
        is_bhikkhuni = False
        source_sutta_list = []
        sutta_name = None
        
        for p in ps:
            
            # sutta example consist of either gāthas or sentences
            # which need to be processed differently
 
            example = None
            text = clean_example(p.text)

            if text_to_find is not None and re.findall(text_to_find, text):

                # compile gathas line by line

                if "gatha" in p["rend"]:
                    example = ""

                    start_time = time.time()
                    while True:
                        if p.text == "\n":
                            p = p.previous_sibling
                        elif p["rend"] == "gatha1":
                            break
                        elif p["rend"] == "gatha2":
                            p = p.previous_sibling
                        elif p["rend"] == "gatha3":
                            p = p.previous_sibling
                        elif p["rend"] == "gathalast":
                            p = p.previous_sibling
                        if time.time() - start_time > 1:
                            print(f"[bright_red]{text_to_find} [red]is stuck in a loop")
                            break

                    text = clean_gatha(p.text)
                    example += text

                    while True:
                        try:
                            if p is not None:
                                p = p.next_sibling
                                if p.text == "\n":
                                    pass
                                elif p["rend"] == "gatha2":
                                    text = clean_gatha(p.text)
                                    text = text.replace(".", ",")
                                    example += text
                                elif p["rend"] == "gatha3":
                                    text = clean_gatha(p.text)
                                    text = text.replace(".", ",")
                                    example += text
                                elif p["rend"] == "gathalast":
                                    text = clean_gatha(p.text)
                                    text = re.sub(",$", ".", text)
                                    example += text
                                    break
                            else:
                                break
                        except AttributeError as e:
                            print(f"[red]{e}")
                            print(text_to_find)
                            print(p)
                            break

                # or compile sentences

                else:
                    sentences = sent_tokenize(text)
                    for i, sentence in enumerate(sentences):
                        if re.findall(text_to_find, sentence):
                            prev_sentence = sentences[i - 1] if i > 0 else ""
                            next_sentence = sentences[i + 1] if i < len(sentences)-1 else ""
                            example = f"{prev_sentence} {sentence} {next_sentence}"

            # compile source and sutta

            if (
                book in four_nikayas
                and book not in ["sn1", "sn2", "sn3", "sn4", "sn5"]
            ):
                if p["rend"] == "subhead":
                    if "suttaṃ" in p.text:
                        sutta_counter += 1
                    source = book.upper()
                    book_name = re.sub(r"\d", "", source)
                    sutta_number = ""
                    try:
                        sutta_number = p.next_sibling.next_sibling["n"]
                    except Exception as e:
                        print(e)
                        print(text_to_find)
                        print(p)
                        continue

                    # choose which method to number suttas according to book
                    if book.startswith("mn1"):
                        source = f"{book_name}{sutta_counter}"
                    elif book.startswith("mn2"):
                        source = f"{book_name}{sutta_counter+50}"
                    elif book.startswith("mn3"):
                        source = f"{book_name}{sutta_counter+100}"
                    elif book.startswith("an"):
                        source = f"{source}.{sutta_number}"

                    # remove the digits and the dot in sutta name
                    sutta = re.sub(r"\d*\. ", "", p.text)
                    sutta = re.sub(r" \[.*?\]", "", sutta)


            # dn
            if "dn" in book:
                book_name = "DN"
                if p.has_attr("rend") and p["rend"] == "subhead":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    chapter_text = chapter_head.text
                    pattern = r"^(\d+)\.\s+(.*)$"
                    match = re.match(pattern, chapter_text)
                    if match:
                        if book == "dn1":
                            source = f"{book_name}{match.group(1)}"
                        if book == "dn2":
                            # there are 13 suttas previously in dn1
                            source = f"{book_name}{int(match.group(1))+13}"
                        if book == "dn3":
                            # there are 13+10 suttas previously in dn1 & dn2
                            source = f"{book_name}{int(match.group(1))+23}"
                        sutta = match.group(2)
            
            # TODO cleanup all 'chapter_head = p.find_previous'
            # TODO clean up DN sutta counter
            
            # sn1-5
            # Structure of Saṃyutta Nikaya is 
            # main_vagga    <head rend="book">Sagāthāvaggo</head>
            # samyutta      <head rend="chapter">1. Devatāsaṃyuttaṃ</head>
            # vagga         <p rend="title">1. Naḷavaggo</p>
            # sutta         <p rend="subhead">1. Oghataraṇasuttaṃ</p>

            elif book in ["sn1", "sn2", "sn3", "sn4", "sn5"]:
                book_name = "SN"

                if p["rend"] == "chapter":
                    samyutta = re.sub(r"^\d*\. ", "", p.text.lower())
                    samyutta_counter += 1
                    sutta_counter = 0
                    sutta_name = ""

                elif p["rend"] == "title":
                    vagga = re.sub(r"^\d*\. ", "", p.text.lower())
                    vagga_no = re.sub("\\. *.+", "", p.text)

                elif (
                    p["rend"] == "subhead"
                    and re.findall(r"^\d", p.text)
                    and "-" not in p.text                       # a "-" in the sutta means it contains multiple suttas
                ):
                    sutta_name = re.sub(r"^\d*\. ", "", p.text.lower())
                    sutta_counter += 1
                    sutta_counter_special = ""

                # deal with peyyāla suttas individually
                elif (
                    p["rend"] == "subhead"
                    and "-" in p.text                           # a "-" in the sutta means it contains multiple suttas
                ):
                    for peyyala in  peyyalas:
                        p_samyutta_counter, p_sutta_name, p_start, p_end = peyyala
                        if (
                            p_samyutta_counter == samyutta_counter
                            and p.text == p_sutta_name
                            and sutta_counter == p_start-1
                        ):
                            sutta_name = re.sub(r"^\d.*\. ", "", p.text)
                            sutta_counter_special = f"{p_start}-{p_end}"
                            sutta_counter = p_end
                            break
                            
                if sutta_name:
                    if sutta_counter_special:
                        source = f"{book_name}{samyutta_counter}.{sutta_counter_special}"
                    else:
                        source = f"{book_name}{samyutta_counter}.{sutta_counter}" 
                    sutta = f"{samyutta}, {sutta_name}".lower()
                    source_sutta = (source, sutta)
                    if source_sutta not in source_sutta_list:
                        source_sutta_list.append(source_sutta)
                        print(source_sutta)
                

            # vin1 
            # there are four subdivisions
            # 1. chapter of rules = pārājika, saṅghādisesa, aniyata, nissaggiya, etc. 
            # 2. vagga: in some cases, if more than 13 rules
            # 3. rule: name of the rule
            # 4. subhead: subsection of the rule
            # and corresponding chapter, vagga and title numbers

            elif book in ["vin1"]:
                book_name = "VIN1"

                if p["rend"] == "chapter":
                    chapter = re.sub(r"^\d*\. ", "", p.text.lower()) 
                    chapter_num = re.sub("\\. *.+", "", p.text)
                    if chapter == "verañjakaṇḍaṃ":
                        chapter_num = "0"
                    
                    title = ""                                          # reset everything on a new chapter
                    title_no = ""
                    vagga = ""
                    vagga_no = ""

                if p["rend"] == "title" and "vaggo" in p.text:
                    vagga = re.sub(r"^\d*\. ", "", p.text.lower())
                    vagga_no = re.sub("\\. *.+", "", p.text)
                    title = ""                                          # reset title on a new vagga

                if p["rend"] == "title" and "vaggo" not in p.text:
                    title = re.sub(r"^\d*\. ", "", p.text.lower())
                    title_no = re.sub("\\. *.+", "", p.text)
                    subhead = ""                                        # reset the subhead on a new title

                if p["rend"] == "subhead":
                    subhead = p.text.lower()
                
                # make source numbering
                if chapter_num and vagga_no and title_no:
                    source = f"{book_name}.{chapter_num}.{vagga_no}.{title_no}"
                elif chapter_num and vagga_no and not title_no:
                    source = f"{book_name}.{chapter_num}.{vagga_no}"
                elif chapter_num and not vagga_no and title_no:         # pārajika has no vaggas
                    source = f"{book_name}.{chapter_num}.{title_no}"            
                elif chapter_num and not vagga_no and not title_no:
                    source = f"{book_name}.{chapter_num}"
            
                # make sutta title
                if title and subhead:
                    sutta = f"{title}, {subhead}"
                elif title and not subhead:
                    sutta = f"{title}"
                elif not title and not subhead and vagga:
                    sutta = f"{chapter}, {vagga}"
                else:
                    sutta = chapter

            # vin2

            elif book in ["vin2"]:

                # this switches is_bhikkhuni to True at the start of the Bhikkhunīvibhaṅgo
                # because bhikkhuni vinaya has its own logical sequence 

                if (
                    not is_bhikkhuni
                    and p["rend"] == "book"
                    and p.text == "Bhikkhunīvibhaṅgo"
                ):
                    is_bhikkhuni = True
                    source = None
                    sutta = None
                    
                if not is_bhikkhuni:
                    book_name = "VIN2"

                    if p["rend"] == "chapter":
                        chapter = re.sub(r"^\d*\. ", "", p.text.lower()) 
                        chapter_num = re.sub("\\. *.+", "", p.text)
                        
                        rule = ""                                          # reset everything on a new chapter
                        rule_no = ""
                        vagga = ""
                        vagga_no = ""

                    if p["rend"] == "title" and "vaggo" in p.text:
                        vagga = re.sub(r"^\d*\. ", "", p.text.lower())
                        vagga_no = re.sub("\\. *.+", "", p.text)
                        rule = ""                                          # reset rule on a new vagga

                    if p["rend"] == "title" and "vaggo" not in p.text:
                        rule = re.sub(r"^\d*\. ", "", p.text.lower())
                        rule_no = re.sub("\\. *.+", "", p.text)
        

                    if p["rend"] == "subhead":
                        rule = re.sub(r"^\d*\. ", "", p.text.lower())
                        rule_no = re.sub("\\. *.+", "", p.text)
                    
                    # make source numbering
                    if chapter_num and vagga_no and rule_no:
                        source = f"{book_name}.{chapter_num}.{vagga_no}.{rule_no}"
                    elif chapter_num and vagga_no and not rule_no:
                        source = f"{book_name}.{chapter_num}.{vagga_no}"
                    elif chapter_num and not vagga_no and rule_no:         # pārājika has no vaggas
                        source = f"{book_name}.{chapter_num}.{rule_no}"            
                    elif chapter_num and not vagga_no and not rule_no:
                        source = f"{book_name}.{chapter_num}"
                
                    # make sutta = rule
                    if rule:
                        sutta = rule
                    elif not rule and vagga:
                        sutta = f"{chapter}, {vagga}"
                    else:
                        sutta = chapter

                # bhikkhuni vinaya

                elif is_bhikkhuni:
                    book_name = "BHI VIN"

                    def bhikkhuni_cleaner(text):
                        return text.replace(" (bhikkhunīvibhaṅgo)", "")

                    if p["rend"] == "chapter":
                        chapter = re.sub(r"^\d*\. ", "", p.text.lower())
                        chapter = bhikkhuni_cleaner(chapter)
                        chapter_num = re.sub("\\. *.+", "", p.text)
                        
                        rule = ""                                          # reset everything on a new chapter
                        rule_no = ""
                        vagga = ""
                        vagga_no = ""

                    if p["rend"] == "title" and "vaggo" in p.text:
                        vagga = re.sub(r"^\d*\. ", "", p.text.lower())
                        vagga_no = re.sub("\\. *.+", "", p.text)
                        rule = ""                                          # reset rule on a new vagga

                    if p["rend"] == "title" and "vaggo" not in p.text:
                        rule = re.sub(r"^\d*\. ", "", p.text.lower())
                        rule_no = re.sub("\\. *.+", "", p.text)
        
                    if p["rend"] == "subhead" and "vaggo" not in p.text:    # there's only one exception "1. Pattavaggo"
                        rule = re.sub(r"^\d*\. ", "", p.text.lower())
                        rule_no = re.sub("\\. *.+", "", p.text)
                    
                    # make source numbering
                    if chapter_num and vagga_no and rule_no:
                        source = f"{book_name}{chapter_num}.{vagga_no}.{rule_no}"
                    elif chapter_num and vagga_no and not rule_no:
                        source = f"{book_name}{chapter_num}.{vagga_no}"
                    elif chapter_num and not vagga_no and rule_no:         # pārajika has no vaggas
                        source = f"{book_name}{chapter_num}.{rule_no}"            
                    elif chapter_num and not vagga_no and not rule_no:
                        source = f"{book_name}{chapter_num}"
                
                    # make sutta = rule
                    if chapter and vagga and rule:
                        sutta = f"{vagga}, {rule}"
                    elif chapter and not vagga and rule:
                        sutta = f"{chapter}, {rule}"
                    elif chapter and vagga and not rule:
                        sutta = f"{chapter}, {vagga}"
                    else:
                        sutta = chapter


            # vin3-4 mahāvagga & culavagga
            elif book in ["vin3", "vin4"]:
                if book == "vin3":
                    book_name = "VIN3"
                elif book == "vin4":
                    book_name = "VIN4"

                if p.has_attr("rend") and p["rend"] == "subhead":
                    subhead = p.text.lower()

                    bad_subheadings = [
                        "soṇassa pabbajjā", "abhiññātānaṃ pabbajjā"]
                    if subhead in bad_subheadings:
                        continue

                    # remove / keep digits 
                    sub_num = re.sub("\\. *.+", "", subhead)
                    sub_title = re.sub("\\d*\\. *", "", subhead)

                    # if subnum not a digit, then remove
                    if not sub_num[0].isnumeric():
                        sub_num = ""
                    
                    # find the previous head + chapter
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"}).text
                    
                    # remove / keep digits
                    chapter_num = re.sub("\\. *.+", ".", chapter_head)
                    chapter_title =  re.sub("\\d*\\. *", "", chapter_head)

                    # construct the source if there's valid parts
                    # if not, the previous source will be used
                    if book_name and chapter_num and sub_num:
                        source = f"{book_name}.{chapter_num}{sub_num}"

                    # construct the sutta name
                    sutta = f"{chapter_title}, {sub_title}"
                    sutta = sutta.lower()

            # kn1
            elif book == "kn1":
                book_name = "KHP"
                chapter_text = None
                if not chapter_text:
                    chapter_div = p.find_parent("div", {"type": "chapter"})
                    if chapter_div:
                        chapter_text = chapter_div.find("head").get_text()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book_name}{match.group(1)}"
                            sutta = match.group(2)
                        

            # kn2
            elif book == "kn2":
                book_name = "DHP"
                if p.has_attr("rend") and p["rend"] == "hangnum":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    if chapter_head is not None:
                        chapter_text = chapter_head.string.strip()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book_name}{match.group(1)}"
                            sutta = match.group(2)


            elif book == "kn3":
                book_name = "UD"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn4":
                book_name = "ITI"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn5":
                book_name = "SNP"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn6":
                book_name = "VV"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn7":
                book_name = "PV"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn8":
                book_name = "TH"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn9":
                book_name = "THI"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn10":
                book_name = "APA"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn11":
                book_name = "API"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub("\\d*\\. *", "", p.text)

            elif book == "kn12":
                book_name = "BV"
                if p.has_attr("rend") and p["rend"] == "hangnum":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    if chapter_head is not None:
                        chapter_text = chapter_head.string.strip()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book_name}{match.group(1)}"
                            sutta = match.group(2)

            elif book == "kn13":
                book_name = "CP"
                if p.has_attr("rend") and p["rend"] == "hangnum":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    if chapter_head is not None:
                        chapter_text = chapter_head.string.strip()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book_name}{match.group(1)}"
                            sutta = match.group(2)

            elif book == "kn14":
                book_name = "JA"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    source = f"{book_name}{kn_counter}"
                    sutta = re.sub(" .*$", "", sutta)

            elif book == "kn15":
                book_name = "NIDD1"
                if p.has_attr("rend") and p["rend"] == "hangnum":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    if chapter_head is not None:
                        chapter_text = chapter_head.string.strip()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book_name}.{match.group(1)}"
                            sutta = match.group(2)

            elif book == "kn16":
                book_name = "NIDD2"
                if p["rend"] == "subhead":
                    kn_counter += 1
                    # 1-20 is the original pārayan verses and khaggavisāṇa
                    # 21-37 is the cūḷaniddesa
                    # 38-41 is the commentary on khaggavisāṇa
                    if kn_counter < 21:
                        source = f"{book_name}.{kn_counter}"
                        sutta = re.sub(" .*$", "", sutta)
                        print(f"{kn_counter} 1 {source:<10}{sutta:<10}")
                    elif 21 <= kn_counter < 38:
                        source = f"{book_name}.{kn_counter-20}"
                        sutta = re.sub(" .*$", "", sutta)
                        print(f"{kn_counter} 1 {source:<10}{sutta:<10}")
                    elif kn_counter >=38:
                        source = f"{book_name}.19"
                        sutta = "Khaggavisāṇasuttaniddeso, " + re.sub(" .*$", "", sutta)
                        print(f"{kn_counter} 1 {source:<10}{sutta:<10}")
            
            # commentaries

            elif book == "mna":
                book_name = "MNa"
                subhead = ""
                if (
                    p["rend"] == "subhead"
                ):
                    if re.findall(r"^\d", p.text):                  # starts with a digit
                        sutta_name = re.sub(r"\d*\. ", "", p.text)  # remove digits dot space
                        subhead = ""                                # reset subhead
                        sutta_counter += 1                          # increment sutta counter
                    else:
                        if not re.findall(r"^\(", p.text):          # if doesn't start with a bracket like (Dutiyo bhāgo)
                            subhead = p.text
                    source = f"{book_name}{sutta_counter}"
                    if subhead:
                        sutta = f"{sutta_name}, {subhead}"
            
            if source and sutta and example:
                sutta_examples += [(source, sutta.lower(), example)]

    return sutta_examples


# FIXME remove clean_example from functions
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



# FIXME remove clean_gatha from functions
def clean_gatha(text):
    text = clean_example(text)
    text = text.strip()
    text = text.replace(" ,", ",")
    text = text.replace(" .", ".")
    text = text.replace(", ", ",\n")
    text = re.sub(",$", ",\n", text)
    return text


peyyalas = [

    # payyalas is a list of tuples
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


if __name__ == "__main__":
    book = "sn5"
    text_to_find = "sammādiṭṭh"
    
    # FIXME why does it require ProjectPaths?
    pth = ProjectPaths() 
    sutta_examples = find_source_sutta_example(pth, book, text_to_find)
    for sutta_example in sutta_examples:
        print(sutta_example)

