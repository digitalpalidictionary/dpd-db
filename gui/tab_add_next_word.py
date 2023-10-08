"""Render tab to add the next missing word from a text."""


def make_tab_add_next_word(sg, primary_user):

    tab_add_next_word = [
        [
            sg.Text(
                "select book to add: ", 
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
                visible=not primary_user,
                pad=((10, 0), (20, 20)),
            )
        ],
        [
            sg.Text(
                "select sutta to add: ", 
                pad=((100, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Input(
                key="sutta_to_add",
                size=(10, 1), 
                pad=((0, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Button(
                "Add", 
                key="sutta_to_add_button",
                pad=((10, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_sutta_to_add_button", 
                visible=not primary_user,
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text(
                "select source to add: ", 
                pad=((100, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Input(
                key="source_to_add",
                size=(10, 1), 
                pad=((0, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_add_from_source", 
                visible=not primary_user,
                tooltip="from source show all words from db which do not have this source in sbs examples",
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text("from temp/text.txt ", 
            pad=((100, 0), (0, 20))
            ),
            sg.Button(
                "Add", 
                key="from_txt_to_add_button",
                pad=((10, 0), (0, 20)),
                visible=not primary_user,
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_from_txt_to_add_button", 
                visible=not primary_user,
                pad=((10, 0), (0, 20)),
            ),
            sg.Button(
                "No source", 
                key="dps_from_txt_to_add_considering_source_button",
                tooltip="from txt show all words whcih do not have source in sbs",
                visible=not primary_user,
                pad=((10, 0), (0, 20)),
            )
        ],
        [
            sg.Text("from id-list: ", 
            visible=not primary_user, 
            pad=((100, 0), (0, 20))
            ),
            sg.Button(
                "Add (ru)", 
                key="dps_word_from_id_list_button", 
                visible=not primary_user,
                pad=((10, 0), (0, 20)),
            ),
            sg.Text("filed", 
            visible=not primary_user, 
            pad=((10, 0), (0, 20))
            ),
            sg.Input(
                key="field_for_id_list", 
                visible=not primary_user, 
                tooltip="'field' which need to be updated",
                size=(15, 1), 
                pad=((0, 0), (0, 20)),
            ),
            sg.Text("source", 
            visible=not primary_user, 
            pad=((10, 0), (0, 20))
            ),
            sg.Input(
                key="source_for_id_list", 
                visible=not primary_user, 
                tooltip="'source' of those words (mn107, sn56, etc)",
                size=(7, 1), 
                pad=((0, 0), (0, 20)),
            ),
            sg.Checkbox('has value?', 
            default=False, 
            key="empty_field_id_list_check", 
            visible=not primary_user, 
            pad=((10, 0), (0, 20)), 
            tooltip="does the 'field' currently have any value?"
            ),
        ],
        [
            sg.Text("next word to add: ", 
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
                visible=not primary_user
            ),
            sg.Button(
                "in DPS",
                key="dps_edit_word", 
                size=(19, 1), 
                visible=not primary_user,
                enable_events=True,
            ),
            sg.Button(
                "in DPD",
                key="dpd_edit_word", 
                size=(19, 1), 
                visible=not primary_user,
                enable_events=True,
            ),
        ],
        [
            sg.Button(
                "update sbs_category",
                key="dps_update_word", 
                size=(50, 1), 
                visible=not primary_user,
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
                visible=not primary_user,
                enable_events=True, 
                pad=((100, 0), (0, 0))
            ),
        ],
        [
            sg.Text(
                """kp 1, dhp 2, ud 3, iti 4, snp 5, vv 6, pv 7, th 8, thi 9, apa 10, api 11""",
                size=(50, 1),
                pad=((100, 0), (0, 0))
            )
        ],
        [
            sg.Text(
                """bv 12, cp 13, ja 14, mnd 15, cnd 16, ps 17, mil 18, ne 19, pe 20""",
                size=(50, 1),
                pad=((100, 0), (0, 0))
            )
        ]
    ]

    return tab_add_next_word
