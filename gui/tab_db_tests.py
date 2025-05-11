"""Render tab to run database tests."""


def make_tab_db_tests(sg):
    LOGIC = [
        "equals",
        "does not equal",
        "contains",
        "contains word",
        "does not contain",
        "does not contain word",
        "is empty",
        "is not empty",
    ]

    tab_db_tests = [
        [
            sg.Text("", size=(15, 1)),
            sg.Button("Run Tests", key="test_db_internal", pad=((0, 10), (10, 10))),
            sg.Button("Stop Tests", key="test_stop", pad=((0, 10), (10, 10))),
            sg.Button("Edit Tests", key="test_edit", pad=((0, 10), (10, 10))),
        ],
        [
            sg.Text("0", size=(15, 1), key="test_number", justification="right"),
            sg.Input("", key="test_name", size=(41, 1), text_color="white"),
            sg.Input("", key="iterations", size=(5, 1)),
        ],
        [
            sg.Text("test 1", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_1", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_1", size=(19, 1)),
            sg.Input("", key="search_string_1", size=(30, 1)),
        ],
        [
            sg.Text("test 2", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_2", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_2", size=(19, 1)),
            sg.Input("", key="search_string_2", size=(30, 1)),
        ],
        [
            sg.Text("test 3", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_3", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_3", size=(19, 1)),
            sg.Input("", key="search_string_3", size=(30, 1)),
        ],
        [
            sg.Text("test 4", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_4", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_4", size=(19, 1)),
            sg.Input("", key="search_string_4", size=(30, 1)),
        ],
        [
            sg.Text("test 5", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_5", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_5", size=(19, 1)),
            sg.Input("", key="search_string_5", size=(30, 1)),
        ],
        [
            sg.Text("test 6", size=(15, 1), justification="right"),
            sg.Input("", key="search_column_6", size=(20, 1)),
            sg.Combo(LOGIC, key="search_sign_6", size=(19, 1)),
            sg.Input("", key="search_string_6", size=(30, 1)),
        ],
        [
            sg.Text("display", size=(15, 1), justification="right"),
            sg.Input("", key="display_1", size=(20, 1)),
            sg.Input("", key="display_2", size=(20, 1)),
            sg.Input("", key="display_3", size=(30, 1)),
        ],
        [
            sg.Text("error col msg", size=(15, 1), justification="right"),
            sg.Input("", key="error_column", size=(20, 1)),
            sg.Combo([], key="exceptions", size=(20, 1), auto_size_text=False),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button("Update Tests", key="test_update", pad=((0, 10), (10, 10))),
            sg.Button("Add New Test", key="test_new", pad=((0, 10), (10, 10))),
            sg.Button("Delete Test", key="test_delete", pad=((0, 10), (10, 10))),
        ],
        [
            sg.Text("", size=(15, 1), justification="right"),
            sg.Text("displaying", pad=0),
            sg.Text("0", key="test_results_redux", text_color="white"),
            sg.Text("of", pad=0),
            sg.Text("0", key="test_results_total", text_color="white"),
            sg.Text("results"),
        ],
        [
            sg.Text("test results", size=(15, 11), justification="right"),
            sg.Table(
                [[]],
                headings=["1", "2", "3"],
                key="test_results",
                size=(70, 11),
                justification="left",
                enable_events=True,
                auto_size_columns=False,
                col_widths=[20, 20, 30],
            ),
        ],
        [
            sg.Text("add exception", size=(15, 1), justification="right"),
            sg.Combo([], key="test_add_exception", size=(30, 1), auto_size_text=False),
            sg.Button("Add", key="test_add_exception_button", size=(5, 1)),
            sg.Input("", key="test_db_query", size=(19, 1)),
            sg.Button("Db Query", key="test_db_query_copy"),
        ],
        [sg.Text("", size=(15, 1)), sg.Button("Next", key="test_next", size=(69, 1))],
    ]

    return tab_db_tests
