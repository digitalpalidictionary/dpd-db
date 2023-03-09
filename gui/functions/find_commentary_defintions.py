import textwrap


def find_commentary_defintions(sg, values, definitions_df):

    test1 = definitions_df["bold"].str.contains(values["search_for"])
    test2 = definitions_df["commentary"].str.contains(
        values["contains"])
    filtered = test1 & test2
    df_filtered = definitions_df[filtered]
    search_results = df_filtered.to_dict(orient='records')

    layout_elements = []
    layout_elements.append(
        [
            sg.Button(
                "Add Commentary Definition", key="add_button_1"),
            sg.Button(
                "Cancel", key="cancel_1")
        ]
    )

    if len(search_results) < 50:
        layout_elements.append(
            [sg.Text(f"{len(search_results)} results ")])
    else:
        layout_elements.append(
            [sg.Text("dispalying the first 50 results. \
                please refine your search")])

    for i, r in enumerate(search_results):
        if i >= 50:
            break
        else:
            try:
                commentary = r["commentary"].replace("<b>", "")
                commentary = commentary.replace("</b>", "")
                commentary = textwrap.fill(commentary, 150)

                layout_elements.append(
                    [
                        sg.Checkbox(f"{i}.", key=i),
                        sg.Text(r['ref_code']),
                        sg.Text(r['bold'], text_color="white"),
                    ]
                )
                layout_elements.append(
                    [
                        sg.Text(
                            f"{commentary}", size=(150, None),
                            text_color="lightgray"),
                    ],
                )
            except Exception:
                layout_elements.append([sg.Text("no results")])

    layout_elements.append(
        [
            sg.Button(
                "Add Commentary Definition", key="add_button_2"),
            sg.Button(
                "Cancel", key="cancel_2")
        ]
    )

    layout = [
        [
            [sg.Column(
                layout=layout_elements, key='results',
                expand_y=True, expand_x=True,
                scrollable=True, vertical_scroll_only=True
                )],
        ]
    ]

    window = sg.Window(
        "Find Commentary Defintions",
        layout,
        resizable=True,
        size=(1920, 1080),
        finalize=True,
        )

    while True:
        event, values = window.read()
        if event == "Close" or event == sg.WIN_CLOSED:
            break

        if event == "add_button_1" or event == "add_button_2":
            return_results = []
            number = 0
            for value in values:
                if values[value]:
                    number = int(value)
                    return_results += [search_results[number]]

            window.close()
            return return_results

        if event == "cancel_1" or event == "cancel_2":
            window.close()

    window.close()
