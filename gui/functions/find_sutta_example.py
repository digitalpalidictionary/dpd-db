import re
import nltk

from bs4 import BeautifulSoup
from tools.pali_text_files import cst_texts
from functions.get_paths import get_paths
from rich import print
from aksharamukha import transliterate


def transliterate_xml(xml):
    """transliterate from devanagari to roman"""
    xml = transliterate.process("autodetect", "IASTPali", xml)
    xml = xml.replace("ü", "u")
    xml = xml.replace("ï", "i")
    return xml


def find_sutta_example(sg, values: dict) -> str:
    pth = get_paths()

    filename = cst_texts[values["book_to_add"]][0].replace(".txt", "")

    with open(
            pth.cst_xml_dir.joinpath(filename), "r", encoding="UTF-16") as f:
        xml = f.read()
    xml = transliterate_xml(xml)

    with open(pth.cst_xml_roman_dir.joinpath(filename), "w") as w:
        w.write(xml)
    print(pth.cst_xml_roman_dir.joinpath(filename))

    soup = BeautifulSoup(xml, "xml")

    # remove all the "pb" tags
    pbs = soup.find_all("pb")
    for pb in pbs:
        pb.decompose()

    # unwrap all the notes
    notes = soup.find_all("note")
    for note in notes:
        note.unwrap()

    # unwrap all the hi parunum dot tags
    his = soup.find_all("hi", rend=["paranum", "dot"])
    for hi in his:
        hi.unwrap()

    word_to_add = values['word_to_add'][0]
    ps = soup.find_all("p")

    sutta_sentences = []
    for p in ps:

        if p["rend"] == "subhead":
            source_1 = values["book_to_add"].upper()
            # add space to digtis
            source_1 = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", source_1)
            # add sutta number and name
            source_1 += f".{p.text}"
            # remove from the dot onwards
            source_1 = re.sub(r"\. .+", "", source_1)
            # remove the digits and the dot in sutta name
            sutta_1 = re.sub(r"\d*\. ", "", p.text)

        text = clean_example(p.text)

        if word_to_add in text:
            sentences = nltk.sent_tokenize(text)
            for sentence in sentences:
                if word_to_add in sentence:
                    sutta_sentences += [{
                        "source_1": source_1,
                        "sutta_1": sutta_1,
                        "example_1": sentence}]

    # print(sutta_sentences)

    sentences_list = [sentence['example_1'] for sentence in sutta_sentences]

    layout = [[
        sg.Radio(
            "", "sentence", key=f"{i}", text_color="lightblue",
            pad=((0, 10), 5)),
        sg.Multiline(
            sentences_list[i],
            wrap_lines=True,
            auto_size_text=True,
            size=(100, 2),
            text_color="lightgray",
            no_scrollbar=True,
            )]
        for i in range(len(sentences_list))]

    layout.append([sg.Button("OK")])

    window = sg.Window(
        "Sutta Examples",
        layout,
        resizable=True,
        location=(400, 200))

    event, values = window.read()
    window.close()

    number = 0
    for value in values:
        if values[value] is True:
            number = int(value)

    return sutta_sentences[number]


def clean_example(text):
    text = text.replace("‘", "")
    text = text.replace(" – ", ", ")
    text = text.replace("’", "")
    text = text.replace("…pe॰…", " ... ")
    text = text.replace(";", ",")
    return text
