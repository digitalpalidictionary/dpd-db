# from db_helpers import get_next_ids
from db_helpers import get_verb_values
from db_helpers import get_case_values
from db_helpers import get_root_key_values
from db_helpers import get_family_word_values
from db_helpers import get_family_set_values
from db_helpers import get_compound_type_values
from db_helpers import get_patterns
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

# database field tooltips
id_tooltip = "A unique id.\nNot manually adjustable."
user_id_tooltip = "A unique user id.\nNot manually adjustable."
show_fields_tooltip = "What type of word is it? \
This determines what fields need to be added"
pali_1_tooltip = "Nouns and partitiplces: vocative singular.\n\
Verbs: 3rd person singular unless irrgular."
pali_2_tooltip = "Nominative singular of masc and neuter nouns."
pos_tooltip = "Only use values in the dropdown list."
grammar_tooltip = "Order:\npos\n, or of\n"
derived_from_tooltip = "Kitas are derived from the present tense verb.\n\
Taddhitas - remove prefix and suffixes."
neg_tooltip = "Most commonly prefixed with 'na', 'nir' or 'vi'."
verb_tooltip = "Synchronize with base and grammar."
trans_tooltip = "Transitivity of verbs and active participles.\n\
Leave blank for other parts of speech."
plus_case_tooltip = "What case does a related syntactically related word take?"
meaning_1_tooltip = "Primary meanings, seperated by ';'"
add_spelling_tooltip = "Add a word to the user dictionary."
meaning_lit_tooltip = "Literal meaning of the prefix and suffix.\n\
Leave empty for long compounds."
meaning_2_tooltip = "Meaning from another dictionary."
non_ia_tooltip = "Cognate of the word in non Indo-Aryan languages?"
sanskrit_tooltip = "Cogante of the word in Sanskrit."
xxx_sanskrit_root_tooltip = ""
xxx_sanskrit_root_meaning_tooltip = ""
xxx_sanskrit_root_class_tooltip = ""
root_key_tooltip = "Select a value from the dropdown list."
xxx_root_in_comps_tooltip = ""
xxx_root_has_verb_tooltip = ""
xxx_root_group_tooltip = ""
root_sign_tooltip = "Sign of the verb.\n\
Inlclude '*' for causatives and group 8 verbs."
xxx_root_meaning_tooltip = ""
root_base_tooltip = "Root + sign = Base. (caus, pass, etc.)\n\
If irregular, show phonetic development, e.g.\n\
kar + *āpe  > kārāpe > karāpe (caus, irreg)."
family_root_tooltip = "Prefix(es) and root seperated by a space."
family_word_tooltip = "Family of the word if not derived from a root."
family_compound_tooltip = "Family compounds, seperated by space."
construction_tooltip = "Construciton of the word, showing all phonetic change."
add_construction_tooltip = "Add this word to the words to add list."
derivative_tooltip = ""
suffix_tooltip = ""
phonetic_tooltip = ""
compound_type_tooltip = ""
compound_construction_tooltip = ""
bold_cc_tooltip = ""
non_root_in_comps_tooltip = ""
source_1_tooltip = ""
sutta_1_tooltip = ""
example_1_tooltip = ""
source_2_tooltip = ""
sutta_2_tooltip = ""
example_2_tooltip = ""
antonym_tooltip = ""
synonym_tooltip = ""
variant_tooltip = ""
commentary_tooltip = ""
notes_tooltip = ""
cognate_tooltip = ""
family_set_tooltip = ""
link_tooltip = ""
stem_tooltip = ""
pattern_tooltip = ""
origin_tooltip = ""

# ui tooltips
search_for_tooltip = ""
contains_tooltip = ""
bold_1_tooltip = ""
another_eg_1_tooltip = ""
bold_2_tooltip = ""
another_eg_2_tooltip = ""


