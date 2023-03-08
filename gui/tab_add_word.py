from db_helpers import get_next_ids
from tools.pos import POS
from db_helpers import get_verb_values
from db_helpers import get_case_values
from db_helpers import get_root_key_values
from db_helpers import get_family_word_values
from db_helpers import get_derivative_values
from db_helpers import get_compound_type_values

VERB_VALUES = get_verb_values()
TRANS_VALUES = ["", "trans", "intrans", "ditrans"]
NEG_VALUES = ["", "neg", "neg x2"]
CASE_VALUES = get_case_values()
ROOT_VALUES = get_root_key_values()
FAMILY_WORD_VALUES = get_family_word_values()
DERIVATIVE_VALUES = ["", "kicca", "kita", "taddhita"]
COMPOUND_TYPE_VALUES = get_compound_type_values()


def make_tab_add_word(sg):

    id, user_id = get_next_ids()

    add_word_layout = [
        [
            sg.Text("id", size=(15, 1, )),
            sg.Input(f"{id}", key="id", size=(20, 1)),
            sg.Text("user_id"),
            sg.Input(f"{user_id}", key="user_id", size=(21, 1))
        ],
        [
            sg.Text("pali_1", size=(15, 1)),
            sg.Input(key="pali_1", size=(50, 1))
        ],
        [
            sg.Text("pali_2", size=(15, 1)),
            sg.Input(key="pali_2", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("pos", size=(15, 1)),
            sg.Combo(POS, key="pos", size=(7, 1), enable_events=True),
        ],
        [
            sg.Text("grammar", size=(15, 1)),
            sg.Input(key="grammar", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("derived_from", size=(15, 1)),
            sg.Input(key="derived_from", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("verb", size=(15, 1)),
            sg.Combo(VERB_VALUES, key="verb", size=(13, 1)),

            sg.Text("trans"),
            sg.Combo(TRANS_VALUES, key="trans", size=(7, 1))
        ],
        [
            sg.Text("neg", size=(15, 1)),
            sg.Combo(NEG_VALUES, key="neg", size=(7, 1)),

            sg.Text("case "),
            sg.Combo(CASE_VALUES, key="plus_case", size=(20, 1))
        ],
        [
            sg.Text("meaning_1", size=(15, 2)),
            sg.Multiline(key="meaning_1", size=(50, 2), no_scrollbar=True)
        ],
        [
            sg.Text("meaning_lit", size=(15, 1)),
            sg.Input(key="meaning_lit", size=(50, 1))
        ],
        [
            sg.Text("meaning_2", size=(15, 1)),
            sg.Input(key="meaning_2", size=(50, 1))
        ],
        [
            sg.Text("root_key", key="root_key_label", size=(15, 1)),
            sg.Combo(ROOT_VALUES, key="root_key", size=(8, 1)),

            sg.Text("family root", key="family_root_label"),
            sg.Combo(
                values=[], key="family_root", size=(28, 1),
                enable_events=True,
                enable_per_char_events=True),
        ],
        [
            sg.Text("root_sign", size=(15, 1)),
            sg.Combo(
                values=[],
                key="root_sign",
                size=(10, 1),
                enable_events=True,
                enable_per_char_events=True),

            sg.Text("root_base  "),
            sg.Combo(
                values=[],
                key="root_base", size=(26, 1),
                enable_per_char_events=True),
        ],
        [
            sg.Text("family_word", size=(15, 1)),
            sg.Combo(
                FAMILY_WORD_VALUES, key="family_word", size=(49, 1))
        ],
        [
            sg.Text("family_compound", size=(15, 1)),
            sg.Input(key="family_compound", size=(50, 1))
        ],
        [
            sg.Text("construction", size=(15, 1)),
            sg.Input(
                key="construction", size=(50, 1),
                enable_events=True)
        ],
        [
            sg.Text("derivative", size=(15, 1)),
            sg.Combo(
                values=DERIVATIVE_VALUES, key="derivative", size=(10, 1),
                enable_per_char_events=True),

            sg.Text("suffix"),
            sg.Input(key="suffix", size=(32, 1), enable_events=True),
        ],
        [
            sg.Text("phonetic", size=(15, 1)),
            sg.Multiline(key="phonetic", size=(50, 2), no_scrollbar=True)
        ],
        [
            sg.Text("compound_type", size=(15, 1)),
            sg.Combo(
                COMPOUND_TYPE_VALUES, key="compound_type",
                size=(49, 1)),
        ],
        [
            sg.Text("compound_construction", size=(15, 1)),
            sg.Input(
                key="compound_construction", size=(50, 1),
                enable_events=True),
        ],
        [
            sg.Text("antonym", size=(15, 1)),
            sg.Input(key="antonym", size=(50, 1))
        ],
        [
            sg.Text("synonym", size=(15, 1)),
            sg.Input(key="synonym", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("variant", size=(15, 1)),
            sg.Input(key="variant", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("commentary", size=(15, 4)),
            sg.Multiline(key="commentary", size=(50, 4), no_scrollbar=True)
        ],
        [
            sg.Text("notes", size=(15, 1)),
            sg.Input(key="notes", size=(50, 41))
        ],
        [
            sg.Text("non_ia", size=(15, 1)),
            sg.Input(key="non_ia", size=(50, 41))
        ],
        [
            sg.Text("sanskrit", size=(15, 1)),
            sg.Input(key="sanskrit", size=(50, 1), enable_events=True)
        ],
        [
            sg.Text("cognate", size=(15, 1)),
            sg.Input(key="cognate", size=(50, 1))
        ],
        [
            sg.Text("link", size=(15, 1)),
            sg.Input(key="link", size=(50, 1))
        ],
        [
            sg.Text("source_1", size=(15, 1)),
            sg.Input(key="source_1", size=(50, 1)),
        ],
        [
            sg.Text("sutta_1", size=(15, 1)),
            sg.Input(key="sutta_1", size=(50, 1)),
        ],
        [
            sg.Text("example_1", size=(15, 4)),
            sg.Multiline(
                key="example_1", size=(50, 4), no_scrollbar=True,
                enable_events=True)
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(key="bold_1", size=(20, 1)),
            sg.Button("Bold", key="bold_1_button"),
            sg.Button("Another Eg", key="another_eg_1"),
        ],
        [
            sg.Text("source_2", size=(15, 1)),
            sg.Input(key="source_2", size=(50, 1)),
        ],
        [
            sg.Text("sutta_2", size=(15, 1)),
            sg.Input(key="sutta_2", size=(50, 1)),
        ],
        [
            sg.Text("example_2", size=(15, 4)),
            sg.Multiline(key="example_2", size=(50, 4), no_scrollbar=True)
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Input(key="bold_2", size=(20, 1)),
            sg.Button("Bold", key="bold_2_button")
        ],
        [
            sg.Text("family_set", size=(15, 1)),
            sg.Input(key="family_set", size=(50, 1))
        ],
        [
            sg.Text("stem pattern", size=(15, 1)),
            sg.Input(key="stem", size=(20, 1), justification="r"),
            sg.Input(key="pattern", size=(17, 1)),
            sg.Input("pass1", key="origin", size=(10, 1))
        ],
        ]

    helper_layout = [[
        sg.Multiline(
            "",
            key="message_display",
            size=(25, 27),
            autoscroll=True,
            expand_y=True,
            no_scrollbar=True
        ),
    ]]

    tab_add_word = [
        [
            sg.Column(
                add_word_layout,
                scrollable=True,
                vertical_scroll_only=True,
                expand_y=True,
                size=(None, 900)
            ),
            sg.Column(
                helper_layout,
                expand_y=True,

            ),
        ],
        [
            sg.Button("Copy"),
            sg.Input(
                key="word_to_copy",
                size=(15, 1),
                enable_events=True,
            ),
            sg.Button("Clear"),
            sg.Button("Add to db", key="add_word_db"),
            sg.Button("Update", key="update_word"),
            sg.Button("Debug"),
            sg.Button("Close")
        ]
    ]

    return tab_add_word
