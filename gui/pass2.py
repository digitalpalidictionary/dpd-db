"""Go thru each word and its components in a text to find missing examples."""

import json
import re

import PySimpleGUI as sg

from rich import print
from typing import List, Optional
from sqlalchemy.orm import Session

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup
from functions import load_gui_config
from tools.pali_sort_key import pali_list_sorter


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
            window,
            values: dict[str, str],
            book: str,
        ) -> None:
        self.pth: ProjectPaths = pth
        self.db_session = db_session
        self.main_window = window
        self.values: dict[str, str] = values
        if book:
            self.book: str = book
        else:
            self.book: str = self.get_book()
        self.tried_dict: dict = self.load_tried_dict()
        self.phrase_exceptions_set: set = set(self.tried_dict["phrase_exceptions"])
        self.word_list: List[str] = make_text_list(self.pth, self.book)
        self.word_list_length = len(self.word_list)
        try:
            self.last_word = self.tried_dict["last_word"][self.book]
        except KeyError:
            self.last_word = self.word_list[0]
        self.word_list_index: int = self.word_list.index(self.last_word)
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
        self.exceptions: List[int] = [
            6664, 18055, 18054, 19159, 19162]   # irrelevant words which appear freqently
        self.continue_flag: str = ""
        self.pass2_window: sg.Window
        self.pass2_layout: list
        
    def get_book(self):
        while True:
            book = sg.popup_get_text(
            "which book?", default_text="", location=(400, 400))
            if book:
                break
        return book
            
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
    
    def update_phrase_exceptions(self, phrase_exception: str) -> None:
        self.phrase_exceptions_set.add(phrase_exception)
        self.tried_dict["phrase_exceptions"] = pali_list_sorter(self.phrase_exceptions_set)
        self.save_tried_dict()
    
    def update_last_word(self, wd) -> None:
        self.tried_dict["last_word"][self.book] = wd.word
        self.last_word = wd.word
        self.save_tried_dict()
        self.pass2_window["pass2_last_saved"].update(
            value=f"{self.word_list_index} / {self.word_list_length} {wd.word}")
        self.word_list_index = self.word_list.index(self.last_word)


class WordData():
    def __init__(self, word) -> None:
        self.word: str = word
        self.subword: str
        self.search_pattern: str = fr"(^|\[|\{{|\s)({self.word})(\s|[.,;:!?]|\]|\}}$)"
        self.sutta_examples: List[tuple[str, str, str]]
        self.sutta_examples_count: int 
        self.sutta_examples_total: int
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
        parts = re.split(fr"\b{self.word}\b", self.example)
        self.example_start = parts[0]
        self.example_end = parts[1]

    def update_headword(self, headword):
        self.headword: str = headword

    def update_id(self, id):
        self.id: str = str(id)


