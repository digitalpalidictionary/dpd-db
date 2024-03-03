"""Go thru each word and its components in a text to find missing examples."""

import json
import pyperclip
import re

import PySimpleGUI as sg

from rich import print
from typing import List, Optional
from sqlalchemy.orm import Session

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup
from functions import load_gui_config


from tools.paths import ProjectPaths

from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_sc_text_list
from tools.source_sutta_example import find_source_sutta_example
from tools.meaning_construction import make_meaning
from tools.goldedict_tools import open_in_goldendict


class Pass2Data():
    def __init__(
            self,
            pth: ProjectPaths,
            db_session: Session,
            book: str
        ) -> None:
        self.pth: ProjectPaths = pth
        self.db_session = db_session
        self.book = book
        self.tried_dict: dict = self.load_tried_dict()
        self.word_list: List[str] = make_text_list(self.pth, self.book)
        self.word_list_length = len(self.word_list)
        self.commentary_list: List[str] = [
            "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
            "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
            "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
            "NIDD1a", "NIDD2a", "PMa", "NPa", "NPt", "PTP",
            "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
            "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
            "VISM", "VISMa",
            "PRS", "SDM", "SPM",
            "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
            "buddhavandana"
            ]
        self.exceptions: List[int] = [6664]
        self.continue_flag: bool = True
        self.pass2_window: sg.Window
        self.pass2_layout: list
        
        
    def load_tried_dict(self):
        try:
            with open(self.pth.pass2_checked_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {self.book: dict()}

    def save_tried_dict(self) -> None:
        with open(self.pth.pass2_checked_path, "w") as f:
            json.dump(self.tried_dict, f, ensure_ascii=False, indent=2)
    
    def update_tried_dict(self, wd) -> None:
        if self.book not in self.tried_dict:
            self.tried_dict[self.book] = {}
        if wd.word not in self.tried_dict[self.book]:
            self.tried_dict[self.book][wd.word] = {}
        if wd.id not in self.tried_dict[self.book][wd.word]:
            self.tried_dict[self.book][wd.word][wd.id] = []
        self.tried_dict[self.book][wd.word][wd.id].append(wd.sutta_example)
        self.save_tried_dict()
    
    def update_last_word(self, wd) -> None:
        self.tried_dict["last_word"] = wd.word
        self.save_tried_dict()
        index = self.word_list.index(wd.word)
        total = len(self.word_list)
        counter = f"{index+1} / {total+12}"
        print("-"*50)
        print(f"[cyan]{counter:<12}[green]last word saved: [white]{wd.word}")


class WordData():
    def __init__(self, word) -> None:
        self.word: str = word
        self.subword: str
        self.search_pattern: str = fr"(^|\[|\{{|\s)({self.word})(\s|[.,;:!?]|\]|\}}$)"
        self.sutta_example: List[str]
        self.source: str
        self.sutta: str
        self.example: str
        self.example_print: str
        self.headword: str
        self.id: str
    
    def update_sutta_example(self, sutta_example):
        self.sutta_example = sutta_example
        self.source = sutta_example[0]
        self.sutta = sutta_example[1]
        self.example = sutta_example[2]
        parts = self.example.split(self.word, 1)
        self.example_start = parts[0]
        self.example_end = parts[1]

    def _example_to_print(self):
        self.example_print: str = self.example\
            .replace("[", "{")\
            .replace("]", "}")
        self.replace: str = fr"\1[cyan]{self.word}[/cyan]\3"
        self.example_print: str = re.sub(
            self.search_pattern,
            self.replace,
            self.example_print)

    def update_headword(self, headword):
        self.headword: str = headword

    def update_id(self, id):
        self.id: str = str(id)


def start_from_where_gui(window, p2d, flags):
    """
    Where to start running pass2 from?
    1. Start from the beginning
    2. or from the last saved word
    3. or from a specific word.
    """

    layout = [
        [sg.Text("1. Start from the beginning")],
        [sg.Text("2. Start from the last saved word")],
        [sg.Text("OR enter a specific word to start from")],
        [
            sg.Input(key="user_input", visible=True, size=(20, 1)), 
            sg.Button("OK", key='OK')
        ],
    ]

    start_window: sg.Window = sg.Window(
        "Pass2",
        layout, 
        location=(400, 400))

    while True:
        event, values = start_window.read() #type:ignore
        if event == sg.WINDOW_CLOSED:
            break
        elif event == "OK":
            user_input = values["user_input"]
            
            # start from the beginning
            if user_input == "1":
                flags.pass2_start = False
                window["messages"].update(
                        value="starting from the beginning", text_color="white")
                break
            
            # start from the last saved word
            elif user_input == "2":
                last_word = p2d.tried_dict["last_word"]
                try:
                    index = p2d.word_list.index(last_word)
                    p2d.word_list = p2d.word_list[index:]
                    flags.pass2_start = False
                    window["messages"].update(
                        value=f"starting from the last saved word: {last_word}",
                        text_color="white")
                    break
                except ValueError:
                    sg.popup(f"{last_word} is not in the word list")
                    start_from_where_gui(window, p2d, flags)
            
            # start from a specific word
            elif user_input:
                try:
                    index = p2d.word_list.index(user_input)
                    p2d.word_list = p2d.word_list[index:]
                    flags.pass2_start = False
                    window["messages"].update(
                        value=f"starting from {user_input}",
                        text_color="white")
                    break
                except ValueError:
                    sg.popup(f"{user_input} is not in the word list")
                    start_from_where_gui(start_window, p2d, flags)
                
    start_window.close()


def window_options(p2d: Pass2Data):

    config = load_gui_config()
    # Create the window
    sg.theme(config["theme"])
    sg.set_options(
        font=config["font"],
        input_text_color=config["input_text_color"],
        text_color=config["text_color"],
        window_location=config["window_location"],
        element_padding=config["element_padding"],
        margins=config["margins"],
    )

    pass2_layout = [
        [
            sg.Text("index", size = (15,1)),
            sg.Text("", key="pass2_index", size=(50,1))    
        ],
        [
            sg.Text("word", size = (15,1)),
            sg.Text("", key="pass2_word", size=(50,1))    
        ],
        [
            sg.Text("", size = (15,1)),
        ],
        [
            sg.Text("source", size = (15,1)),
            sg.Multiline("", key="pass2_source", no_scrollbar=True, size=(50,1))    
        ],
        [
            sg.Text("sutta", size = (15,1)),
            sg.Multiline("", key="pass2_sutta", no_scrollbar=True, size=(50,1))    
        ],
        [
            sg.Text("example", size = (15,1)),
            sg.Multiline(
                "",
                key="pass2_example",
                size = (50,10),
                autoscroll=False,
                focus=True),
        ],
        [
            sg.Text("", size = (15,1)),
        ],
        [
            sg.Text("id", size = (15,1)),
            sg.Multiline("", key="pass2_id", no_scrollbar=True, size=(50,1))    
        ],
        [
            sg.Text("headword", size = (15,1)),
            sg.Multiline(
                "", key="pass2_headword", no_scrollbar=True, size=(50,1),
                text_color="dodgerblue")    
        ],

        [
            sg.Text("pos", size = (15,1)),
            sg.Multiline("", key="pass2_pos", no_scrollbar=True, size=(50,1)),
        ],
        [
            sg.Text("meaning", size = (15,1)),
            sg.Multiline(
                "", key="pass2_meaning", no_scrollbar=False, size=(50,1),
                text_color="dodgerblue"),
        ],
        [
            sg.Text("", size = (15,1)),
        ],
        [
            sg.Text("", size = (15,1)),
            sg.Button("Start", key="pass2_start"),
            sg.Button("Yes", key="pass2_yes"),
            sg.Button("No", key="pass2_no"),
            sg.Button("Pass", key="pass2_pass"),
            sg.Button("Exit", key="pass2_exit")
        
        ]
    ]

    screen_width, screen_height = sg.Window.get_screen_size()
    width = int(screen_width * 0.60)
    height = screen_height

    pass2_window = sg.Window(
        "Pass2",
        pass2_layout,
        size=(width, height),
        finalize=True)
    p2d.pass2_window = pass2_window
    p2d.pass2_layout = pass2_layout



def pass2_gui(p2d: Pass2Data):
    """GUI for pass2"""

    window_options(p2d)

    for index, word in enumerate(p2d.word_list):
        wd = WordData(word)

        if p2d.continue_flag == False:
            return wd
        
        p2d.pass2_window["pass2_index"].update(value=f"{index} / {p2d.word_list_length}")
        p2d.pass2_window["pass2_word"].update(value=word)
        p2d.pass2_window.refresh()

        sutta_examples = find_source_sutta_example(
            p2d.pth, p2d.book, wd.search_pattern)
        
        if sutta_examples:
            for sutta_example in sutta_examples:
                wd.update_sutta_example(list(sutta_example))
                headwords_list = get_headwords(p2d, word)
                if headwords_list:
                    check_example_headword(p2d, wd, headwords_list)
                    if p2d.continue_flag == False:
                        return wd

                # check for words in deconstructions with no examples
                headwords_list = get_deconstruction_headwords(p2d, word)
                if headwords_list:
                    check_example_headword(p2d, wd, headwords_list)
                    if p2d.continue_flag == False:
                        return wd
                
            p2d.update_last_word(wd)
        
        else:
            print(f"[red]{'-'*50}")
            print(f"[red]no sutta example found for [bright_red]{word}")


def get_headwords(        
        p2d:Pass2Data,
        word_to_find: str
    ) -> List[int] | None:
    
    """Get the headwords of an inflected word."""
    results: Optional[Lookup]
    results = p2d.db_session \
        .query(Lookup) \
        .filter_by(lookup_key=word_to_find) \
        .first()
    if results and results.headwords:
        return results.headwords_unpack
    else:
        return None


def get_deconstruction_headwords(
        p2d: Pass2Data,
        word_to_find: str
    ) -> list[int] | None:

    """Lookup in deconstructions and return a list of headword ids."""

    results = p2d.db_session \
        .query(Lookup) \
        .filter_by(lookup_key=word_to_find) \
        .first()
    if results and results.deconstructor:
        deconstructions = results.deconstructor_unpack
        
        inflections = set()
        for d in deconstructions:
            inflections.update(d.split(" + "))
        
        headword_id_list: set[int] = set()
        for inflection in inflections:
            results = p2d.db_session \
                .query(Lookup) \
                .filter_by(lookup_key=inflection) \
                .first()
            if results:
                headword_id_list.update(results.headwords_unpack)
        return sorted(headword_id_list)
    else:
        return None


def check_example_headword(
        p2d: Pass2Data,
        wd: WordData,
        id_list: List[int]
    ) -> None:

    if id_list:
        for id in id_list:
            wd.update_id(id)
            dpd_headword = p2d.db_session \
                .query(DpdHeadwords) \
                .filter_by(id=wd.id) \
                .first()
            
            if dpd_headword:
                wd.update_headword(dpd_headword.lemma_1)

                # test not in tried_dict
                test1 = wd.sutta_example not in p2d.tried_dict \
                        .get(p2d.book, {}) \
                        .get(wd.word, {}) \
                        .get(wd.id, [])
                
                # test has no meaning and example
                test2 = has_no_meaning_or_example(dpd_headword)

                # test if can replace a commentary example 
                test3 = (
                    any(
                        item in dpd_headword.source_1
                        for item in p2d.commentary_list)
                    ) and "(gram)" not in dpd_headword.meaning_1
                
                test4 = dpd_headword.id not in p2d.exceptions

                if test1 and (test2 or test3) and test4:
                    choose_route(p2d, wd, dpd_headword)
                    if p2d.continue_flag == False:
                        return wd
            
            else:
                # if "√" not in id:
                    id = DpdHeadwords()
                    print(id_list)
                    print(f"[red]{id} not found")

            if id and dpd_headword:
                test_words_in_construction(p2d, wd, dpd_headword)
                

def has_no_meaning_or_example(
        headword: DpdHeadwords
    ) -> bool:
    """"Test the pali_word"""

    # needs an example
    condition_1 = headword and not headword.example_1

    # needs meaning_1
    condition_2 = headword and not headword.meaning_1

    if condition_1 or condition_2:
        return True
    else:
        return False
                
   

def update_gui(
        p2d: Pass2Data,
        wd: WordData,
        headword: DpdHeadwords
    ):
    """
    Update the gui with word info.
    """
    open_in_goldendict(headword.lemma_1)

    p2d.pass2_window["pass2_word"].update(value=wd.word)
    p2d.pass2_window["pass2_source"].update(value=wd.source)
    p2d.pass2_window["pass2_sutta"].update(value=wd.sutta)

    p2d.pass2_window["pass2_example"].update(value="")
    p2d.pass2_window["pass2_example"].print(wd.example_start, text_color="darkgray", end="") #type:ignore
    p2d.pass2_window["pass2_example"].print(wd.word, text_color="dodgerblue", end="")        #type:ignore
    p2d.pass2_window["pass2_example"].print(wd.example_end, text_color="darkgray", end="")   #type:ignore

    p2d.pass2_window["pass2_id"].update(value=headword.id)
    p2d.pass2_window["pass2_headword"].update(value=headword.lemma_1)
    p2d.pass2_window["pass2_pos"].update(value=headword.pos)
    p2d.pass2_window["pass2_meaning"].update(value=f"{make_meaning(headword)}")
    p2d.pass2_window.refresh()


def clear_gui(p2d: Pass2Data):
    p2d.pass2_window["pass2_word"].update(value="")
    p2d.pass2_window["pass2_source"].update(value="")
    p2d.pass2_window["pass2_sutta"].update(value="")

    p2d.pass2_window["pass2_example"].update(value="")

    p2d.pass2_window["pass2_id"].update(value="")
    p2d.pass2_window["pass2_headword"].update(value="")
    p2d.pass2_window["pass2_pos"].update(value="")
    p2d.pass2_window["pass2_meaning"].update(value="")
    p2d.pass2_window.refresh()



def choose_route(
        p2d: Pass2Data,
        wd:WordData,
        headword: DpdHeadwords
    ):
    """
    Handle the user response and take necessary action.
    """
    
    while True:
        event, values = p2d.pass2_window.read() #type:ignore
        update_gui(p2d, wd, headword)
        print(event)
        print(values)
        if event == sg.WINDOW_CLOSED or event == "pass2_exit":
            p2d.pass2_window.close()
            p2d.continue_flag = False
            break
        if event == "pass2_start":
            pass
        if event == "pass2_yes":
            p2d.continue_flag = False
            p2d.pass2_window.close()
            pyperclip.copy(headword.id)
            break
        if event == "pass2_no":
            p2d.continue_flag = True
            p2d.update_tried_dict(wd)
            break
        if event == "pass2_pass":
            p2d.continue_flag = True
            break


def test_words_in_construction(
        p2d: Pass2Data,
        wd: WordData,
        dpd_headword: DpdHeadwords
    ) -> None:

    if (
        dpd_headword
        and not dpd_headword.root_key
        and dpd_headword.construction
        and re.findall(r"\bcomp\b", dpd_headword.grammar)
    ):
        construction_clean = re.sub(
            r" >.+?\+ ", " + ", dpd_headword.construction)
        construction_parts = construction_clean.split(" + ")
        for word in construction_parts:
            headwords_list = get_headwords(p2d, word)
            if headwords_list:
                check_example_headword(p2d, wd, headwords_list)
    

def make_text_list(
        pth: ProjectPaths,
        book: str
        ) -> List[str]:
    cst_text_list = make_cst_text_list(pth, [book])
    sc_text_list = make_sc_text_list(pth, [book])
    full_text_list = cst_text_list + sc_text_list

    # sp_mistakes_list = make_sp_mistakes_list(pth)
    # variant_list = make_variant_list(pth)

    text_set = set(cst_text_list) | set(sc_text_list)
    # text_set = text_set - set(sp_mistakes_list)
    # text_set = text_set - set(variant_list)
    return sorted(text_set, key=lambda x: full_text_list.index(x))


if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    p2d = Pass2Data(pth, db_session, "mn1")
    pass2_gui(p2d)
