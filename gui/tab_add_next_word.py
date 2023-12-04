"""Render tab to add the next missing word from a text."""


def make_tab_add_next_word(sg, username):

    sutta_codes = """VIN
01. pārājika:\t\tvin1
02. pācittiya:\t\tvin2
03. mahāvagga:\t\tvin3
04. cūḷavagga:\t\tvin4
05. parivāra:\t\tvin5

DN
01. sīlakkhandhavagga:\tdn1
02. mahāvagga:\t\tdn2
03. pāthikavagga:\t\tdn3

MN
01. mūlapaṇṇāsa:\t\tmn1
02. majjhimapaṇṇāsa:\tmn2
03. uparipaṇṇāsa:\t\tmn3

SN
01. sagāthāvaggo:\t\tsn1
02. nidānavaggo:\t\tsn2
03. khandhavaggo:\t\tsn3
04. saḷāyatanavaggo:\tsn4
05. mahāvaggo:\t\tsn5

AN
01. ekakanipāta:\t\tan1
02. dukanipāta:\t\tan2
...
11. ekādasakanipāta:\tan11

KN
01. khuddakapāṭha:\tkn1
02. dhammapada:\t\tkn2
03. udāna:\t\tkn3
04. itivuttaka:\t\tkn4
05. suttanipāta:\t\tkn5
06. vimānavatthu:\t\tkn6
07. petavatthu:\t\tkn7
08. theragāthā:\t\tkn8
09. therīgāthā:\t\tkn9
10. therāpadāna:\t\tkn10
11. therīapadāna:\t\tkn11
12. buddhavaṃsa:\t\tkn12
13. cariyāpiṭaka:\t\tkn13
14. jātaka:\t\tkn14
15. mahāniddesa:\t\tkn15
16. cūḷaniddesa:\t\tkn16
17. paṭisambhidāmagga:\tkn17
18. milindapañha:\t\tkn18
19. nettippakaraṇa:\t\tkn19
20. peṭakopadesa:\t\tkn20
"""

    tab_add_next_word = [
        [
            sg.Text(
                "select book to add:", 
                pad=((100, 0), (20, 20))
            ),
            sg.Input(
                key="book_to_add",
                size=(10, 1), 
                pad=((0, 0), (20, 20)),
            ),
            sg.Button(
                "Add", 
                key="books_to_add_button",
                pad=((10, 0), (20, 20)),
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_books_to_add_button", 
                visible=username == "deva",
                pad=((10, 0), (20, 20))
            ),
            sg.Text(
                "sutta codes",
                size=(50, 1),
                pad=((10, 0), (20, 20)),
                tooltip=sutta_codes
            ),
        ],
        [
            sg.Text(
                "select sutta to add:", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="sutta_to_add",
                size=(10, 1), 
                pad=((0, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add", 
                key="sutta_to_add_button",
                pad=((10, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_sutta_to_add_button", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text(
                "select source to add:", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="source_to_add",
                size=(10, 1), 
                pad=((0, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_add_from_source", 
                visible=username == "deva",
                tooltip="from source show all words from db which do not have this source in sbs examples",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text(
                "from temp/text.txt", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add", 
                key="from_txt_to_add_button",
                pad=((10, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_from_txt_to_add_button", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "No source", 
                key="dps_from_txt_to_add_considering_source_button",
                tooltip="from txt show all words whcih do not have source in sbs",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text("from id-list:", 
            visible=username == "deva", 
            pad=((100, 0), (0, 20))
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_word_from_id_list_button", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Text("filed", 
            visible=username == "deva", 
            pad=((10, 0), (0, 20))
            ),
            sg.Input(
                key="field_for_id_list", 
                visible=username == "deva", 
                tooltip="'field' which need to be updated",
                size=(15, 1), 
                pad=((0, 0), (0, 20)),
            ),
            sg.Text("source", 
            visible=username == "deva", 
            pad=((10, 0), (0, 20))
            ),
            sg.Input(
                key="source_for_id_list", 
                visible=username == "deva", 
                tooltip="'source' of those words (mn107, sn56, etc)",
                size=(7, 1), 
                pad=((0, 0), (0, 20)),
            ),
            sg.Checkbox('has value?', 
            default=False, 
            key="empty_field_id_list_check", 
            visible=username == "deva", 
            pad=((10, 0), (0, 20)), 
            tooltip="does the 'field' currently have any value?"
            ),
        ],
        [
            sg.Text("next word to add:", 
            pad=((100, 0), (0, 0))),
        ],
        [
            sg.Listbox(
                values=[],
                key="word_to_add",
                size=(51, 1), 
                pad=((100, 0), (0, 0)),
                enable_events=True
                ),
            sg.Text(
                "",
                key="words_to_add_length",
                text_color="white"),
        ],
        [
            sg.Text(
                "", pad=((100, 0), (0, 0))
            )
        ],
        [
            sg.Button(
                "sandhi ok",
                key="sandhi_ok",
                size=(50, 1),
                enable_events=True,
                pad=((100, 0), (0, 0))),
        ],
        [
            sg.Button(
                "add word to dictionary",
                key="add_word", 
                size=(50, 1),
                enable_events=True, 
                pad=((100, 0), (0, 0))
            ),
        ],

        [
            sg.Text(
                "edit word",
                key="words_to_add_length",
                text_color="white", 
                pad=((100, 0), (0, 0)), 
                size=(10, 1),
                visible=username == "deva"
            ),
            sg.Button(
                "in DPS",
                key="dps_edit_word", 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
            sg.Button(
                "in DPD",
                key="dpd_edit_word", 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
        ],
        [
            sg.Button(
                "update sbs_category",
                key="dps_update_word", 
                size=(50, 1), 
                visible=username == "deva",
                enable_events=True, 
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Button(
                "sandhi, spelling mistakes and variants",
                key="fix_sandhi",
                size=(50, 1),
                enable_events=True,
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Button(
                "update inflection templates",
                key="update_inflection_templates",
                size=(50, 1),
                enable_events=True,
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Button(
                "remove word from list",
                key="remove_word",
                size=(50, 1),
                enable_events=True,
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Button(
                "save GUI state",
                key="dps_save_gui_state", 
                size=(50, 1), 
                visible=username == "deva",
                enable_events=True, 
                pad=((100, 0), (0, 0))
            ),
        ],
    ]

    return tab_add_next_word
