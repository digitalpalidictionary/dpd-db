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
    chapter_list = ['Homage to the Triple Gem', 'Verses', 'Teachings','Reflections', 'Cardinal Suttas', 'Thanksgiving Recitations', 'Protective Recitations', 'Funeral Chants', 'Sharing of Merits', 'International Pātimokkha', 'Post Pātimokkha', 'Prefixes']
    chant_list = ['dependent on chosen chapter']
    pali_class_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    dpd_line_1 = ['id', 'pali_1']
    dpd_line_2 = ['pos', 'grammar', 'derived_from', 'neg', 'verb', 'trans', 'case']
    dpd_line_3 = ['meaning_1', 'meaning_lit', 'or', 'meaning_2 if meaning_1 empty']
    dpd_line_4 = ['root_key', 'root_group', 'root_sign', 'root_meaning']
    dpd_line_5 = ['base', 'or', 'comp']
    dpd_line_6 = ['construction', 'or', 'comp_constr']
    dpd_line_7 = ['synonym', 'antonym']
    dpd_line_8 = ['notes']
    dpd_line_9 = ['source_1', 'sutta_1', 'example_1']
    dpd_line_10 = ['source_2', 'sutta_2', 'example_2']
    

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
            sg.Text("id and pali_1", size=(15, 1)),
            sg.Multiline(
                "00000 chandarāgappaṭibaddhatta",
                key="dpd_line_1", size=(50, 1),
                tooltip=example_tooltip),
        ],
        [
            sg.Text("grammar", size=(15, 1)),
            sg.Multiline(
                "pr, reflx 3rd sg of na bhāvayati, neg, caus, trans (+acc)",
                key="dpd_line_2",
                size=(50, 1),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("meaning", size=(15, 1)),
            sg.Multiline(
                "due to attachment to passion for sensual pleasure, bondage to it, greed for it, obsession with it and fixation with it; because of adherence to love of sensual desire, being tied to it, craving for it, being consumed by it and addiction to it",
                key="dpd_line_3",
                size=(50, 3),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            # make the key names the same as the
            # name of the field in db

            sg.Text("russian", size=(15, 1)),
            sg.Multiline(
                "",
                key="ru_meaning",
                size=(50, 3),
                wrap_lines = True,
                enable_events=True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("russian lit", size=(15, 1)),
            sg.Multiline(
                "",
                key="ru_meaning_lit",
                size=(50, 1),
                wrap_lines = True,
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs meaning", size=(15, 1)),
            sg.Multiline(
                "",
                key="sbs_meaning",
                size=(50, 2),
                enable_events=True,
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("root", size=(15, 1)),
            sg.Multiline(
                "√sambh･4 uṇā (reach, attain)",
                key="dpd_line_4",
                size=(50, 1),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("base or comp", size=(15, 1)),
            sg.Multiline(
                "√sambh + uṇā > sambhuṇā",
                key="dpd_line_5",
                size=(50, 1),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
                [
            sg.Text("constr", size=(15, 1)),
            sg.Multiline(
                "na > an + abhi + sambhuṇā + nta</br>na + abhisambhuṇanta",
                key="dpd_line_6",
                size=(50, 2),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("syn/ant", size=(15, 1)),
            sg.Multiline(
                "vevacana; avevacana",
                key="dpd_line_7",
                size=(50, 1),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Multiline(
                "ten peceptions 1. aniccasaññā, 2. <b>anattasaññā</b>, 3. asubhasaññā, 4. ādīnavasaññā, 5. pahānasaññā, 6. virāgasaññā, 7. nirodhasaññā, 8. sabbaloke anabhiratasaññā, 9. sabbasaṅkhāresu anicchāsaññā, 10. ānāpānassati.",
                key="dpd_line_8",
                size=(50, 3),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],
        [
            sg.Text("russian note", size=(15, 1)),
            sg.Multiline(
                "",
                key="ru_notes",
                size=(50, 1),
                enable_events=True,
                wrap_lines = True,
                tooltip=example_tooltip),
        ],



        [
            sg.Text("sbs note", size=(15, 1)),
            sg.Multiline(
                "",
                key="sbs_notes",
                size=(50, 1),
                enable_events=True,
                wrap_lines = True,
                tooltip=example_tooltip),
        ],


        [
            sg.Text("example 1", size=(15, 1)),
            sg.Multiline(
                "tassā ubhosu tīresu kāsā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, kusā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, pabbajā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, bīraṇā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, rukkhā ce'pi jātā assu, te naṃ ajjholambeyyuṃ. SN 22.93 nadīsuttaṃ",
                key="dpd_line_9",
                size=(50, 3),
                wrap_lines = True,
                tooltip=example_tooltip),
        ],


        [
            sg.Text("sbs_chapter_1", size=(15, 1)),
            sg.Combo(
                chapter_list,
                key="sbs_chapter_1",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_pali_1", size=(15, 1)),
            sg.Combo(
                chant_list,
                key="sbs_chant_pali_1",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_eng_1", size=(15, 1)),
            sg.Text(
                "chant name taken from sbs-index.csv",
                key="sbs_chant_eng_1",
                size=(50, 1),
                tooltip=example_tooltip),
        ],

        [
            sg.Text("example 2", size=(15, 3)),
            sg.Multiline(
                "dhammatā esā, bhikkhave, diṭṭhisampannassa puggalassa, kiñ'c'āpi tathārūpiṃ āpattiṃ āpajjati, yathārūpāya āpattiyā vuṭṭhānaṃ paññāyati, atha kho naṃ khippam'eva satthari vā viññūsu vā sabrahmacārīsu deseti vivarati uttānīkaroti, desetvā vivaritvā uttānīkatvā āyatiṃ saṃvaraṃ āpajjati. MN 48 kosambiyasuttaṃ",
                key="dpd_line_10",
                size=(50, 3),
                tooltip=example_tooltip),
        ],


        [
            sg.Text("sbs_chapter_2", size=(15, 1)),
            sg.Combo(
                chapter_list,
                key="sbs_chapter_2",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_pali_2", size=(15, 1)),
            sg.Combo(
                chant_list,
                key="sbs_chant_pali_2",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_eng_2", size=(15, 1)),
            sg.Text(
                "chant name taken from sbs-index.csv",
                key="sbs_chant_eng_2",
                size=(40, 1),
                tooltip=example_tooltip),
        ],


        [
            sg.Text("sbs_source_3", size=(15, 1)),
            sg.Input(
                "",
                key="sbs_source_3",
                size=(40, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_sutta_3", size=(15, 1)),
            sg.Input(
                "",
                key="sbs_sutta_3",
                size=(40, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_example_3", size=(15, 3)),
            sg.Input(
                "",
                key="sbs_example_3",
                size=(40, 3),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chapter_3", size=(15, 1)),
            sg.Combo(
                chapter_list,
                key="sbs_chapter_3",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_pali_3", size=(15, 1)),
            sg.Combo(
                chant_list,
                key="sbs_chant_pali_3",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_eng_3", size=(15, 1)),
            sg.Text(
                "chant name taken from sbs-index.csv",
                key="sbs_chant_eng_3",
                size=(40, 1),
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_source_4", size=(15, 1)),
            sg.Input(
                "",
                key="sbs_source_4",
                size=(40, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_sutta_4", size=(15, 1)),
            sg.Input(
                "",
                key="sbs_sutta_4",
                size=(40, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_example_4", size=(15, 3)),
            sg.Input(
                "",
                key="sbs_example_4",
                size=(40, 3),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chapter_4", size=(15, 1)),
            sg.Combo(
                chapter_list,
                key="sbs_chapter_4",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_pali_4", size=(15, 1)),
            sg.Combo(
                chant_list,
                key="sbs_chant_pali_4",
                size=(21, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_chant_eng_4", size=(15, 1)),
            sg.Text(
                "chant name taken from sbs-index.csv",
                key="sbs_chant_eng_4",
                size=(40, 1),
                tooltip=example_tooltip),
        ],


        [
            sg.Text("class anki", size=(15, 1)),
            sg.Combo(
                pali_class_list,
                key="sbs_class_anki",
                size=(3, 1),
                enable_events=True,
                text_color=None, background_color=None,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_category", size=(15, 1)),
            sg.Input(
                "",
                key="sbs_category",
                size=(20, 1),
                enable_events=True,
                tooltip=example_tooltip),
        ],

        [
            sg.Text("sbs_audio", size=(15, 1)),
            sg.Text(
                "audio=[sound:pali1(without number).mp3]",
                key="sbs_audio",
                size=(40, 1),
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
            sg.Tab("DPS", tab_devatab, key="devamitta_tab")
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

def read_csv_file(file_path):
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        rows = [tuple(row) for row in reader]
        return rows

    index_rows = read_csv_file("sbs-index.csv")
    for row in index_rows:
        print(f"{row[0]}. {row[1]}")



if __name__ == "__main__":
    main()