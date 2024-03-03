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

    corresponding_quick_links = """
DN
01. sīlakkhandhavagga
02. mahāvagga (>=DN14)
03. pāthikavagga (>=DN24)

SN
01. sagāthāvagg
02. nidānavaggo (>=SN12)
03. khandhavaggo (>=SN22)
04. saḷāyatanavaggo (>=SN35)
05. mahāvaggo (>=SN45)
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
                "dps", 
                key="dps_books_to_add_button",
                tooltip="only in dps db", 
                visible=username == "deva",
                pad=((10, 0), (20, 20))
            ),
            sg.Text(
                "links",
                tooltip=corresponding_quick_links,
                visible=username == "deva",
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
                "sutta: ", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="sutta_to_add",
                tooltip="name of the 'sutta' from which we are adding words",
                size=(20, 1), 
                pad=((0, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Text(
                "source: ", 
                pad=((20, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="source_to_add",
                tooltip="'source' from which we are adding words",
                size=(10, 1), 
                pad=((0, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Text(
                "field: ", 
                pad=((20, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="field_for_id_list", 
                visible=username == "deva", 
                tooltip="'field' which needs to be updated or checked",
                size=(15, 1), 
                pad=((0, 0), (0, 20)),
            ),
        ],
        [
            sg.Button(
                "from sutta", 
                key="sutta_to_add_button",
                tooltip="add words from 'sutta' full db", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Text(
                "dps:", 
                pad=((20, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "from sutta", 
                key="dps_sutta_to_add_button",
                tooltip="add words from 'sutta' only in dps db", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "from source", 
                key="dps_add_from_source",
                tooltip="add words from 'source' only in dps db", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "source in field", 
                key="dps_source_in_field",
                tooltip="add words which has 'source' in sbs_'field'", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text(
                "from temp/text.txt:", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add", 
                key="from_txt_to_add_button",
                tooltip="full db",
                pad=((10, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Text(
                "dps:", 
                pad=((20, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "Add", 
                key="dps_from_txt_to_add_button", 
                tooltip="only in dps db",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "No source", 
                key="dps_from_txt_to_add_considering_source_button",
                tooltip="show all words from text.txt that do not have a source in sbs_source(s), using the 'source to add'",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "No field", 
                key="dps_from_txt_to_add_considering_field_button",
                tooltip="show all words from text.txt that do not have anything in field",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text(
                "Add:", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "from id_to_add", 
                key="dps_word_from_id_list_button", 
                tooltip="show all words from the id_to_add.csv file that have an empty 'field'",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "from tests", 
                key="from_test_to_add_button",
                tooltip="show all words from the current dps_test_1.tsv",
                pad=((10, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Button(
                "from id_temp_list", 
                key="from_temp_id_list_to_add_button",
                tooltip="show all words from the id_temp_list.csv",
                pad=((10, 0), (0, 20)),
                visible=username == "deva",
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
            sg.Button(
                "to simsapa", 
                key="send_sutta_study_request_button",
                tooltip="search word in the simsapa in the 'sutta' + 'source', eg. 'pli-tv-kd1' + '/en/brahmali'", 
                pad=((20, 0), (0, 5)),
                visible=username == "deva",
            ),
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
                "update",
                key="dps_update_word", 
                tooltip="update 'field' with 'source'",
                pad=((100, 0), (0, 0)), 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
            sg.Button(
                "mark",
                key="dps_mark_word",
                tooltip="update 'field' with 'source' + '_', e.g. if 'source' is sn35 'field' will be updated with sn35_", 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
            sg.Text(
                " field",
                tooltip="from 'field' input box",
                text_color="white", 
                size=(10, 1),
                visible=username == "deva"
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
                "pass 2",
                key="pass2_button",
                size=(50, 1),
                enable_events=True,
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Text(
                "load GUI",
                text_color="white", 
                size=(10, 1),
                pad=((100, 0), (0, 0)),
                visible=username == "deva"
            ),
            sg.Button(
                "state (1)",
                key="dps_load_gui_state_1", 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True, 
            ),
            sg.Button(
                "state (2)",
                key="dps_load_gui_state_2", 
                size=(19, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
        ],
        [
            sg.Button(
                "save GUI state (1)",
                key="dps_save_gui_state_1", 
                size=(24, 1), 
                visible=username == "deva",
                enable_events=True, 
                pad=((100, 0), (0, 0))
            ),
            sg.Button(
                "save GUI state (2)",
                key="dps_save_gui_state_2", 
                size=(24, 1), 
                visible=username == "deva",
                enable_events=True,
            ),
        ],
        [
            sg.Text(
                "Added:", 
                pad=((100, 0), (0, 0))
            ),
            sg.Text(
                "0", key="daily_added",
                text_color="white"
            ),
        ],
        [
            sg.Text(
                "Edited: ",
                pad=((100, 0), (0, 0))
            ),
            sg.Text(
                "0", key="daily_edited",
                text_color="white"
            ),
        ],
        [
            sg.Text(
                "Deleted: ",
                pad=((100, 0), (0, 0))
            ),
            sg.Text(
                "0", key="daily_deleted",
                text_color="white"
            ),
        ],
        [
            sg.Text(
                "Checked: ",
                pad=((100, 0), (0, 0))
            ),
            sg.Text(
                "0", key="daily_checked",
                text_color="white"
            ),
        ],
    ]

    return tab_add_next_word
