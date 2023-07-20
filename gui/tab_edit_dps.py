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
                font=(None, 13)
            )
        ],
        [
            sg.Text("id and pali_1", size=(15, 1)),
            sg.Multiline(
                "00000",
                key="dps_dpd_id", size=(7, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
            sg.Multiline(
                "chandarāgappaṭibaddhatta",
                key="dps_pali_1", size=(43, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("grammar", size=(15, 1)),
            sg.Multiline(
                "pr, reflx 3rd sg of na bhāvayati, neg, caus, trans (+acc)",
                key="dps_grammar",
                size=(50, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("meaning", size=(15, 1)),
            sg.Multiline(
                "due to attachment to passion for sensual pleasure, bondage to it, greed for it, obsession with it and fixation with it; because of adherence to love of sensual desire, being tied to it, craving for it, being consumed by it and addiction to it",
                key="dps_meaning",
                size=(50, 2),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [

            sg.Text("russian", size=(15, 1)),
            sg.Multiline(
                "",
                key="dps_ru_meaning",
                size=(50, 2),
                no_scrollbar=True,
                enable_events=True,
                tooltip="type Russian meaning",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("russian lit", size=(15, 1)),
            sg.Multiline(
                "",
                key="dps_ru_meaning_lit",
                size=(50, 1),
                no_scrollbar=True,
                enable_events=True,
                tooltip="type Russian literal meaning",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("sbs meaning", size=(15, 1)),
            sg.Multiline(
                "",
                key="dps_sbs_meaning",
                size=(50, 2),
                no_scrollbar=True,
                enable_events=True,
                tooltip="type Russian literal meaning",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("root", size=(15, 1)),
            sg.Multiline(
                "√sambh･4 uṇā (reach, attain)",
                key="dps_root",
                size=(50, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("base or comp", size=(15, 1)),
            sg.Multiline(
                "√sambh + uṇā > sambhuṇā",
                key="dps_base_or_comp",
                size=(50, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("constr", size=(15, 1)),
            sg.Multiline(
                "na > an + abhi + sambhuṇā + nta</br>na + abhisambhuṇanta",
                key="dps_constr_or_comp_constr",
                size=(50, 2),
                no_scrollbar=True,
                tooltip="",
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("synonym", size=(15, 1)),
            sg.Multiline(
                "vevacana",
                key="dps_synonym",
                size=(50, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("antonym", size=(15, 1)),
            sg.Multiline(
                "avevacana",
                key="dps_antonym",
                size=(50, 1),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Multiline(
                "ten peceptions 1. aniccasaññā, 2. <b>anattasaññā</b>, 3. asubhasaññā, 4. ādīnavasaññā, 5. pahānasaññā, 6. virāgasaññā, 7. nirodhasaññā, 8. sabbaloke anabhiratasaññā, 9. sabbasaṅkhāresu anicchāsaññā, 10. ānāpānassati.",
                key="dps_notes",
                size=(50, 3),
                no_scrollbar=True,
                text_color=dpd_text,
                background_color=dpd_background),
        ],
        [
            sg.Text("russian note", size=(15, 1)),
            sg.Multiline(
                "",
                key="dps_ru_notes",
                size=(50, 1),
                enable_events=True,
                no_scrollbar=True,
                tooltip="",
                text_color=ru_text,
                background_color=ru_background),
        ],
        [
            sg.Text("sbs note", size=(15, 1)),
            sg.Multiline(
                "",
                key="dps_sbs_notes",
                size=(50, 1),
                enable_events=True,
                no_scrollbar=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("example 1", size=(15, 1)),
            sg.Multiline(
                "tassā ubhosu tīresu kāsā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, kusā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, pabbajā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, bīraṇā ce'pi jātā assu, te naṃ ajjholambeyyuṃ, rukkhā ce'pi jātā assu, te naṃ ajjholambeyyuṃ. SN 22.93 nadīsuttaṃ",
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
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("sbs_chant_eng_1", size=(15, 1)),
            sg.Input(
                "",
                key="dps_sbs_chant_eng_1",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_1", size=(15, 1)),
            sg.Input(
                "",
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
                "dhammatā esā, bhikkhave, diṭṭhisampannassa puggalassa, kiñ'c'āpi tathārūpiṃ āpattiṃ āpajjati, yathārūpāya āpattiyā vuṭṭhānaṃ paññāyati, atha kho naṃ khippam'eva satthari vā viññūsu vā sabrahmacārīsu deseti vivarati uttānīkaroti, desetvā vivaritvā uttānīkatvā āyatiṃ saṃvaraṃ āpajjati. MN 48 kosambiyasuttaṃ",
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
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_2", size=(15, 1)),
            sg.Input(
                "",
                key="dps_sbs_chant_eng_2",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_2", size=(15, 1)),
            sg.Input(
                "",
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
                "",
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
                "",
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
                size=(50, 1),
                enable_events=True,
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chant_eng_3", size=(15, 1)),
            sg.Input(
                "",
                key="dps_sbs_chant_eng_3",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_3", size=(15, 1)),
            sg.Input(
                "",
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
                "",
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
                "",
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
                size=(50, 1),
                enable_events=True,
                text_color=sbs_text,
                background_color=sbs_background,
                tooltip=""),
        ],
        [
            sg.Text("sbs_chant_eng_4", size=(15, 1)),
            sg.Input(
                "",
                key="dps_sbs_chant_eng_4",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_chapter_4", size=(15, 1)),
            sg.Input(
                "",
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
                "audio=[sound:pali1(without number).mp3]",
                key="dps_sbs_audio",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_category", size=(15, 1)),
            sg.Input(
                "",
                key="dps_sbs_category",
                size=(50, 1),
                tooltip="",
                text_color=sbs_text,
                background_color=sbs_background),
        ],
        [
            sg.Text("sbs_index", size=(15, 1)),
            sg.Input(
                "",
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
