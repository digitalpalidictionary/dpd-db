from functions import load_sbs_index
from completion_combo import CompletionCombo

sbs_index = load_sbs_index()
pali_chant_list = [i.pali_chant for i in sbs_index]
pali_class_list = [str(i) for i in range(1, 99)]

dpd_background = "#1c1e23"
dpd_text = "#0a9ce4"
ru_background = "#32363f"
ru_text = "white"
sbs_background = "#272a31"
sbs_text = "white"


def make_tab_edit_dps(sg):

    dps_layout = [
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                "",
                key="dps_id_or_pali_1",
                size=(35, 1),
                enable_events=True,
                tooltip="enter id or pali_1"),
            sg.Button(
                "Get word from Db",
                key="dps_id_or_pali_1_button",
                tooltip="click to fetch word from db",
                font=(None, 13)),
            sg.Text("", size=(5, 1)),
        ],
        [
            sg.Text("id and pali_1", size=(15, 1)),
            sg.Input(
                key="dps_dpd_id", size=(7, 1),
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Input(
                key="dps_pali_1", size=(43, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("grammar", size=(15, 1)),
            sg.Input(
                key="dps_grammar",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("meaning", size=(15, 1)),
            sg.Input(
                key="dps_meaning",
                size=(50, 2),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [

            sg.Text("russian", size=(15, 1)),
            sg.Multiline(
                key="dps_ru_meaning",
                size=(50, 2),
                enable_events=True,
                tooltip="type Russian meaning",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("russian lit", size=(15, 1)),
            sg.Input(
                key="dps_ru_meaning_lit",
                size=(50, 1),
                enable_events=True,
                tooltip="type Russian literal meaning",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("sbs meaning", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_meaning",
                size=(50, 2),
                enable_events=True,
                tooltip="type Russian literal meaning",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("root", size=(15, 1)),
            sg.Input(
                key="dps_root",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("base or comp", size=(15, 1)),
            sg.Input(
                key="dps_base_or_comp",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("constr", size=(15, 1)),
            sg.Input(
                key="dps_constr_or_comp_constr",
                size=(50, 2),
                tooltip="",
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("synonym", size=(15, 1)),
            sg.Input(
                key="dps_synonym",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("antonym", size=(15, 1)),
            sg.Input(
                key="dps_antonym",
                size=(50, 1),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Multiline(
                key="dps_notes",
                size=(50, 3),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("russian note", size=(15, 1)),
            sg.Multiline(
                key="dps_ru_notes",
                size=(50, 2),
                enable_events=True,
                tooltip="",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("sbs note", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_notes",
                size=(50, 2),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("example 1", size=(15, 1)),
            sg.Multiline(
                key="dps_example_1",
                size=(50, 4),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("sbs_chant_pali_1", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_1",
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_1",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_1", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_1",
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("example 2", size=(15, 1)),
            sg.Multiline(
                key="dps_example_2",
                size=(50, 4),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("sbs_chant_pali_2", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_2",
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_2",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_2", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_2",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_source_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_3",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_sutta_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_3",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_example_3", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_3",
                size=(50, 4),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_pali_3", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_3",
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_3",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_3", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_3",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_source_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_source_4",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_sutta_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_sutta_4",
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_example_4", size=(15, 1)),
            sg.Multiline(
                key="dps_sbs_example_4",
                size=(50, 4),
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("sbs_chant_pali_4", size=(15, 1)),
            CompletionCombo(
                pali_chant_list,
                key="dps_sbs_chant_pali_4",
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chant_eng_4",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_4", size=(15, 1)),
            sg.Input(
                key="dps_sbs_chapter_4",
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("class anki", size=(15, 1)),
            CompletionCombo(
                pali_class_list,
                key="dps_sbs_class_anki",
                default_value="",
                size=(3, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("sbs_audio", size=(15, 1)),
            sg.Input(
                key="dps_sbs_audio",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_category", size=(15, 1)),
            sg.Input(
                key="dps_sbs_category",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_index", size=(15, 1)),
            sg.Input(
                key="dps_sbs_index",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("", size=(55, 1))
        ],
    ]

    tab_edit_dps = [
        [
            sg.Column(
                dps_layout,
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
        [
            sg.Button("Clear", key="dps_clear_button"),
            sg.Button("Reset", key="dps_reset_button"),
            sg.Button("Update DB", key="dps_update_db_button"),
        ],
    ]

    return tab_edit_dps
