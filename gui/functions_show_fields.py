
def make_has_values_list(values: dict) -> list[str]:
    """Return a list of all the fields with values."""
    has_value_list = []
    for key, value in values.items():
        if value:
            has_value_list.append(key)
    return has_value_list


def show_all_fields(
        values, window, flags, username, hide_list_all
):
    """Show all fields. This is the starting default."""
    for value in values:
        window[value].update(visible=True)
        window["get_family_root"].update(visible=True)
        window["get_root_base"].update(visible=True)
        window["get_root_sign"].update(visible=True)
        window["bold_cc_button"].update(visible=True)
        window["bold_2_button"].update(visible=True)
        window["another_eg_2"].update(visible=True)
        window["example_2_lower"].update(visible=True)
        flags.show_fields = False
    
    for value in hide_list_all:
        window[value].update(visible=username == "deva") 
    
    return flags


def show_root_fields(
        values, window,
        hide_list_all,
        username,
        flags
):
    "Only show root related fields."
     
    has_value_list = make_has_values_list(values)

    hide_list = [
        "meaning_2", "family_word", "family_compound", "compound_type",
        "compound_construction", "bold_cc", "bold_cc_button",
        "bold_2", "bold_2_button",
        "another_eg_2",
        "source_2", "sutta_2",
        "example_2"
    ]
    for value in values:
        window[value].update(visible=True)
    
    for value in hide_list:
        if value not in has_value_list:
            window[value].update(visible=False)
    
    for value in hide_list_all:
        window[value].update(visible=username == "deva")
    
    window["get_family_root"].update(visible=True)
    window["get_root_base"].update(visible=True)
    window["get_root_sign"].update(visible=True)
    
    flags.show_fields = False
    return flags


def show_compound_fields(
        values, window,
        hide_list_all,
        username, flags
):
    """Only show compound related fields."""
    
    has_value_list = make_has_values_list(values)

    hide_list = [
        "verb", "trans", "meaning_2", "root_key", "family_root",
        "get_family_root", "root_sign",  "get_root_sign", "root_base",
        "get_root_base", "family_word", "derivative",
        "suffix", "non_root_in_comps", "non_ia", "source_2", "sutta_2",
        "example_2", "bold_2", "bold_2_button", "example_2_lower",
        "another_eg_2",
        ]
    
    for value in values:
        window[value].update(visible=True)
        window["bold_cc_button"].update(visible=True)
        window["bold_2_button"].update(visible=True)
    
    for value in hide_list:
        if value not in has_value_list:
            window[value].update(visible=False)
    
    for value in hide_list_all:
        window[value].update(visible=username == "deva")
    
    flags.show_fields = False
    return flags


def show_word_fields(
        values, window, 
        hide_list_all, username,
        flags,
):
    "Only show word related fields."

    has_value_list = make_has_values_list(values)

    hide_list = [
        "verb", "trans", "meaning_2", "root_key",
        "family_root", "get_family_root",
        "root_sign",  "get_root_sign",
        "root_base", "get_root_base",
        "family_compound",
        "compound_type", "compound_construction",
        "bold_cc", "bold_cc_button",
        "non_root_in_comps",
        "source_2", "sutta_2", "example_2",
        "bold_2", "bold_2_button",  "example_2_lower", "another_eg_2",
        ]
    for value in values:
        window[value].update(visible=True)
    
    for value in hide_list:
        if value not in has_value_list:
            window[value].update(visible=False)
    
    for value in hide_list_all:
        window[value].update(visible=username == "deva")
    
    flags.show_fields = False
    return flags
