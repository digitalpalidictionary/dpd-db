import PySimpleGUI as sg

# this is the pysimplegui reference which has all the details for each element
# https://www.pysimplegui.org/en/latest/call%20reference/#text-element

# i found these youtube tutorials useful
# https://www.youtube.com/watch?v=-_z2RPAH0Qk&pp=ygULcHlzaW1wbGVndWk%3D
# https://www.youtube.com/watch?v=a3AeM1GZNTk&list=PLqC1Lik2CUiiNhSuk5UdWpHmBKPEryrSo


def main():

    # this controls the colors and font

    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="darkgray",
        text_color="#00bfff",
        window_location=(0, 0),
        element_padding=(0, 3),
        margins=(0, 0),
    )

    # examples of tooltips and lists 

    example_tooltip = "this is an example tooltip"
    listylist = ["it's", "easy", "to", "make", "a", "gui"]

    # this is your main layout to edit

    deva_layout = [
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                "",
                key="fetch_from_db",
                size=(45, 1),
                enable_events=True,
                tooltip=example_tooltip),
            sg.Button(
                "Get word from Db",
                font=(None, 13)
            )
        ],
        [
            sg.Text("dpd info 1", size=(15, 1, )),
            sg.Text(
                "here you can show id and pali1",
                key="dpd_line_1", size=(50, 1),
                tooltip=example_tooltip),
        ],
        [
            sg.Text("dpd info 2", size=(15, 1)),
            sg.Text(
                "maybe the meaning and literal meaning goes here",
                key="dpd_line_2",
                size=(50, 1),
                tooltip=example_tooltip),
        ],
        [
            sg.Text("dpd info 3", size=(15, 1)),
            sg.Text(
                "and whatever other dpd info you want to display",
                key="dpd_line_3",
                size=(50, 1),
                tooltip=example_tooltip),
        ],
        [
            sg.Text("dpd info 4", size=(15, 1)),
            sg.Text(
                "as many lines as you want, and as detailed as you want",
                key="dpd_line_4",
                size=(50, 1),
                tooltip=example_tooltip),
        ],
        [
            sg.Text("radio button", size=(15, 1)),
            sg.Radio(
                "all", "group1",
                key="show_fields_all",
                enable_events=True,
                tooltip=example_tooltip),
            sg.Radio(
                "root", "group1",
                key="show_fields_root",
                enable_events=True,
                tooltip=example_tooltip),
            sg.Radio(
                "compound", "group1",
                key="show_fields_compound",
                enable_events=True,
                tooltip=example_tooltip),
            sg.Radio(
                "word", "group1",
                key="show_fields_word",
                enable_events=True,
                tooltip=example_tooltip),
            sg.Text(
                "", key="show_fields_error", size=(50, 1), text_color="red")
        ],
        [
            # make the key names the same as the
            # name of the field in db

            sg.Text("russian", size=(15, 1)),
            sg.Input(
                "some input goes here",
                key="same_as_the_db_field_name",
                size=(50, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("russian lit", size=(15, 1)),
            sg.Input(
                "",
                key="same_as_the_db_field_name",
                size=(50, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("pos", size=(15, 1)),
            sg.Combo(
                listylist,
                key="listylist",
                size=(7, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
            sg.Button(
                "Buttons",
                key="buttons",
                font=(None, 13)),
            sg.Button(
                "Which",
                key="which",
                font=(None, 13)),
            sg.Button(
                "Do Stuff",
                key="do_stuff",
                font=(None, 13)),
        ],
        [
            sg.Text("etc", size=(15, 1)),
            sg.Input("etc", key="etc", enable_events=True)
        ]
        ]

    # this controls the layout of your tabs

    tab_devatab = [
        [
            sg.Column(
                deva_layout,
                scrollable=True,
                vertical_scroll_only=True,
                expand_y=True,
                expand_x=True,
                size=(None, 850),
            ),
        ],
        [
            sg.HSep(),
        ],
        # here you can put as many buttons functions as you want
        # or just delete
        [
            sg.Button("Copy"),
            sg.Input(
                key="word_to_copy",
                size=(15, 1),
                enable_events=True,
            ),
            sg.Button("Edit", key="edit_button"),
            sg.Button("Test", key="test_internal"),
            sg.Button("Add to db", key="add_word_to_db"),
            sg.Button("Update", key="update_word"),
            sg.Button("Save", key="save_state"),
            sg.Button("Delete", key="delete_button"),
        ],
        [
            sg.Button("Debug"),
            sg.Button("Stash", key="stash"),
            sg.Button("Unstash", key="unstash"),
            sg.Button("Summary", key="summary"),
            sg.Button("Open tests", key="open_tests"),
            sg.Button("Update Sandhi", key="update_sandhi"),
            sg.Button("Clear"),
            sg.Button("Close"),
        ]
    ]

    # this controls the layout of all the tabs

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", [[]], key="tab_add_next_word"),
            sg.Tab("Add Word", [[]], key="tab_add_word"),
            sg.Tab("Fix Sandhi", [[]], key="tab_fix_sandhi"),
            sg.Tab("Test db", [[]], key="tab_db_tests"),
            sg.Tab("Devatab", tab_devatab, key="devamitta_tab")
        ]],
        key="tabgroup",
        enable_events=True,
        size=(None, None)
    )

    # and this is the layout of the whole window

    layout = [
        [tab_group],
        [sg.Text(
            "svāgataṃ", key="messages", text_color="white", font=(None, 12))]
    ]

    #  window size and position

    window = sg.Window(
        'Devatab',
        layout,
        resizable=True,
        size=(1280, 1080),
        finalize=True,
        )

    # this is the while loop where the logic goes
    # for now it just prints out events and values when they change

    while True:
        event, values = window.read()

        if event:
            print(f"{event}")
            print(f"{values}")


if __name__ == "__main__":
    main()