def start_from_where_gui(p2d: Pass2Data):
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
                p2d.word_list_index = 0
                p2d.main_window["messages"].update(
                        value="starting from the beginning", text_color="white")
                break
            
            # start from the last saved word
            elif user_input == "2":
                last_word = p2d.tried_dict["last_word"][p2d.book]
                try:
                    p2d.word_list_index = p2d.word_list.index(last_word)
                    p2d.main_window["messages"].update(
                        value=f"starting from the last saved word: {last_word}",
                        text_color="white")
                    break
                except ValueError:
                    sg.popup(f"{last_word} is not in the word list")
                    start_from_where_gui(p2d)
            
            # start from a specific word
            elif user_input:
                try:
                    p2d.word_list_index = p2d.word_list.index(user_input)
                    p2d.main_window["messages"].update(
                        value=f"starting from {user_input}",
                        text_color="white")
                    break
                except ValueError:
                    sg.popup(f"{user_input} is not in the word list")
                    start_from_where_gui(p2d)
    
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
            sg.Text("examples", size = (15,1)),
            sg.Text("", key="pass2_examples_count", size=(50,1))    
        ],
        [
            sg.Text("source", size = (15,1)),
            sg.Multiline(
                "", key="pass2_source", no_scrollbar=True, size=(50,1),
                enable_events=True, autoscroll=False, auto_refresh=True)    
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
                no_scrollbar=True),
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
            sg.Text("phrase exception", size = (15,1)),
            sg.Input(
                "", key="pass2_phrase_exception", size=(46,1)),
            sg.Button("Add", key="pass2_phrase_exception_button")
        ],
        [
            sg.Text("", size = (15,1)),
        ],
        [
            sg.Text("", size = (15,1)),
            sg.Button("Start", key="pass2_start"),
            sg.Button("Yes", key="pass2_yes"),
            sg.Button("No", key="pass2_no"),
            sg.Button("No All", key="pass2_no_all"),
            sg.Button("Pass", key="pass2_pass"),
            sg.Button("Skip", key="pass2_skip"),
            sg.Button("Exit", key="pass2_exit")
        ],
        [
            sg.Text("", size = (15,1)),
        ],
        [
            sg.Text("last word", size = (15,1)),
            sg.Multiline("", key="pass2_last_saved", no_scrollbar=True, size=(50,1)),
        ],

    ]

    screen_width, screen_height = sg.Window.get_screen_size()
    width = int(screen_width * 0.60)
    height = screen_height

    pass2_window = sg.Window(
        "Pass2",
        pass2_layout,
        size=(width, height),
        finalize=True,
        resizable=True)
    p2d.pass2_window = pass2_window
    p2d.pass2_layout = pass2_layout



def pass2_gui(p2d: Pass2Data) -> tuple[Pass2Data, WordData]:
    """GUI for pass2"""

    window_options(p2d)

    for index, word in enumerate(p2d.word_list):
        
        # reset the flag
        p2d.continue_flag = ""
        
        # dont bother with words before the last index
        if index < p2d.word_list_index:
            continue

        wd = WordData(word)

        # update the gui
        p2d.pass2_window["pass2_index"].update(value=f"{index} / {p2d.word_list_length}")
        p2d.pass2_window["pass2_word"].update(value=word)
        p2d.pass2_window.refresh()

        sutta_examples = find_source_sutta_example(
            p2d.pth, p2d.book, wd.search_pattern)
        
        if sutta_examples:
            wd.sutta_examples = sutta_examples
            wd.sutta_examples_total = len(sutta_examples)
            
            for count, sutta_example in enumerate(sutta_examples):
                wd.sutta_examples_count = count
                wd.update_sutta_example(list(sutta_example))

                if is_phrase_exception(p2d, wd):
                    continue 

                headwords_list = get_headwords(p2d, word)
                if headwords_list:
                    check_example_headword(p2d, wd, headwords_list)
                    if p2d.continue_flag == "yes":
                        update_main_window(p2d, wd)
                        return p2d, wd
                    elif p2d.continue_flag == "exit":
                        return p2d, wd
                    elif p2d.continue_flag == "skip":
                        break

                # check for words in deconstructions with no examples
                headwords_list = get_deconstruction_headwords(p2d, word)
                if headwords_list:
                    check_example_headword(p2d, wd, headwords_list)
                    if p2d.continue_flag == "yes":
                        update_main_window(p2d, wd)
                        return p2d, wd
                    elif p2d.continue_flag == "exit":
                        return p2d, wd
                    elif p2d.continue_flag == "skip":
                        break

            p2d.update_last_word(wd)
        
        else:
            print(f"[red]{'-'*50}")
            print(f"[red]no sutta example found for [bright_red]{word}")
    
    return p2d, wd


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

            if p2d.continue_flag == "yes":
                return
            elif p2d.continue_flag == "exit":
                return
            elif p2d.continue_flag == "skip":
                break
            if is_phrase_exception(p2d, wd):
                break 

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

                    # dont go to the gui window if no_all
                    if p2d.continue_flag == "no_all":
                        p2d.update_tried_dict(wd)
                    else:
                        choose_route(p2d, wd, dpd_headword)

                    if p2d.continue_flag in ["exit", "yes"]:
                        return
            
            else:
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

    p2d.pass2_window["pass2_word"].update(value=wd.word)
    p2d.pass2_window["pass2_source"].update(value=wd.source)
    p2d.pass2_window["pass2_examples_count"].update(
        value=f"{wd.sutta_examples_count+1} / {wd.sutta_examples_total}")
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
    
    open_in_goldendict(headword.lemma_1)
    update_gui(p2d, wd, headword)
    p2d.pass2_window.refresh()

    while True:
        event, values = p2d.pass2_window.read() #type:ignore
        print(event)
        print(values)
        
        if event == sg.WINDOW_CLOSED or event == "pass2_exit":
            p2d.pass2_window.close()
            p2d.continue_flag = "exit"
            break
        elif event == "pass2_start":
            pass
        elif event == "pass2_yes":
            p2d.continue_flag = "yes"
            p2d.pass2_window.close()
            break
        elif event == "pass2_no":
            p2d.continue_flag = "no"
            p2d.update_tried_dict(wd)
            break
        elif event == "pass2_no_all":
            p2d.continue_flag = "no_all"
            p2d.update_tried_dict(wd)
            break
        elif event == "pass2_pass":
            p2d.continue_flag = "pass"
            break
        elif event == "pass2_skip":
            p2d.continue_flag = "skip"
            break
        elif event == "pass2_phrase_exception_button":
            p2d.update_phrase_exceptions(values["pass2_phrase_exception"])
            p2d.pass2_window["pass2_phrase_exception"].update(value="")
            p2d.continue_flag = "phrase_exception"
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
                if p2d.continue_flag == "yes":
                    update_main_window(p2d, wd)
                    return
                elif p2d.continue_flag == "exit":
                    return
                elif p2d.continue_flag == "skip":
                    break
    

