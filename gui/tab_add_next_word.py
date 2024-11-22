"""Render tab to add the next missing word from a text."""
from gui.tooltips import sutta_codes

def make_tab_add_next_word(sg, username):


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
            sg.Button(
                "No source", 
                key="dps_books_to_add_considering_source_button",
                tooltip="words from book does not have source in any sources", 
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
                "sutta: ", 
                pad=((100, 0), (0, 20)),
                visible=username == "deva",
            ),
            sg.Input(
                key="sutta_to_add",
                tooltip="The name of the 'sutta' from which we are adding words.",
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
                tooltip="The 'source' from which we are adding words.",
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
                tooltip="The 'field' that requires updating or verification.",
                size=(15, 1), 
                pad=((0, 0), (0, 20)),
            ),
        ],
        [
            sg.Button(
                "from sutta", 
                key="sutta_to_add_button",
                tooltip="Add words from 'sutta' full db", 
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
                tooltip="Add words from 'sutta' only in dps db", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "from source", 
                key="dps_add_from_source",
                tooltip="Add words from 'source' only in dps db", 
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "source in field", 
                key="dps_source_in_field",
                tooltip="Add words that have 'source' in the corresponding 'field'", 
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
                tooltip="Display all words from text.txt that don't have a 'source' in any sources",
                visible=username == "deva",
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "No field", 
                key="dps_from_txt_to_add_considering_field_button",
                tooltip="Display all words from text.txt where the 'field' is empty.",
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
                tooltip="Display words from id_to_add.csv where 'field' is empty if 'source' is empty, or where 'field' matches 'source' if 'source' is not empty.",
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
                text_color="white", 
                size=(5, 1),
                pad=((100, 0), (0, 0)),
                visible=username == "deva"
            ),
            sg.Button(
                "load GUI state (1)",
                key="dps_load_gui_state_1", 
                size=(19, 1), 
                visible=username == "deva",
                button_color=("white", "#00008B"),
                enable_events=True, 
            ),
            sg.Button(
                "load GUI state (2)",
                key="dps_load_gui_state_2", 
                size=(19, 1), 
                visible=username == "deva",
                button_color=("white", "#00008B"),
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
