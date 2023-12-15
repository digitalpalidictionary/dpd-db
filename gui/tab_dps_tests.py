"""Render tab to run database tests for dps."""


def make_tab_dps_tests(sg):

    LOGIC = [
        "equals",
        "does not equal",
        "contains",
        "contains word",
        "does not contain",
        "does not contain word",
        "is empty",
        "is not empty"]

    tab_dps_tests = [
        [
            sg.Text(
                "DPS TEST TAB", size=(15, 1), justification="right", text_color="yellow"),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Run Tests", key="dps_test_db_internal"),
            sg.Button(
                "Stop Tests", key="dps_test_stop"),
            sg.Button(
                "Edit Tests", key="dps_test_edit"),
        ],
        [
            sg.Text(
                "0", size=(15, 1), key="dps_test_number", justification="right"),
            sg.Input(
                "", key="dps_test_name", size=(41, 1), text_color="white"),
            sg.Input("", key="dps_test_iterations", size=(5, 1)),
        ],
        [
            sg.Text("test 1", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_1", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_1", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_1", size=(30, 1)),
        ],
        [
            sg.Text("test 2", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_2", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_2", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_2", size=(30, 1)),
        ],
        [
            sg.Text("test 3", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_3", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_3", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_3", size=(30, 1)),
        ],
        [
            sg.Text("test 4", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_4", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_4", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_4", size=(30, 1)),
        ],
        [
            sg.Text("test 5", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_5", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_5", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_5", size=(30, 1)),
        ],
        [
            sg.Text("test 6", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_search_column_6", size=(20, 1)),
            sg.Combo(LOGIC, key="dps_test_search_sign_6", size=(19, 1)),
            sg.Input("", key="dps_test_search_string_6", size=(30, 1)),
        ],
        [
            sg.Text("display", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_display_1", size=(20, 1)),
            sg.Input("", key="dps_test_display_2", size=(20, 1)),
            sg.Input("", key="dps_test_display_3", size=(30, 1)),
        ],
        [
            sg.Text("error col msg", size=(15, 1), justification="right"),
            sg.Input("", key="dps_test_error_column", size=(20, 1)),
            sg.Combo(
                [], key="dps_test_exceptions", size=(20, 1), auto_size_text=False),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button("Update Tests", key="dps_test_update"),
            sg.Button("Add New Test", key="dps_test_new"),
            sg.Button("Delete Test", key="dps_test_delete"),
        ],
        [
            sg.Text("", size=(15, 1), justification="right"),
            sg.Text("displaying", pad=0),
            sg.Text(
                "0", key="dps_test_results_redux", text_color="white"),
            sg.Text("of", pad=0),
            sg.Text(
                "0", key="dps_test_results_total", text_color="white"),
            sg.Text("results")
        ],
        [
            sg.Text("results", size=(6, 11), justification="left"),
            sg.Table(
                [[]], headings=["1", "2", "3"], key="dps_test_results",
                size=(70, 11), justification="left", enable_events=True,
                auto_size_columns=False, col_widths=[20, 20, 30])
        ],
        [
            sg.Text("except:", size=(6, 1), justification="left"),
            sg.Combo(
                [], key="dps_test_add_exception",
                size=(30, 1), auto_size_text=False),
            sg.Button("Add", key="dps_test_add_exception_button", size=(5, 1)),
            sg.Input("", key="dps_test_db_query", size=(19, 1)),
            sg.Button("Db Query", key="dps_test_db_query_copy"),
            sg.Button("Save list", key="dps_test_save_list", tooltip="save current list of words in dps_test_1.tsv",),
        ],
        [
            sg.Text("", size=(44, 1)),
            sg.Button("Next", key="dps_test_next", size=(18, 1))
        ],
    ]

    return tab_dps_tests
