"""Render tab to edit add sandhi rules, manual corrections, spelling mistakes
and variant readings."""


def make_tab_fix_sandhi(sg):
    tab_fix_sandhi = [
        [
            sg.Text("rule_no", size=(4, 1), pad=((190, 0), (50, 0))),
            sg.Text("chA", size=(4, 1), pad=((0, 0), (50, 0))),
            sg.Text("chB", size=(4, 1), pad=((0, 0), (50, 0))),
            sg.Text("ch1", size=(4, 1), pad=((0, 0), (50, 0))),
            sg.Text("ch2", size=(4, 1), pad=((0, 0), (50, 0))),
            sg.Text("example", size=(25, 1), pad=((0, 0), (50, 0))),
            sg.Text("weight", size=(7, 1), pad=((0, 0), (50, 0))),
        ],
        [
            sg.Text("add sandhi rule: "),
            sg.Input(key="rule_no", size=(3, 1), justification="l"),
            sg.Input(key="chA", size=(3, 1), justification="r"),
            sg.Input(key="chB", size=(3, 1), justification="l"),
            sg.Input(key="ch1", size=(3, 1), justification="r"),
            sg.Input(key="ch2", size=(3, 1), justification="l"),
            sg.Input(key="example", size=(25, 1)),
            sg.Input("weight", key="weight", size=(7, 1)),
            sg.Button("Add", key="add_sandhi_rule"),
            sg.Button("Open", key="open_sandhi_rules"),
        ],
        [sg.Text("")],
        [
            sg.Text("sandhi", size=(26, 1), pad=((210, 0), (0, 0))),
            sg.Text("correction", size=(27, 1), pad=((0, 0), (0, 0))),
        ],
        [
            sg.Text("sandhi correction: "),
            sg.Input(key="sandhi_to_correct", size=(25, 1)),
            sg.Input(key="sandhi_correction", size=(27, 1)),
            sg.Button("Add", key="add_sandhi_correction"),
            sg.Button("Open", key="open_sandhi_corrections"),
        ],
        [sg.Text("")],
        [
            sg.Text("spelling mistake", size=(26, 1), pad=((200, 0), (0, 0))),
            sg.Text("correction", size=(27, 1), pad=((0, 0), (0, 0))),
        ],
        [
            sg.Text("spelling mistake: "),
            sg.Input(key="spelling_mistake", size=(25, 1)),
            sg.Input(key="spelling_correction", size=(27, 1)),
            sg.Button("Add", key="add_spelling_mistake"),
            sg.Button("Open", key="open_spelling_mistakes"),
        ],
        [sg.Text("")],
        [
            sg.Text("variant reading", size=(26, 1), pad=((200, 0), (0, 0))),
            sg.Text("main reading", size=(27, 1), pad=((0, 0), (0, 0))),
        ],
        [
            sg.Text("variant reading: "),
            sg.Input(key="variant_reading", size=(25, 1)),
            sg.Input(key="main_reading", size=(27, 1)),
            sg.Button("Add", key="add_variant_reading"),
            sg.Button("Open", key="open_variant_readings"),
        ],
        [sg.Text("sandhi ok: ", size=(25, 1)), sg.Button("Open", key="open_sandhi_ok")],
        [
            sg.Text("sandhi exceptions: ", size=(25, 1)),
            sg.Button("Open", key="open_sandhi_exceptions"),
        ],
    ]

    return tab_fix_sandhi
