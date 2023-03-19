def make_tab_add_next_word(sg):

    tab_add_next_word = [
        [
            sg.Text("select book to add: ", pad=((100, 0), (100, 50))),
            sg.Input(
                key="book_to_add",
                size=(10, 1), pad=((0, 0), (100, 50)),
            ),
            sg.Button(
                "Add", key="books_to_add_button",
                pad=((10, 0), (100, 50)),
            )
        ],
        [
            sg.Text("next word to add: ", pad=((100, 0), (0, 0))),
        ],
        [
            sg.Listbox(
                values=[], key="word_to_add",
                size=(51, 1), pad=((100, 0), (0, 0)),
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
                key="add_word", size=(50, 1),
                enable_events=True, pad=((100, 0), (0, 0))
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
    ]

    return tab_add_next_word