def make_tab_add_word(sg):

    add_word_layout = [
        [
            sg.Text("show fields", size=(15, 1)),
            sg.Radio(
                "all", "group1",
                key="show_fields_all",
                enable_events=True,
                tooltip=show_fields_tooltip),
            sg.Radio(
                "root", "group1",
                key="show_fields_root",
                enable_events=True,
                tooltip=show_fields_tooltip),
            sg.Radio(
                "compound", "group1",
                key="show_fields_compound",
                enable_events=True,
                tooltip=show_fields_tooltip),
            sg.Radio(
                "word", "group1",
                key="show_fields_word",
                enable_events=True,
                tooltip=show_fields_tooltip),
            sg.Text(
                "", key="show_fields_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("id", size=(15, 1, )),
            sg.Input(
                "", key="id", size=(20, 1),
                background_color="black",
                tooltip=id_tooltip),

            sg.Text("user_id"),
            sg.Input(
                "", key="user_id", size=(21, 1),
                background_color="black",
                tooltip=user_id_tooltip),
            sg.Text(
                "", key="id_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pali_1", size=(15, 1)),
            sg.Input(key="pali_1", size=(50, 1), tooltip=pali_1_tooltip),
            sg.Text(
                "", key="pali_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pali_2*", size=(15, 1)),
            sg.Input(
                key="pali_2", size=(50, 1), enable_events=True,
                tooltip=pali_2_tooltip),
            sg.Text(
                "", key="pali_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("pos", size=(15, 1)),
            sg.Combo(
                POS, key="pos", size=(7, 1), enable_events=True,
                text_color=None, background_color=None,
                tooltip=pos_tooltip),
            sg.Text(
                "", key="pos_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("grammar*", size=(15, 1)),
            sg.Input(
                key="grammar", size=(50, 1), enable_events=True,
                tooltip=grammar_tooltip),
            sg.Text(
                "", key="grammar_error", size=(50, 1), text_color="red")
        ],

        [
            sg.Text("derived_from*", size=(15, 1)),
            sg.Input(
                key="derived_from", size=(50, 1),
                enable_events=True,
                tooltip=derived_from_tooltip),
            sg.Text(
                "", key="derived_from_error", size=(50, 1), text_color="red")

        ],
        [
            sg.Text("neg", size=(15, 1)),
            sg.Combo(
                    NEG_VALUES, key="neg", size=(7, 1), tooltip=neg_tooltip),
            sg.Text("", key="neg_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("verb", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    VERB_VALUES, key="verb", size=(13, 1),
                    tooltip=verb_tooltip)),
            sg.Text("", key="verb_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("trans", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    TRANS_VALUES, key="trans", size=(7, 1),
                    tooltip=trans_tooltip)),
            sg.Text(
                    "", key="trans_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("case", size=(15, 1)),
            sg.Combo(
                CASE_VALUES, key="plus_case", size=(20, 1),
                tooltip=plus_case_tooltip),
            sg.Text(
                "", key="case_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_1", size=(15, 2)),
            sg.Multiline(
                key="meaning_1", size=(50, 2), no_scrollbar=True,
                enable_events=True, tooltip=meaning_1_tooltip),
            sg.Text(
                "", key="meaning_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("add_spelling", size=(15, 1)),
            sg.Input(
                key="add_spelling", size=(25, 1),
                enable_events=True, tooltip=add_spelling_tooltip),
            sg.Button("Add", key="add_spelling_button"),
            sg.Button("Edit", key="edit_spelling_button"),
            sg.Button("Check", key="check_spelling_button"),
            sg.Text(
                "", key="add_spelling_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_lit", size=(15, 1)),
            sg.Input(
                key="meaning_lit", size=(50, 1),
                enable_events=True, tooltip=meaning_lit_tooltip),
            sg.Text(
                "", key="meaning_lit_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("meaning_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="meaning_2", size=(50, 1),
                    enable_events=True, tooltip=meaning_2_tooltip),
            ),
            sg.Text(
                "", key="meaning_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root_key", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    ROOT_VALUES, key="root_key",
                    size=(10, 1), tooltip=root_key_tooltip)),
            sg.Text(
                "", key="root_key_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family_root*", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[], key="family_root", size=(10, 1),
                    enable_events=True,
                    enable_per_char_events=True,
                    tooltip=family_root_tooltip)),
            sg.Text(
                "", key="family_root_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root_sign*", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[],
                    key="root_sign",
                    size=(10, 1),
                    enable_events=True,
                    enable_per_char_events=True,
                    tooltip=root_sign_tooltip)),
            sg.Text(
                "", key="root_sign_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("root_base", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=[],
                    key="root_base", size=(10, 1),
                    enable_per_char_events=True,
                    tooltip=root_base_tooltip)
            ),
            sg.Text(
                "", key="root_base_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family_word", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    FAMILY_WORD_VALUES,
                    key="family_word",
                    size=(49, 1),
                    tooltip=family_word_tooltip),
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
                    tooltip=family_compound_tooltip)),
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
                tooltip=construction_tooltip),
            sg.Text(
                "", key="construction_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.pin(
                 sg.Input(
                    key="add_construction", size=(20, 1),
                    tooltip=add_construction_tooltip)),
            sg.pin(
                sg.Button("Add", key="add_construction_button")),
            sg.Text(
                "", key="add_construction_error", size=(50, 1),
                text_color="red")
        ],
        [
            sg.Text("derivative", size=(15, 1)),
            sg.pin(
                sg.Combo(
                    values=DERIVATIVE_VALUES, key="derivative", size=(10, 1),
                    enable_per_char_events=True,
                    tooltip=derivative_tooltip)),
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
                    tooltip=suffix_tooltip)),
            sg.Text(
                "", key="suffix_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("phonetic", size=(15, 1)),
            sg.Multiline(
                key="phonetic", size=(50, 2), no_scrollbar=True,
                tooltip=phonetic_tooltip),
            sg.Text(
                "", key="phonetic_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("compound_type", size=(15, 1)),
            sg.pin(
                 sg.Combo(
                    COMPOUND_TYPE_VALUES, key="compound_type",
                    size=(49, 1), tooltip=compound_type_tooltip)),
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
                    tooltip=compound_construction_tooltip)),
            sg.Text(
                "", key="compound_construction_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(key="bold_cc", size=(20, 1), tooltip=bold_cc_tooltip),
            sg.Button("Bold", key="bold_cc_button"),
        ],
        [
            sg.Text("non_root_in_comps", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="non_root_in_comps", size=(50, 1),
                    tooltip=non_root_in_comps_tooltip)),
            sg.Text(
                "", key="non_root_in_comps_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("antonym", size=(15, 1)),
            sg.Input(key="antonym", size=(50, 1), tooltip=antonym_tooltip),
            sg.Text(
                "", key="antonym_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("synonym*", size=(15, 1)),
            sg.Input(
                key="synonym", size=(50, 1), enable_events=True,
                tooltip=synonym_tooltip),
            sg.Text(
                "", key="synonym_error",
                size=(50, 1), text_color="red")
        ],
        [
            sg.Text("variant", size=(15, 1)),
            sg.Input(
                key="variant", size=(50, 1), enable_events=True,
                tooltip=variant_tooltip),
            sg.Text(
                "", key="variant_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("commentary", size=(15, 5)),
            sg.Multiline(
                key="commentary", size=(50, 5), no_scrollbar=True,
                tooltip=commentary_tooltip),
            sg.Text(
                "", key="commentary_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("search for", size=(15, 1)),
            sg.Input(
                "", key="search_for", size=(20, 1),
                enable_events=True, tooltip=search_for_tooltip),
            sg.Input(
                "", key="contains", size=(20, 1),
                tooltip=contains_tooltip),
            sg.Button("Search", key="defintions_search_button"),
            sg.Text(
                "", key="search_for_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Input(
                key="notes", size=(50, 41), tooltip=notes_tooltip),
            sg.Text(
                "", key="notes_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("non_ia", size=(15, 1)),
            sg.pin(
                sg.Input(key="non_ia", size=(50, 41), tooltip=non_ia_tooltip),
            ),
            sg.Text(
                "", key="non_ia_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sanskrit*", size=(15, 1)),
            sg.Input(
                key="sanskrit", size=(50, 1), enable_events=True,
                tooltip=sanskrit_tooltip),
            sg.Text(
                "", key="sanskrit_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("cognate", size=(15, 1)),
            sg.Input(key="cognate", size=(50, 1), tooltip=cognate_tooltip),
            sg.Text(
                "", key="cognate_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("link", size=(15, 1)),
            sg.Input(key="link", size=(50, 1), tooltip=link_tooltip),
            sg.Text(
                "", key="link_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("source_1*", size=(15, 1)),
            sg.Input(
                key="source_1", size=(50, 1), enable_events=True,
                tooltip=source_1_tooltip),
            sg.Text(
                "", key="source_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sutta_1*", size=(15, 1)),
            sg.Input(
                key="sutta_1", size=(50, 1), enable_events=True,
                tooltip=sutta_1_tooltip),
            sg.Text(
                "", key="sutta_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("example_1*", size=(15, 5)),
            sg.Multiline(
                key="example_1", size=(50, 5), no_scrollbar=True,
                enable_events=True, tooltip=example_1_tooltip),
            sg.Text(
                "", key="example_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(key="bold_1", size=(20, 1), tooltip=bold_1_tooltip),
            sg.Button("Bold", key="bold_1_button"),
            sg.Button(
                "Another Eg", key="another_eg_1",
                tooltip=another_eg_1_tooltip),
            sg.Button("Lower", key="example_1_lower"),
            sg.Text("", key="bold_1_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("source_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="source_2", size=(50, 1), tooltip=source_2_tooltip)),
            sg.Text(
                "", key="source_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("sutta_2", size=(15, 1)),
            sg.pin(
                sg.Input(
                    key="sutta_2", size=(50, 1), tooltip=sutta_2_tooltip)),
            sg.Text(
                "", key="sutta_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("example_2", size=(15, 5)),
            sg.pin(
                sg.Multiline(
                    key="example_2", size=(50, 5), no_scrollbar=True,
                    tooltip=example_2_tooltip)),
            sg.Text(
                "", key="example_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.pin(
                 sg.Input(key="bold_2", size=(20, 1), tooltip=bold_2_tooltip)),
            sg.pin(
                sg.Button("Bold", key="bold_2_button")),
            sg.pin(
                sg.Button(
                    "Another Eg", key="another_eg_2",
                    tooltip=another_eg_2_tooltip)),
            sg.Button("Lower", key="example_2_lower"),
            sg.Text("", key="bold_2_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("family set*", size=(15, 1)),
            sg.Combo(
                FAMILY_SET_VALUES, key="family_set",
                size=(49, 1), tooltip=family_set_tooltip),
            sg.Text("", key="family_set_error", size=(50, 1), text_color="red")
        ],
        [
            sg.Text("stem pattern*", size=(15, 1)),
            sg.Input(
                key="stem", size=(20, 1), justification="r",
                enable_events=True, tooltip=stem_tooltip),

            sg.Combo(
                PATTERN_VALUES, key="pattern",
                size=(17, 1), tooltip=pattern_tooltip),
            sg.Input(
                "pass1", key="origin", size=(10, 1),
                tooltip=origin_tooltip),
            sg.Text(
                "", key="stem_error", size=(50, 1), text_color="red")
        ],
        ]

    tab_add_word = [
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
            sg.Button("Copy"),
            sg.Input(
                key="word_to_copy",
                size=(15, 1),
                enable_events=True,
            ),
            sg.Button("Edit", key="edit_button"),
            sg.Button("Test", key="test_internal"),
            sg.Button("Add to db", key="add_word_to_db"),
            sg.Button("Update", key="update_word")
        ],
        [
            sg.Button("Debug"),
            sg.Button("Stash", key="stash"),
            sg.Button("Unstash", key="unstash"),
            sg.Button("Summary", key="summary"),
            sg.Button("Open tests", key="open_tests"),
            sg.Button("Clear"),
            sg.Button("Close"),
        ]
    ]

    return tab_add_word
