"""Functions related to the GUI."""

import re
import csv
import subprocess
import textwrap
import pickle
from typing import Optional, Tuple, List, Dict

from spellchecker import SpellChecker
from aksharamukha import transliterate
from rich import print
from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize

# from db.db_helpers import get_column_names
from db.models import PaliWord
from functions_db import make_all_inflections_set
from functions_db import get_family_compound_values
from functions_db import values_to_pali_word

from tools.pos import INDECLINEABLES
from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_sc_text_set
from tools.paths import ProjectPaths as PTH
from tools.pali_text_files import cst_texts
from tools.pali_alphabet import pali_alphabet
from tools.configger import config_test_option
from tools.configger import config_update
from tools.configger import config_test
# from tools.meaning_construction import make_meaning
# from tools.tsv_read_write import read_tsv_dot_dict


def add_sandhi_correction(window, values: dict) -> None:
    sandhi_to_correct = values["sandhi_to_correct"]
    sandhi_correction = values["sandhi_correction"]

    if sandhi_to_correct == "" or sandhi_correction == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    elif " + " not in sandhi_correction:
        window["messages"].update(
            "no plus sign in sandhi correction!", text_color="red")

    else:

        with open(
                PTH.manual_corrections_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([sandhi_to_correct, sandhi_correction])
            window["messages"].update(
                f"{sandhi_to_correct} > {sandhi_correction} added to corrections", text_color="white")
            window["sandhi_to_correct"].update("")
            window["chB"].update("")
            window["sandhi_correction"].update("")


def open_sandhi_corrections():
    subprocess.Popen(
        ["code", PTH.manual_corrections_path])


def add_sandhi_rule(window, values: dict) -> None:
    chA = values["chA"]
    chB = values["chB"]
    ch1 = values["ch1"]
    ch2 = values["ch2"]
    example = values["example"]
    usage = values["usage"]

    if (chA == "" or chB == "" or (ch1 == "" and ch2 == "")):
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    elif "'" not in example:
        window["messages"].update(
            "use an apostrophe in the example!", text_color="red")

    else:

        with open(PTH.sandhi_rules_path, "r") as f:
            reader = csv.reader(f, delimiter="\t")

            for row in reader:
                print(row)
                if row[0] == chA and row[1] == chB and row[2] == ch1 and row[3] == ch2:
                    window["messages"].update(
                        f"{row[0]}-{row[1]} {row[2]}-{row[3]} {row[4]} {row[5]} already exists!", text_color="red")
                    break
            else:
                with open(
                        PTH.sandhi_rules_path, mode="a", newline="") as file:
                    writer = csv.writer(file, delimiter="\t")
                    writer.writerow([chA, chB, ch1, ch2, example, usage])
                    window["messages"].update(
                        f"{chA}-{chB} {ch1}-{ch2} {example} {usage} added to rules!", text_color="white")
                    window["chA"].update("")
                    window["chB"].update("")
                    window["ch1"].update("")
                    window["ch2"].update("")
                    window["example"].update("")
                    window["usage"].update("")


def open_sandhi_rules():
    subprocess.Popen(
        ["code", PTH.sandhi_rules_path])


def add_spelling_mistake(window, values: dict) -> None:
    spelling_mistake = values["spelling_mistake"]
    spelling_correction = values["spelling_correction"]

    if spelling_mistake == "" or spelling_correction == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:

        with open(
                PTH.spelling_mistakes_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([spelling_mistake, spelling_correction])
            window["messages"].update(
                f"{spelling_mistake} > {spelling_correction} added to spelling mistakes", text_color="white")
            window["spelling_mistake"].update("")
            window["spelling_correction"].update("")


def open_spelling_mistakes():
    subprocess.Popen(
        ["code", PTH.spelling_mistakes_path])


def add_variant_reading(window, values: dict) -> None:
    variant_reading = values["variant_reading"]
    main_reading = values["main_reading"]

    if variant_reading == "" or main_reading == "":
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:
        with open(
                PTH.variant_readings_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([variant_reading, main_reading])
            window["messages"].update(
                f"{variant_reading} > {main_reading} added to variant readings", text_color="white")
            window["variant_reading"].update("")
            window["main_reading"].update("")


def open_variant_readings():
    subprocess.Popen(
        ["code", PTH.variant_readings_path])


def open_sandhi_ok():
    subprocess.Popen(
        ["code", PTH.sandhi_ok_path])


def open_sandhi_exceptions():
    subprocess.Popen(
        ["code", PTH.sandhi_exceptions_path])


def add_stem_pattern(values, window):
    pos = values["pos"]
    grammar = values["grammar"]
    pali_1 = values["pali_1"]
    pali_1_clean = re.sub(r"\s\d.*$", "", pali_1)

    if pos == "adj":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a adj")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī adj")
        if pali_1_clean.endswith("ant"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ant adj")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u adj")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i adj")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū adj")
        if pali_1_clean.endswith("aka"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("aka adj")

    elif pos == "masc":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a masc")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī masc")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i masc")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u masc")
        if pali_1_clean.endswith("ar"):
            window["stem"].update(pali_1_clean[:-2])
            window["pattern"].update("ar masc")
        if pali_1_clean.endswith("as"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("as masc")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū masc")
        if pali_1_clean.endswith("ant"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ant masc")
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a masc pl")
        if pali_1_clean.endswith("as"):
            window["stem"].update(pali_1_clean[:-2])
            window["pattern"].update("as masc")

    elif pos == "fem":
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā fem")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i fem")
        if pali_1_clean.endswith("ī"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ī fem")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u fem")
        if pali_1_clean.endswith("ar"):
            window["stem"].update(pali_1_clean[:-2])
            window["pattern"].update("ar fem")
        if pali_1_clean.endswith("ū"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ū fem")
        if pali_1_clean.endswith("mātar"):
            window["stem"].update(pali_1_clean[:-5])
            window["pattern"].update("mātar fem")

    elif pos == "nt":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a nt")
        if pali_1_clean.endswith("u"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("u nt")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i nt")

    elif pos == "card":
        if "x pl" in grammar:
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a1 card")
        if "nt sg" in grammar:
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a2 card")
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i card")
        if pali_1_clean.endswith("koṭi"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i2 card")
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā card")

    elif pos == "ordin":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a ordin")

    elif pos == "pp":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a pp")

    elif pos == "prp":
        if pali_1_clean.endswith("anta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("anta prp")
        if pali_1_clean.endswith("enta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("enta prp")
        if pali_1_clean.endswith("onta"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("onta prp")
        if pali_1_clean.endswith("māna"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("māna prp")
        elif pali_1_clean.endswith("āna"):
            window["stem"].update(pali_1_clean[:-4])
            window["pattern"].update("āna prp")

    elif pos == "ptp":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a ptp")

    elif pos == "pron":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a pron")

    elif pos == "pr":
        if pali_1_clean.endswith("ati"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("ati pr")
        if pali_1_clean.endswith("eti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("eti pr")
        if pali_1_clean.endswith("oti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("oti pr")
        if pali_1_clean.endswith("āti"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("āti pr")

    elif pos == "aor":
        if pali_1_clean.endswith("i"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("i aor")
        if pali_1_clean.endswith("esi"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("esi aor")
        if pali_1_clean.endswith("āsi"):
            window["stem"].update(pali_1_clean[:-3])
            window["pattern"].update("āsi aor")

    elif pos == "perf":
        if pali_1_clean.endswith("a"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("a perf")

    elif pos == "imperf":
        if pali_1_clean.endswith("ā"):
            window["stem"].update(pali_1_clean[:-1])
            window["pattern"].update("ā imperf")

    elif pos in INDECLINEABLES:
        window["stem"].update("-")
        window["pattern"].update("")

# !!! add all the plural forms !!!





def check_spelling(field, error_field, values, window):

    spell = SpellChecker(language='en')
    spell.word_frequency.load_text_file(str(PTH.user_dict_path))

    sentence = values[field]
    words = word_tokenize(sentence)

    misspelled = spell.unknown(words)

    candidates = ""
    for word in misspelled:
        candidates = spell.candidates(word)
    window[error_field].update(f"{candidates}")


def add_spelling(word):
    with open(PTH.user_dict_path, "a") as f:
        f.write(f"{word}\n")


def edit_spelling():
    subprocess.Popen(
        ["code", PTH.user_dict_path])


def clear_errors(window):
    error_elements = [
        e for e in window.element_list()
        if hasattr(e, "key") and isinstance(e.key, str) and "error" in e.key]
    for e in error_elements:
        window[e.key].update("")


def clear_values(values, window, primary_user):
    from functions_db import dpd_values_list
    origin = "pass" if primary_user else "dps"
    for value in values:
        if value in dpd_values_list:
            window[value].update("")
    window["family_root"].update(values=[])
    window["root_sign"].update(values=[])
    window["root_base"].update(values=[])
    window["origin"].update(origin)
    window["root_info"].update("")


def find_commentary_defintions(sg, values, definitions_df):

    test1 = definitions_df["bold"].str.contains(values["search_for"])
    test2 = definitions_df["commentary"].str.contains(
        values["contains"])
    filtered = test1 & test2
    df_filtered = definitions_df[filtered]
    search_results = df_filtered.to_dict(orient="records")

    layout_elements = []
    layout_elements.append(
        [
            sg.Button(
                "Add Commentary Definition", key="add_button_1"),
            sg.Button(
                "Cancel", key="cancel_1")
        ]
    )

    if len(search_results) < 50:
        layout_elements.append(
            [sg.Text(f"{len(search_results)} results ")])
    else:
        layout_elements.append(
            [sg.Text("dispalying the first 50 results. \
                please refine your search")])

    for i, r in enumerate(search_results):
        if i >= 50:
            break
        else:
            try:
                commentary = r["commentary"].replace("<b>", "")
                commentary = commentary.replace("</b>", "")
                commentary = textwrap.fill(commentary, 150)

                layout_elements.append(
                    [
                        sg.Checkbox(f"{i}.", key=i),
                        sg.Text(r["ref_code"]),
                        sg.Text(r["bold"], text_color="white"),
                    ]
                )
                layout_elements.append(
                    [
                        sg.Text(
                            f"{commentary}", size=(150, None),
                            text_color="lightgray"),
                    ],
                )
            except Exception:
                layout_elements.append([sg.Text("no results")])

    layout_elements.append([
        sg.Button(
            "Add Commentary Definition", key="add_button_2"),
        sg.Button(
            "Cancel", key="cancel_2")
        ])

    layout = [
        [
            [
                sg.Column(
                    layout=layout_elements, key="results",
                    expand_y=True, expand_x=True,
                    scrollable=True, vertical_scroll_only=True
                )
            ],
        ]
    ]

    window = sg.Window(
        "Find Commentary Defintions",
        layout,
        resizable=True,
        size=(1920, 1080),
        finalize=True
    )

    while True:
        event, values = window.read()
        if event == "Close" or event == sg.WIN_CLOSED:
            break

        if event == "add_button_1" or event == "add_button_2":
            return_results = []
            number = 0
            for value in values:
                if values[value]:
                    number = int(value)
                    return_results += [search_results[number]]

            window.close()
            return return_results

        if event == "cancel_1" or event == "cancel_2":
            window.close()

    window.close()


def transliterate_xml(xml):
    """transliterate from devanagari to roman"""
    xml = transliterate.process("autodetect", "IASTPali", xml)
    if xml is None:
        # Handle the error, perhaps by raising an exception or returning a default value.
        raise ValueError("Failed to transliterate XML.")
    xml = xml.replace("ü", "u")
    xml = xml.replace("ï", "i")
    return xml


def find_sutta_example(sg, window, values: dict) -> Optional[Dict[str, str]]:

    filename = ""

    if values["book_to_add"] in cst_texts:
        try:
            filename = cst_texts[values["book_to_add"]][0].replace(".txt", ".xml")
        except KeyError as e:
            window["messages"].update(e, text_color="red")

        with open(
                PTH.cst_xml_dir.joinpath(filename), "r", encoding="UTF-16") as f:
            xml = f.read()
        xml = transliterate_xml(xml)

        with open(PTH.cst_xml_roman_dir.joinpath(filename), "w") as w:
            w.write(xml)
        print(PTH.cst_xml_roman_dir.joinpath(filename))

        soup = BeautifulSoup(xml, "xml")

        # remove all the "pb" tags
        pbs = soup.find_all("pb")
        for pb in pbs:
            pb.decompose()

        # unwrap all the notes
        notes = soup.find_all("note")
        for note in notes:
            note.replace_with(fr" [{note.text}] ")

        # unwrap all the hi parunum dot tags
        his = soup.find_all("hi", rend=["paranum", "dot"])
        for hi in his:
            hi.unwrap()

        word_to_add = values["word_to_add"][0]
        ps = soup.find_all("p")
        source = ""
        sutta = ""

        sutta_sentences = []
        sutta_counter = 0
        udana_counter = 0
        itivuttaka_counter = 0
        snp_counter = 0
        for p in ps:

            if p["rend"] == "subhead":
                if "suttaṃ" in p.text:
                    sutta_counter += 1
                source = values["book_to_add"].upper()
                book = re.sub(r"\d", "", source)
                # add space to digtis
                source = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", source)
                sutta_number = ""
                try:
                    sutta_number = p.next_sibling.next_sibling["n"]
                except KeyError as e:
                    window["messages"].update(e, text_color="red")

                # choose which method to number suttas according to book
                if values["book_to_add"].startswith("mn1"):
                    source = f"{book} {sutta_counter}"
                elif values["book_to_add"].startswith("mn2"):
                    source = f"{book} {sutta_counter+50}"
                elif values["book_to_add"].startswith("mn3"):
                    source = f"{book} {sutta_counter+100}"
                elif values["book_to_add"].startswith("an"):
                    source = f"{source}.{sutta_number}"
                elif values["book_to_add"].startswith("sn"):
                    source = ""

                # remove the digits and the dot in sutta name
                sutta = re.sub(r"\d*\. ", "", p.text)

            # dn
            if "dn" in values["book_to_add"]:
                book = "DN "
                if p.has_attr("rend") and p["rend"] == "subhead":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    chapter_text = chapter_head.text
                    pattern = r"^(\d+)\.\s+(.*)$"
                    match = re.match(pattern, chapter_text)
                    if match:
                        if values["book_to_add"] == "dn1":
                            source = f"{book}{match.group(1)}"
                        if values["book_to_add"] == "dn2":
                            # there are 13 suttas previously in dn1
                            source = f"{book}{int(match.group(1))+13}"
                        if values["book_to_add"] == "dn3":
                            # there are 13+10 suttas previously in dn1 & dn2
                            source = f"{book}{int(match.group(1))+23}"
                        sutta = match.group(2)

            # kn1
            if values["book_to_add"] == "kn1":
                book = "KHP"
                chapter_text = None
                if not chapter_text:
                    chapter_div = p.find_parent("div", {"type": "chapter"})
                    if chapter_div:
                        chapter_text = chapter_div.find("head").get_text()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book}{match.group(1)}"
                            sutta = match.group(2)
                        

            # kn2
            elif values["book_to_add"] == "kn2":
                book = "DHP "
                if p.has_attr("rend") and p["rend"] == "hangnum":
                    # Find the previous "head" tag with "rend" attribute containing "chapter"
                    chapter_head = p.find_previous("head", attrs={"rend": "chapter"})
                    if chapter_head is not None:
                        chapter_text = chapter_head.string.strip()
                        pattern = r"^(\d+)\.\s+(.*)$"
                        match = re.match(pattern, chapter_text)
                        if match:
                            source = f"{book}{match.group(1)}"
                            sutta = match.group(2)

            elif values["book_to_add"] == "kn3":
                book = "UD"
                if p["rend"] == "subhead":
                    udana_counter += 1
                    source = f"{book} {udana_counter}"

            elif values["book_to_add"] == "kn4":
                book = "ITI"
                if p["rend"] == "subhead":
                    itivuttaka_counter += 1
                    source = f"{book} {itivuttaka_counter}"

            elif values["book_to_add"] == "kn5":
                book = "SNP"
                if p["rend"] == "subhead":
                    snp_counter += 1
                    source = f"{book} {snp_counter}"

            text = clean_example(p.text)

            if word_to_add is not None and word_to_add in text:

                # compile gathas line by line
                if "gatha" in p["rend"]:
                    example = ""

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

                    text = clean_gatha(p.text)
                    text = text.replace(".", ",\n")
                    example += text

                    while True:
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
                            example += text
                            break

                    sutta_sentences += [{
                        "source": source,
                        "sutta": sutta,
                        "example": example}]

                # or compile sentences
                else:
                    sentences = sent_tokenize(text)
                    for i, sentence in enumerate(sentences):
                        if word_to_add in sentence:
                            prev_sentence = sentences[i - 1] if i > 0 else ""
                            next_sentence = sentences[i + 1] if i < len(sentences)-1 else ""
                            sutta_sentences += [{
                                "source": source,
                                "sutta": sutta,
                                "example": f"{prev_sentence} {sentence} {next_sentence}"}]

        sentences_list = [sentence["example"] for sentence in sutta_sentences]

        layout_elements = []
        layout_elements.append([
            sg.Button(
                "Add Sutta Example", key="add_button_1"),
            sg.Button(
                "Cancel", key="cancel_1")
        ])

        layout_elements.extend([
            [
                sg.Radio(
                    "", "sentence",
                    key=f"{i}",
                    text_color="lightblue",
                    pad=((0, 10), 5)),
                sg.Multiline(
                    sentences_list[i],
                    wrap_lines=True,
                    auto_size_text=True,
                    size=(100, 2),
                    text_color="lightgray",
                    no_scrollbar=True,
                )
            ]
            for i in range(len(sentences_list))
        ])

        layout_elements.append([
            sg.Button(
                "Add Sutta Example", key="add_button_2"),
            sg.Button(
                "Cancel", key="cancel_2")
        ])

        layout = [[
            [
                sg.Column(
                    layout=layout_elements, key="results",
                    expand_y=True, expand_x=True,
                    scrollable=True, vertical_scroll_only=True
                )
            ],
        ]]

        window = sg.Window(
            "Find Sutta Examples",
            layout,
            resizable=True,
            size=(1920, 1080),
            finalize=True
        )

        while True:
            event, values = window.read()

            if event == "Close" or event == sg.WIN_CLOSED:
                break

            if event == "add_button_1" or event == "add_button_2":
                number = 0
                for value in values:
                    if values[value] is True:
                        number = int(value)

                if sutta_sentences != []:
                    window.close()
                    return sutta_sentences[number]
                else:
                    window.close()
                    return None

            if event == "cancel_1" or event == "cancel_2":
                window.close()

        window.close()

    else:
        window["messages"].update("book code not found", text_color="red")


def clean_example(text):
    text = text.lower()
    text = text.replace("‘", "")
    text = text.replace(" – ", ", ")
    text = text.replace("’", "")
    text = text.replace("…pe॰…", " ... ")
    text = text.replace(";", ",")
    text = text.replace("  ", " ")
    text = text.replace("..", ".")
    text = text.replace(" ,", ",")

    return text


def clean_gatha(text):
    text = clean_example(text)
    text = text.replace(", ", ",\n")
    text = text.strip()
    return text


def find_gathalast(p, example):

    while p["rend"] != "gathalast":
        p = p.next_sibling
        if p.text == "\n":
            pass
        elif p["rend"] == "gatha2":
            example += p.text
        elif p["rend"] == "gatha3":
            example += p.text
        elif p["rend"] == "gathalast":
            example += p.text
        p = p.next_sibling


def test_book_to_add(values, window):
    """Test if book is in cst texts."""
    book = values["book_to_add"]
    if book in cst_texts:
        window["messages"].update(
            f"adding {book} ...", text_color="white")
        window.refresh()
        return True
    else:
        window["messages"].update(
            f"{book} invalid book code", text_color="red")
        return False


def make_words_to_add_list(window, book: str) -> list:
    cst_text_list = make_cst_text_set([book], return_list=True)
    sc_text_list = make_sc_text_set([book], return_list=True)
    original_text_list = list(cst_text_list) + list(sc_text_list)

    sp_mistakes_list = make_sp_mistakes_list(PTH)
    variant_list = make_variant_list(PTH)
    sandhi_ok_list = make_sandhi_ok_list(PTH)
    all_inflections_set = make_all_inflections_set()

    text_set = set(cst_text_list) | set(sc_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))
    print(f"words_to_add: {len(text_list)}")

    return text_list


# def make_text_list(window, PTH, book: str) -> list:
#     text_list = []

#     if book in cst_texts and book in sc_texts:
#         for b in cst_texts[book]:
#             filepath = PTH.cst_txt_dir.joinpath(b)
#             with open(filepath) as f:
#                 text_read = f.read()
#                 text_clean = clean_machine(text_read)
#                 text_list += text_clean.split()

#     else:
#         window["messages"].update(
#             f"{book} not found", text_color="red")

#     print(f"text list: {len(text_list)}")
#     return text_list


def make_sp_mistakes_list(PTH):

    with open(PTH.spelling_mistakes_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sp_mistakes_list = [row[0] for row in reader]

    print(f"sp_mistakes_list: {len(sp_mistakes_list)}")
    return sp_mistakes_list


def make_variant_list(PTH):
    with open(PTH.variant_readings_path) as f:
        reader = csv.reader(f, delimiter="\t")
        variant_list = [row[0] for row in reader]

    print(f"variant_list: {len(variant_list)}")
    return variant_list


def make_sandhi_ok_list(PTH):
    with open(PTH.sandhi_ok_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sandhi_ok_list = [row[0] for row in reader]

    print(f"sandhi_ok_list: {len(sandhi_ok_list)}")
    return sandhi_ok_list


def open_in_goldendict(word: str) -> None:
    cmd = ["goldendict", word]
    subprocess.Popen(cmd)


def open_inflection_tables():
    subprocess.Popen(
        ["libreoffice", PTH.inflection_templates_path])


def sandhi_ok(window, word,):
    with open(PTH.sandhi_ok_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([word])
    window["messages"].update(f"{word} added", text_color="white")


class Flags:
    def __init__(self):
        self.show_fields = True
        self.pali_2 = True
        self.grammar = True
        self.derived_from = True
        self.family_root = True
        self.root_sign = True
        self.root_base = True
        self.family_compound = True
        self.construction = True
        self.suffix = True
        self.compound_construction = True
        self.synoyms = True
        self.commentary = True
        self.sanskrit = True
        self.example_1 = True
        self.example_2 = False
        self.stem = True
        self.tested = False
        self.test_next = False


def reset_flags(flags):
    flags.show_fields = True
    flags.pali_2 = True
    flags.grammar = True
    flags.derived_from = True
    flags.family_root = True
    flags.root_sign = True
    flags.root_base = True
    flags.family_compound = True
    flags.construction = True
    flags.suffix = True
    flags.compound_construction = True
    flags.synoyms = True
    flags.commentary = True
    flags.sanskrit = True
    flags.example_1 = True
    flags.example_2 = False
    flags.stem = True
    flags.tested = False
    flags.test_next = False


def display_summary(values, window, sg):
    from functions_db import dpd_values_list
    summary = []
    for value in values:
        if value in dpd_values_list:
            if values[value] != "":
                if len(values[value]) < 40:
                    summary += [[
                        value, values[value]
                    ]]
                else:
                    wrapped_lines = textwrap.wrap(values[value], width=40)
                    summary += [[value, wrapped_lines[0]]]
                    for wrapped_line in wrapped_lines:
                        if wrapped_line != wrapped_lines[0]:
                            summary += [["", wrapped_line]]

    summary_layout = [
                [
                    sg.Table(
                        summary,
                        headings=["field", "value"],
                        auto_size_columns=False,
                        justification="left",
                        col_widths=[20, 50],
                        expand_y=True
                    )
                ],
                [
                    sg.Button("Edit", key="edit_button"),
                    sg.Button("OK", key="ok_button"),
                ]
    ]

    window = sg.Window(
        "Summary",
        summary_layout,
        location=(400, 0),
        size=(800, 1000)
        )

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "ok_button" or event == "edit_button":
            break
    window.close()
    return event


family_compound_values = get_family_compound_values()


def test_family_compound(values, window):
    family_compounds = values["family_compound"].split()
    error_string = ""
    for family_compound in family_compounds:
        if family_compound not in family_compound_values:
            error_string += f"{family_compound} "

    window["family_compound_error"].update(
        error_string, text_color="red")


def remove_word_to_add(values, window, words_to_add_list):
    try:
        words_to_add_list = [
            word for word in words_to_add_list
            if word not in values["word_to_add"]
        ]
        window["word_to_add"].update(words_to_add_list)
    except UnboundLocalError as e:
        window["messages"].update(e, text_color="red")

    return words_to_add_list


def add_to_word_to_add(values, window, words_to_add_list):
    if values["add_construction"]:
        words_to_add_list.insert(0, values["add_construction"])
        window["add_construction"].update("")
        window["messages"].update(
            f"{values['add_construction']} added to words to add list",
            text_color="white")

    return words_to_add_list


def save_gui_state(values, words_to_add_list):
    save_state: tuple = (values, words_to_add_list)
    print(f"[green]saving gui state, values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")
    with open(PTH.save_state_path, "wb") as f:
        pickle.dump(save_state, f)


def load_gui_state():
    with open(PTH.save_state_path, "rb") as f:
        save_state = pickle.load(f)
    values = save_state[0]
    words_to_add_list = save_state[1]
    print(f"[green]loading gui state, values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")
    return values, words_to_add_list


def test_construction(values, window, pali_clean_list):
    construction_list = values["construction"].split(" + ")
    error_string = ""
    for c in construction_list:
        if c not in pali_clean_list:
            error_string += f"{c} "
    window["construction_error"].update(error_string, text_color="red")


def replace_sandhi(string, field: str, sandhi_dict: dict, window) -> None:
    pali_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_string}])", string)

    for i in range(len(splits)):
        word = splits[i]
        if word in sandhi_dict:
            splits[i] = "//".join(sandhi_dict[word]["contractions"])
    string = "".join(splits)

    string = string.replace("</b>ti", "</b>'ti")    # fix bold 'ti
    string = string.replace("</b>nti", "n</b>'ti")  # fix bold 'ti
    string = string.replace(",</b>", "</b>,")  # fix bold comma
    string = re.sub(r"\[[^]]*\]", "", string)   # remove [...]
    string = re.sub(" +", " ", string)  # remove double spaces
    string = re.sub(r"^\d*\. ", "", string)  # remove digits in front
    string = string.strip()  # remove spaces front n back

    window[field].update(string)


def test_username(sg):
    """If no username in config.ini, save one.
    Return user_1 or user_2."""
    while True:
        if not config_test_option("user", "username"):
            username = sg.popup_get_text(
                "What is your name?", title="username")
            if username:
                config_update("user", "username", username)
                break
        else:
            break
    if config_test("user", "username", "1"):
        return True
    else:
        return False


def compare_differences(
        values: dict, sg, pali_word_original: PaliWord, action):
    """Comapre the differences between original and new word.
    Save to corrections or additions TSV."""

    if (
        action == "updated" and
        pali_word_original
    ):
        # check what's changed
        got_comment = set()
        fields = pali_word_original.__dict__
        for field in fields.keys():
            if field in values:
                if str(getattr(pali_word_original, field)) != values[field]:
                    group = None
                    if field in ["source_1", "sutta_1", "example_1"]:
                        group = "source_sutta_example1"
                    elif field in ["source_2", "sutta_2", "example_2"]:
                        group = "source_sutta_example2"
                    elif field in ["derivative", "suffix"]:
                        group = "derivative_suffix"
                    elif field in ["compound_type", "compound_construction"]:
                        group = "compound_type_construction"
                    elif field in ["stem", "pattern"]:
                        group = "stem_pattern"

                    if group not in got_comment:
                        while True:
                            prompt = f"{field} has changed, why?\n"
                            prompt += f"old: {getattr(pali_word_original, field)}\n"
                            prompt += f"new: {values[field]}"
                            comment = sg.popup_get_text(
                                prompt, title="comment", location=(400, 400))
                            if comment:
                                break

                        if group:
                            got_comment.add(group)

                        if group == "source_sutta_example1":
                            correction = [
                                values["id"],
                                "source_1",
                                values["source_1"],
                                "sutta_1",
                                values["sutta_1"],
                                "example_1",
                                values["example_1"],
                                comment,
                                "", ""]

                        elif group == "source_sutta_example2":
                            correction = [
                                values["id"],
                                "source_2",
                                values["source_2"],
                                "sutta_2",
                                values["sutta_2"],
                                "example_2",
                                values["example_2"],
                                comment,
                                "", ""]

                        elif group == "derivative_suffix":
                            correction = [
                                values["id"],
                                "derivative",
                                values["derivative"],
                                "suffix",
                                values["suffix"],
                                "",
                                "",
                                comment,
                                "", ""]

                        elif group == "compound_type_construction":
                            correction = [
                                values["id"],
                                "compound_type",
                                values["compound_type"],
                                "compound_construction",
                                values["compound_construction"],
                                "",
                                "",
                                comment,
                                "", ""]

                        elif group == "stem_pattern":
                            correction = [
                                values["id"],
                                "stem",
                                values["stem"],
                                "pattern",
                                values["pattern"],
                                "",
                                "",
                                comment,
                                "", ""]

                        else:
                            correction = [
                                values["id"],
                                field,
                                values[field],
                                "",
                                "",
                                "",
                                "",
                                comment,
                                "", ""]

                        with open(PTH.corrections_tsv_path, "a") as file:
                            writer = csv.writer(file, delimiter="\t")
                            writer.writerow(correction)

    elif (
        action == "added" or
        not pali_word_original
    ):
        while True:
            prompt = "Please comment on this new word."
            comment = sg.popup_get_text(
                prompt, title="comment", location=(400, 400))
            if comment:
                break

        pali_word = values_to_pali_word(values)
        if PTH.additions_pickle_path.exists():
            additions = additions_load()
        else:
            additions = []
        additions.append((pali_word, comment))
        additions_save(additions)


def additions_load() -> List[Tuple]:
    """Load the list of word to add to db from pickle file."""
    with open(PTH.additions_pickle_path, "rb") as file:
        additions = pickle.load(file)
        print(additions)
        return additions


def additions_save(additions):
    """Save the list of word to add to db to pickle file."""
    with open(PTH.additions_pickle_path, "wb") as file:
        pickle.dump(additions, file)
