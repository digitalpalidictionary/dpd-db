"""Render tab to edit PaliWord table in the database."""

from completion_combo import CompletionCombo
from functions_db import get_verb_values
from functions_db import get_case_values
from functions_db import get_root_key_values
from functions_db import get_family_word_values
from functions_db import get_family_set_values
from functions_db import get_compound_type_values
from functions_db import get_patterns
from tools.pos import POS

VERB_VALUES = get_verb_values()
TRANS_VALUES = ["", "trans", "intrans", "ditrans"]
NEG_VALUES = ["", "neg", "neg x2"]
CASE_VALUES = get_case_values()
ROOT_VALUES = get_root_key_values()
FAMILY_WORD_VALUES = get_family_word_values()
FAMILY_SET_VALUES = get_family_set_values()
DERIVATIVE_VALUES = ["", "kicca", "kita", "taddhita"]
COMPOUND_TYPE_VALUES = get_compound_type_values()
PATTERN_VALUES = get_patterns()


def make_tab_edit_dpd(sg, primary_user):

    origin = "pass1" if primary_user else "dps"

    add_word_layout = [
        [
            sg.Text("show fields", size=(15, 1)),
            sg.Radio(
                "all", "group1",
                key="show_fields_all",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
            sg.Radio(
                "root", "group1",
                key="show_fields_root",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
            sg.Radio(
                "compound", "group1",
                key="show_fields_compound",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
            sg.Radio(
                "word", "group1",
                key="show_fields_word",
                enable_events=True,
                tooltip="Show the fields relevant to the type of word"),
            sg.Text(
                "", key="show_fields_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("id", size=(15, 1, )),
            sg.Input(
                "", key="id", size=(20, 1),
                background_color="black",
                tooltip="A unique id.\n"),
            sg.Text(
                "", key="id_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pali_1", size=(15, 1)),
            sg.Input(
                key="pali_1", size=(50, 1),
                tooltip="Vocative singular of nouns and partitiplces,\n\
3rd person singular of verbs, unless irrgular."),
            sg.Text(
                "", key="pali_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pali_2*", size=(15, 1)),
            sg.Input(
                key="pali_2", size=(50, 1), enable_events=True,
                tooltip="Nominative singular of masc and neuter nouns."),
            sg.Text(
                "", key="pali_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pos", size=(15, 1)),
            CompletionCombo(
                POS, key="pos", size=(7, 1), enable_events=True,
                text_color=None, background_color=None,
                tooltip="Part of speech. Only use values in the dropdown list."
            ),
            sg.Text(
                "", key="pos_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("grammar*", size=(15, 1)),
            sg.Input(
                key="grammar", size=(50, 1), enable_events=True,
                tooltip="Order:\npos\n, or of\n"),
            sg.Text(
                "", key="grammar_error", size=(50, 1), text_color="red")
        ],

        [
            sg.Text("derived_from*", size=(15, 1)),
            sg.Input(
                key="derived_from", size=(50, 1),
                enable_events=True,
                tooltip="Kitas are derived from the present tense verb.\n\
Taddhitas - remove prefix and suffixes."),
            sg.Text(
                "", key="derived_from_error", size=(50, 1), text_color="red")

        ],
        [
            sg.Text("neg", size=(15, 1)),
            CompletionCombo(
                    NEG_VALUES, key="neg", size=(7, 1),
                    tooltip="Negatives. Mostly prefixed with na, nir or vi."),
            sg.Text("", key="neg_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("verb", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    VERB_VALUES, key="verb", size=(13, 1),
                    tooltip="Type of verb. Synchronize with base and grammar.")),
            sg.Text("", key="verb_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("trans", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    TRANS_VALUES, key="trans", size=(7, 1),
                    tooltip="Transitivity of verbs and active participles.\n\
Leave blank for other parts of speech.")),
            sg.Text(
                    "", key="trans_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("case", size=(15, 1)),
            CompletionCombo(
                CASE_VALUES, key="plus_case", size=(20, 1),
                tooltip="What case does a related syntactically related word take?"),
            sg.Text(
                "", key="case_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_1", size=(15, 2)),
            sg.Multiline(
                key="meaning_1", size=(50, 2), no_scrollbar=True,
                enable_events=True,
                tooltip="Primary meanings, seperated by ';'"),
            sg.Text(
                "", key="meaning_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("add_spelling", size=(15, 1)),
            sg.Input(
                key="add_spelling", size=(25, 1), enable_events=True,
                tooltip="Add a word to the user dictionary."),
            sg.Button("Add", key="add_spelling_button", font=(None, 13)),
            sg.Button("Edit", key="edit_spelling_button", font=(None, 13)),
            sg.Button("Check", key="check_spelling_button", font=(None, 13)),
            sg.Text(
                "", key="add_spelling_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_lit", size=(15, 1)),
            sg.Input(
                key="meaning_lit", size=(50, 1),
                enable_events=True,
                tooltip="Literal meaning of the prefix and suffix.\n\
Leave empty for long compounds."),
            sg.Text(
                "", key="meaning_lit_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="meaning_2", size=(50, 1),
                    enable_events=True,
                    tooltip="Meaning from Buddhadatta or CPED or DPS."),
            ),
            sg.Text(
                "", key="meaning_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("suggestion", visible=not primary_user, size=(15, 1)),
            sg.Button("GPT", visible=not primary_user, key="online_suggestion_button"),
            sg.Multiline(
                key="online_suggestion",
                visible=not primary_user,
                size=(45, 2),
                enable_events=True,
            ),
            sg.Text(
                "", key="online_suggestion_error", size=(50, 1), text_color="red", visible=not primary_user)
        ],
        [
            sg.Text("root_key", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    ROOT_VALUES, key="root_key",
                    size=(10, 1),
                    auto_size_text=False,
                    tooltip="Root key in PaliRoots table.\n\
Select a value from the dropdown list.")),
            sg.Text(
                "", key="root_info", text_color="white",
                pad=(10, 0)),
            sg.Text(
                "", key="root_key_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family_root*", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[], key="family_root",
                    size=(40, 1),
                    enable_events=True,
                    enable_per_char_events=True,
                    auto_size_text=False,
                    tooltip="Prefix(es) and root seperated by a space.")),
            sg.pin(
                sg.Button(
                    "Get",
                    size=(5, 1),
                    font=(None, 13),
                    key="get_family_root")),
            sg.Text(
                "", key="family_root_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root_sign*", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[],
                    key="root_sign",
                    size=(40, 1),
                    enable_events=True,
                    enable_per_char_events=True,
                    auto_size_text=False,
                    tooltip="Sign of the verb.\n\
Inlclude '*' for causatives and group 8 verbs.")),
            sg.pin(
                sg.Button(
                    "Get",
                    size=(5, 1),
                    font=(None, 13),
                    key="get_root_sign")),
            sg.Text(
                "", key="root_sign_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root_base", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[],
                    key="root_base",
                    size=(40, 1),
                    enable_per_char_events=True,
                    auto_size_text=False,
                    tooltip="Root + sign = Base. (caus, pass, etc.)\n\
If irregular, show phonetic development, e.g.\n\
kar + *āpe  > kārāpe > karāpe (caus, irreg).")),
            sg.pin(
                sg.Button(
                    "Get",
                    size=(5, 1),
                    font=(None, 13),
                    key="get_root_base")),
            sg.Text(
                "", key="root_base_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family_word", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    FAMILY_WORD_VALUES,
                    key="family_word",
                    size=(49, 1),
                    tooltip="Family of the word if not derived from a root."),
            ),
            sg.Text(
                "", key="family_word_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family_compound*", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="family_compound", size=(50, 1),
                    enable_events=True,
                    tooltip="Family compounds, seperated by space.")),
            sg.Text(
                "", key="family_compound_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("construction*", size=(15, 2)),
            sg.Multiline(
                key="construction",
                no_scrollbar=True,
                size=(50, 2),
                enable_events=True,
                tooltip="Construciton of the word, showing all phonetic change."),
            sg.Text(
                "", key="construction_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.pin(
                 sg.Input(
                    key="add_construction", size=(20, 1),
                    tooltip="Add this word to the words to add list.")),
            sg.pin(
                sg.Button(
                    "Add", key="add_construction_button", font=(None, 13))),
            sg.Text(
                "", key="add_construction_error", size=(50, 1),
                text_color="red")
        ],
        [
            sg.Text("derivative", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    values=DERIVATIVE_VALUES, key="derivative", size=(10, 1),
                    enable_per_char_events=True,
                    tooltip="Choose a value from the dropdown")),
            sg.Text(
                "", key="derivative_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("suffix*", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="suffix",
                    enable_events=True,
                    size=(31, 1),
                    tooltip="Final suffix used. Don't add for words with case endings")),
            sg.Text(
                "", key="suffix_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("phonetic", size=(15, 1)),
            sg.Multiline(
                key="phonetic", size=(50, 2), no_scrollbar=True,
                tooltip="List of all phonetic changes"),
            sg.Text(
                "", key="phonetic_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("compound_type", size=(15, 1)),
            sg.pin(
                CompletionCombo(
                    COMPOUND_TYPE_VALUES,
                    key="compound_type", size=(49, 1),
                    tooltip="Type of samāsa")),
            sg.Text(
                "", key="compound_type_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("compound_construction*", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="compound_construction", size=(50, 1),
                    enable_events=True,
                    tooltip="Construction of the samāsa, showing case relationship")),
            sg.Text(
                "", key="compound_construction_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="bold_cc", size=(20, 1),
                tooltip="Add bold to the case ending"),
            sg.Button("Bold", key="bold_cc_button", font=(None, 13)),
        ],
        [
            sg.Text("non_root_in_comps", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="non_root_in_comps", size=(50, 1),
                    tooltip="")),
            sg.Text(
                "", key="non_root_in_comps_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("antonym", size=(15, 1)),
            sg.Input(
                key="antonym", size=(50, 1),
                tooltip="Word(s) with the opposite meaning"),
            sg.Text(
                "", key="antonym_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("synonym*", size=(15, 1)),
            sg.Input(
                key="synonym", size=(50, 1), enable_events=True,
                tooltip="Will get automatically filled"),
            sg.Text(
                "", key="synonym_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("variant", size=(15, 1)),
            sg.Input(
                key="variant", size=(50, 1), enable_events=True,
                tooltip="Add variant readings in text"),
            sg.Text(
                "", key="variant_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("commentary", size=(15, 5)),
            sg.Multiline(
                key="commentary", size=(50, 5), no_scrollbar=True,
                tooltip="Add commentary definition"),
            sg.Text(
                "", key="commentary_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("search for", size=(15, 1)),
            sg.Input(
                "", key="search_for", size=(20, 1),
                enable_events=True,
                tooltip="Search for BOLD words in commentaries"),
            sg.Input(
                "", key="contains", size=(17, 1),
                tooltip="Search for NOT BOLD words in commentaries"),
            sg.Button(
                "Search", key="defintions_search_button", font=(None, 13)),
            sg.Button(
                "Clean", key="commentary_clean", font=(None, 13)),
            sg.Text(
                "", key="search_for_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Multiline(
                key="notes", size=(50, 1), tooltip="Add additional notes"),
            sg.Text(
                "", key="notes_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="notes_italic_bold", size=(30, 1),
                tooltip="Bold the word"),
            sg.Button("Italic", key="notes_italic_button", font=(None, 13)),
            sg.Button("Bold", key="notes_bold_button", font=(None, 13)),
            sg.Text(
                "", key="notes_italic_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("non_ia", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="non_ia", size=(50, 41),
                    tooltip="Cognate of the word in non Indo-Aryan languages?"),
            ),
            sg.Text(
                "", key="non_ia_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sanskrit*", size=(15, 1)),
            sg.Input(
                key="sanskrit", size=(50, 1), enable_events=True,
                tooltip="Cogante of the word in Sanskrit or BHS."),
            sg.Text(
                "", key="sanskrit_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("cognate", size=(15, 1)),
            sg.Input(
                key="cognate", size=(50, 1),
                tooltip="Cognate words in English"),
            sg.Text(
                "", key="cognate_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("link", size=(15, 1)),
            sg.Input(
                key="link", size=(50, 1),
                tooltip="Add a wikipedia link"),
            sg.Text(
                "", key="link_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("source_1*", size=(15, 1)),
            sg.Input(
                key="source_1", size=(50, 1), enable_events=True,
                tooltip="Sutta code using DPR system"),
            sg.Text(
                "", key="source_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sutta_1*", size=(15, 1)),
            sg.Input(
                key="sutta_1", size=(50, 1), enable_events=True,
                tooltip="Sutta name"),
            sg.Text(
                "", key="sutta_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("example_1*", size=(15, 5)),
            sg.Multiline(
                key="example_1", size=(49, 5),
                enable_events=True,
                tooltip="Sutta example. Add all sandhi apostrophes."),
            sg.Text(
                "", key="example_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(
                key="bold_1", size=(20, 1),
                tooltip="Bold the word"),
            sg.Button("Bold", key="bold_1_button", font=(None, 13)),
            sg.Button(
                "Another Eg",
                key="another_eg_1",
                tooltip="Find another sutta example",
                font=(None, 13)),
            sg.Button("Lower", key="example_1_lower", font=(None, 13)),
            sg.Button("Clean", key="example_1_clean", font=(None, 13)),
            sg.Text("", key="bold_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("source_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="source_2", size=(50, 1),
                    tooltip="Sutta code using DPR system")),
            sg.Text(
                "", key="source_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sutta_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="sutta_2", size=(50, 1),
                    tooltip="Sutta name")),
            sg.Text(
                "", key="sutta_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("example_2", size=(15, 5)),
            sg.pin(
                sg.Multiline(
                    key="example_2", size=(49, 5),
                    tooltip="Sutta example. Add all sandhi apostrophes.")),
            sg.Text(
                "", key="example_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="bold_2", size=(20, 1),
                    tooltip="Bold the word")),
            sg.pin(
                sg.Button("Bold", key="bold_2_button", font=(None, 13))),
            sg.pin(
                sg.Button(
                    "Another Eg", key="another_eg_2", font=(None, 13),
                    tooltip="Find another sutta example")),
            sg.pin(
                sg.Button("Lower", key="example_2_lower", font=(None, 13))),
            sg.pin(
                sg.Button("Clean", key="example_2_clean", font=(None, 13))),
            sg.Text("", key="bold_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family set*", size=(15, 1)),
            CompletionCombo(
                FAMILY_SET_VALUES, key="family_set",
                size=(49, 1),
                tooltip="Add to sets"),
            sg.Text("", key="family_set_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("stem pattern*", size=(15, 1)),
            sg.Input(
                key="stem", size=(30, 1), justification="r",
                enable_events=True,
                tooltip="Stem of the word, without the pattern"),
            CompletionCombo(
                PATTERN_VALUES, key="pattern",
                size=(12, 1), tooltip="Inflection pattern of the word"),
            sg.Input(
                origin, key="origin", size=(6, 1),
                tooltip="Where does this word data come from?"),
            sg.Text(
                "", key="stem_error", size=(50, 1), text_color="red"),
            sg.Text(
                "", key="pattern_error", size=(50, 1), text_color="red")
        ],
        ]

    tab_edit_dpd = [
        [
            sg.Column(
                add_word_layout,
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
            # db buttons
            sg.Text("db buttons", size=(15, 1)),
            sg.Button(
                "Clone", tooltip="Clone a word from the db"),
            sg.Input(
                key="word_to_clone_edit",
                size=(15, 1),
                enable_events=True,
                tooltip="Enter id or pali_1"
            ),
            sg.Button(
                "Edit", key="edit_button", tooltip="Edit a word in the db"),
            sg.Button(
                "Test", key="test_internal_button",
                tooltip="Run internal tests"),
            sg.Button(
                "Update db", key="update_db_button1",
                tooltip="Add a new word or update existing word in the db",
                visible=primary_user),
            sg.Button(
                "Update DB", key="update_db_button2",
                tooltip="Add a new word or update existing word in the db",
                visible=not primary_user),
            sg.Button(
                "Delete", key="delete_button",
                tooltip="Delete a word from the db. Careful!",
                mouseover_colors="red",
                visible=primary_user),
            sg.Button(
                "Update Sandhi", key="update_sandhi_button",
                tooltip="Update list of words with sandhi apostophes"),
            sg.Button(
                "Log", key="open_corrections_button",
                tooltip="open corrections tsv in code",
                visible=not primary_user),
        ],
        [
            # gui buttons
            sg.Text("gui buttons", size=(15, 1)),
            sg.Button(
                "Open Tests", key="open_tests_button",
                tooltip="Open TSV file of internal tests"),
            sg.Button(
                "Debug", key="debug_button",
                tooltip="Print the current values in the terminal"),
            sg.Button(
                "Stash", key="stash_button",
                tooltip="Stash the word to edit it again later"),
            sg.Button(
                "Unstash", key="unstash_button",
                tooltip="Unstash a word to edit it again"),
            sg.Button(
                "Split", key="split_button",
                tooltip="Stash the word and open a copy to edit"),
            sg.Button(
                "Summary", key="summary_button",
                tooltip="See a summary of filled fields"),
            sg.Button(
                "Save", key="save_state_button",
                tooltip="Save the current state of the GUI"),
            sg.Button(
                "Clear", key="clear_button", tooltip="Clear all the fields"),
            sg.Button(
                "Save and Close", key="save_and_close_button",
                tooltip="Save the current state, backup to tsv and close"),
        ]
    ]

    return tab_edit_dpd