def make_text_list(
        pth: ProjectPaths,
        book: str
        ) -> List[str]:
    cst_text_list = make_cst_text_list(pth, [book])
    sc_text_list = make_sc_text_list(pth, [book])
    
    # reverse for better results (temporary)
    # cst_text_list.reverse()
    # sc_text_list.reverse()
    
    full_text_list = cst_text_list + sc_text_list

    # sp_mistakes_list = make_sp_mistakes_list(pth)
    # variant_list = make_variant_list(pth)

    text_set = set(cst_text_list) | set(sc_text_list)
    # text_set = text_set - set(sp_mistakes_list)
    # text_set = text_set - set(variant_list)
    return sorted(text_set, key=lambda x: full_text_list.index(x))


def update_main_window(p2d: Pass2Data, wd: WordData):
    headword = p2d.db_session \
        .query(DpdHeadwords) \
        .filter(DpdHeadwords.id == wd.id) \
        .first()
    if headword:
        attrs = headword.__dict__
        for key in attrs.keys():
            if key in p2d.values:
                p2d.main_window[key].update(attrs[key])

        # move the commentary to example2
        if headword.example_1:
            p2d.main_window["source_2"].update(value=headword.source_1)
            p2d.main_window["sutta_2"].update(value=headword.sutta_1)
            p2d.main_window["example_2"].update(value=headword.example_1)

        # update example 1, commentary and bold
        p2d.main_window["source_1"].update(value=wd.source)
        p2d.main_window["sutta_1"].update(value=wd.sutta)
        p2d.main_window["example_1"].update(value=wd.example)
        p2d.main_window["bold_1"].update(value=wd.word)
        p2d.main_window["search_for"].update(wd.word[:-1])


def is_phrase_exception(p2d, wd):
    for phrase_exception in p2d.phrase_exceptions_set:
        if (
            wd.word in phrase_exception
            and phrase_exception in wd.example
        ):
            return True
    return False

if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    window = sg.Window("", [])  # just a placeholder
    p2d = Pass2Data(pth, db_session, window, {}, "mn2")
    pass2_gui(p2d)
