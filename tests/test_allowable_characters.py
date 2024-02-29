import re
import pyperclip
from rich import print
from db.get_db_session import get_db_session
from db.models import DpdHeadwords, DpdRoots

from tools.db_search_string import db_search_string
from tools.pali_alphabet import pali_alphabet
from tools.pali_alphabet import english_alphabet
from tools.pali_alphabet import english_capitals
from tools.pali_alphabet import sanskrit_alphabet
from tools.paths import ProjectPaths
from tools.unicode_char import unicode_char

from sqlalchemy.orm import joinedload

from tools.configger import config_test

class AllowableCharacters():
    """Defined lists of allowable characters,
    and the characters allowable in each field."""

    # --------------------------------------------------
    # lists of allowable characters
    # --------------------------------------------------

    # letters 
    niggahitas = ["ṁ", "ŋ"]                 #   only in definition of niggahīta
    
    pali_capitals = ["Ā", "Ñ", "Ṭ"]         #   update as needed
    
    sanskrit_capitals = [                   #   update as needed
        "Ṛ", "V", "B", "Ś"]     
    
    greek_characters = [                    #   in names of stars
        "α", "β", "ι", "γ", "δ", "θ"]       
    
    non_ia_char = [                         #   in Tamil, Munda, etc. alphabets
        "ṉ", "ḻ", "ō", "ḵ", "ḱ", "", '̱', '̤']
    
    german_characters = ["ü"]

    cyrillic_characters = [
        "а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я"
        ]
    
    cyrillic_capitals = [
        "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю", "Я"
        ]

    number_ru = ['№']

    # digits
    digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

    one_two_three = ["1", "2", "3"]         #   in grammar 1st 2nd and 3rd person         
    
    super_digits = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]

    # punctuation
    ampersand = ["&"]
    apostrophe = ["'"]                      #   FIXME this should get upgraded to quotation marks etc
    brackets = ["\\(", "\\)"]
    colon = [":"]
    comma = [","]
    dash = ["\\-"]
    dot_dot_dot = ["…"]                     #   rather than ...
    equals = ["\\="]                        #   to show measures 7 x = 1 y
    exclamation = ["!"]
    forward_slash = ["\\/"]                 #   to show factions 1/16th
    fullstop = ["\\."]
    greater_than = [">"]                    #   to show phonetic development
    hash = ["#"]                            #   only in web links
    less_than = ["<"]                       #   to show derivation from
    low_line = ["_"]                        #   only in weblinks
    new_line = ["\n"]
    percent = ["%"]                         #   to show 100% 
    plus = ["\\+"]
    question = ["\\?"]
    root = ["√"]
    semicolon = [";"]
    space = [" "]
    square_brackets = ["\\[", "\\]"]
    star = ["\\*"]                          #   to show ṇ anubandha in grammatical terms and imaginary word forms

    # special groups

    section = ["§"]

    bold = ["<b>", "<\\/b>"]

    italic = ["<i>", "<\\/i>"]

    neg = ["neg", "x2"]
    
    verbs = [
        "caus", "deno", "desid","impers", "intens", "pass"]
    
    trans = ["trans", "intrans", "ditrans"]
    
    plus_case = [
        "\\+nom", "\\+acc", "\\+instr", "\\+dat", "\\+abl", "\\+gen", "\\+loc", 
        "\\+adv", "\\+card", "\\+inf", 
        "\\+aor", "\\+opt", "\\+imp", "\\+voc", ]
    
    and_or = ["&", "or"]
    
    non_ia_languages = [
        "Austric", 
        "Kannada",
        "Malayalam", "Mārāṭhi", "Munda", 
        "Old Tamil", 
        "Proto-Dravidian", 
        "Santali",
        "Tamil", "Telugu", 
        ]
    
    derivatives = ["kita", "kicca", "taddhita"]

    phonetic_terms = [
        "Kacc", "with metrically", "lengthened", "shortened",
        "before", "vowel", "under the influence of", "expansion",
        "contraction", "sk ṛ", "nasalization"]
    
    compound_types = [
        "abyayībhāva", "digu", "tappurisa", "dvanda", "kammadhāraya",
        "bahubbīhi", "missaka", "alutta", "dvanda",
        "dutiyā", "tatiyā", "catutthī", "pañcamī", "chaṭṭhī", "sattamī",
        "tuṃpaccaya"]
    
    source = [
        "kaccāyana", "padarūpasiddhi", "saddanīti", "padamālā", "bālāvatāra",
        "buddhavandana", "a", "t"]
    
    origins = [
        "pass1", "pass2", "dps", "sandhi", "cpd", "dps", "ncped"
    ]
    
    patterns = [
    "paccabyādhi", "pokkharaṇī", "dakkhati", "arahant", "kubbati",
    "bhavant", "ekacca", "issati", "lattha", "kayirā", "addasā",
    "brahma", "hanati", "assosi", "parisā", "jāniyā", "natthi",
    "imperf", "letter", "ubhaya", "karoti", "jantu", "ssati", "kamma",
    "vajjā", "ratti", "brūti", "avaca", "ddasa", "irreg", "addha",
    "mātar", "atthi", "dammi", "avoca", "ordin", "santa", "dajjā",
    "issaṃ", "essa", "card", "nadī", "ubha", "kari", "masc", "māna",
    "anta", "hari", "onta", "pivi", "jāti", "aṃsu", "isuṃ", "east",
    "yuva", "enta", "kaci", "hiti", "catu", "pron", "kati", "iṃsu",
    "hoti", "perf", "tvaṃ", "root", "issa", "ahaṃ", "rāja", "eyya",
    "siyā", "cond", "hosi", "fem", "āha", "opt", "eti", "amu", "oti",
    "eka", "prp", "ati", "āti", "ant", "āsi", "fut", "ima", "aka",
    "aor", "adj", "āna", "dvi", "ssa", "esi", "ptp", "cha", "ar2",
    "ya", "a1", "ka", "ve", "pp", "pl", "ta", "pr", "as", "ar", "aī",
    "go", "nt", "ti", "a2", "i2", "ā", "i", "ṃ", "2", "ī", "u", "ū",
    "a", "o" ]

    sbs_chanting_book_sorces = ["Sri Lanka", "Trad", "Thai", "MJG"]
    

    # --------------------------------------------------
    # allowable characters in each field
    # --------------------------------------------------

    lemma_1_allowed = (
        pali_alphabet + 
        fullstop + 
        space + 
        digits
    )
    
    lemma_2_allowed = (
        pali_alphabet + 
        fullstop + 
        space + 
        digits + 
        dash
    )
    
    pos_allowed = (
        english_alphabet
    )
    
    grammar_allowed = (
        pali_alphabet + 
        english_alphabet +
        space +
        comma + 
        one_two_three + 
        ampersand + 
        root +
        plus +
        question
    )
    
    derived_from_allowed = (
        pali_alphabet +
        space +
        root)
    
    neg_allowed = (
        neg +
        space
    )
    
    verb_allowed = (
        verbs +
        space +
        comma
    )
    
    trans_allowed = (
        trans
    )
    
    plus_case_allowed = (
        plus_case +
        and_or +
        space
    )
    
    meaning_1_allowed = (
        # letters
        english_alphabet +
        english_capitals +
        pali_alphabet +
        pali_capitals +
        niggahitas +
        sanskrit_capitals +
        greek_characters +
        
        # digits
        digits +
        super_digits +
        
        # punctuation
        space +
        comma + 
        semicolon +
        fullstop +
        exclamation + 
        question +
        apostrophe +
        brackets +
        percent +
        forward_slash + 
        dot_dot_dot + 
        star +
        root + 
        equals +
        ampersand +
        dash
    )
    
    non_ia_allowed = (
        pali_alphabet +
        english_alphabet +
        non_ia_char +
        non_ia_languages +
        space +
        comma + 
        apostrophe +
        brackets
    )
    
    sanskrit_allowed = (
        sanskrit_alphabet +
        sanskrit_capitals +
        english_alphabet +
        digits +
        space +
        comma + 
        fullstop +
        plus + 
        brackets +
        square_brackets +
        dash +
        forward_slash +
        less_than
    )

    root_key_allowed = (
        pali_alphabet +
        digits +
        space +
        root
    )

    root_sign_allowed = (
        pali_alphabet +
        space +
        plus +
        star
    )

    root_base_allowed = (
        pali_alphabet +
        english_alphabet +
        space +
        comma +
        plus +
        root +
        star +
        greater_than +
        brackets +
        square_brackets
    )

    family_root_allowed = (
        pali_alphabet +
        root +
        space
    )

    family_word_allowed = (
        pali_alphabet +
        digits
    )

    family_compound_allowed = (
        pali_alphabet +
        digits +
        space
    )

    family_set_allowed = (
        pali_alphabet +
        english_alphabet +
        english_capitals +
        digits +
        space +
        comma +
        semicolon
    )

    construction_allowed = (
        pali_alphabet +
        space +
        comma +
        plus +
        root +
        star +
        question +
        greater_than +      
        bold +              #   FIXME remove?
        brackets +
        square_brackets +
        new_line
    )

    derivative_allowed = (
        derivatives
    )

    suffix_allowed = (
        pali_alphabet +
        star
    )

    phonetic_allowed = (
        phonetic_terms +
        pali_alphabet +
        digits +
        space +
        comma +
        plus +
        root +
        greater_than +
        new_line +
        brackets
    )

    compound_type_allowed = (
        compound_types +
        space +
        greater_than
    )

    compound_construction_allowed = (
        pali_alphabet +
        space +
        plus +
        bold +
        new_line
    )

    non_root_in_comps_allowed = (
        pali_alphabet
    )

    source_allowed = (
        english_capitals +
        source +
        digits +
        space +
        fullstop +
        dash
    )
    sutta_allowed = (
        pali_alphabet +
        digits +
        space +
        comma +                 #   for subsections of suttas
        new_line
    )

    example_allowed = (
        pali_alphabet +
        digits +
        space +
        comma +
        fullstop +
        question +
        exclamation +
        apostrophe +
        dash +
        dot_dot_dot +
        brackets +
        square_brackets +       #   for CST notes [theri. ap. 47]
        equals +                #   only in CST notes
        plus +                  #   only in CST notes
        bold +
        new_line
    )

    ant_syn_var_allowed = (
        pali_alphabet +
        space +
        comma
    )

    commentary_allowed = (
        pali_alphabet +
        english_capitals +
        digits +
        space +
        comma +
        fullstop +
        question +
        apostrophe +
        dash +
        dot_dot_dot +
        brackets +
        bold +
        new_line
    )

    notes_allowed = (
        pali_alphabet +
        pali_capitals +
        english_alphabet +
        english_capitals +
        sanskrit_alphabet +
        sanskrit_capitals +
        german_characters +
        digits +
        space +
        comma +
        semicolon +
        colon +
        fullstop +
        exclamation +
        question +
        apostrophe +
        dash +
        dot_dot_dot +
        new_line +
        plus +
        star +
        root +
        equals +                # in measures 1x = 12y
        forward_slash +         # in fractions 1/12th
        greater_than +          # in derivations na > an 
        brackets +
        bold + 
        italic +
        section
    )

    cognate_allowed = (
        english_alphabet +
        english_capitals +
        space +
        comma +
        star +                   # for imaginary derivations *n-mrt-os (PIE)
        brackets +
        greater_than +           # in derivations na > an
        dash
    )

    link_allowed = (
        english_alphabet +
        english_capitals +
        digits +
        space +
        fullstop +
        forward_slash +
        colon +
        dash + 
        hash +
        percent +
        brackets +
        low_line +
        new_line
    )

    origin_allowed = (
        origins
    )

    stem_allowed = (
        pali_alphabet +
        exclamation +
        star +
        dash 
    )

    pattern_allowed = (
        patterns +
        space
    )

    # --------------------------------------------------
    # allowable characters for Russian fields
    # --------------------------------------------------

    ru_meaning_allowed = (
        # letters
        cyrillic_characters +
        cyrillic_capitals +
        pali_alphabet +
        pali_capitals +
        niggahitas +
        sanskrit_capitals +
        greek_characters +
        
        # digits
        digits +
        super_digits +
        
        # punctuation
        space +
        comma + 
        semicolon +
        fullstop +
        exclamation + 
        question +
        apostrophe +
        brackets +
        percent +
        forward_slash + 
        dot_dot_dot + 
        star +
        root + 
        equals +
        ampersand +
        dash +
        number_ru
    )

    root_meaning_ru_allowed = (
        cyrillic_characters +
        space +
        comma 
    )

    ru_notes_allowed = (
        pali_alphabet +
        pali_capitals +
        cyrillic_characters +
        cyrillic_capitals +
        english_alphabet +
        english_capitals +
        sanskrit_alphabet +
        sanskrit_capitals +
        german_characters +
        digits +
        space +
        comma +
        semicolon +
        colon +
        fullstop +
        exclamation +
        question +
        apostrophe +
        dash +
        dot_dot_dot +
        new_line +
        plus +
        star +
        root +
        equals +                # in measures 1x = 12y
        forward_slash +         # in fractions 1/12th
        greater_than +          # in derivations na > an 
        brackets +
        bold + 
        italic +
        section +
        number_ru +
        niggahitas
    )


    # --------------------------------------------------
    # allowable characters for SBS fields
    # --------------------------------------------------

    sbs_category_allowed = (
        english_alphabet +
        digits +
        low_line
    )

    sbs_source_allowed = (
        english_capitals +
        source +
        english_alphabet +
        digits +
        space +
        fullstop +
        dash
    )
    
    sbs_chant_pali_allowed = (
        pali_alphabet +
        pali_capitals +
        english_capitals +
        space +
        apostrophe +
        dash
    )

    sbs_chant_english_allowed = (
        pali_alphabet +
        english_alphabet +
        english_capitals +
        space +
        apostrophe +
        dash
    )

    sbs_chapter_allowed = (
        pali_alphabet +
        english_alphabet +
        english_capitals +
        space
    )


    # --------------------------------------------------
    # test data, tuple of column and allowable characters
    # --------------------------------------------------
 
    tests_data = [
        ("lemma_1", lemma_1_allowed),
        ("lemma_2", lemma_2_allowed),
        ("pos", pos_allowed),
        ("grammar", grammar_allowed),
        ("derived_from", derived_from_allowed),
        ("neg", neg_allowed),
        ("verb", verb_allowed),
        ("trans", trans_allowed),
        ("plus_case", plus_case_allowed),
        ("meaning_1", meaning_1_allowed),
        ("meaning_lit", meaning_1_allowed),
        ("meaning_2", meaning_1_allowed),
        ("non_ia", non_ia_allowed),
        ("sanskrit", sanskrit_allowed),
        ("root_key", root_key_allowed),
        ("root_sign", root_sign_allowed),
        ("root_base", root_base_allowed),
        ("family_root", family_root_allowed),
        ("family_word", family_word_allowed),
        ("family_compound", family_compound_allowed),
        ("family_set", family_set_allowed),
        ("construction", construction_allowed),
        ("derivative", derivative_allowed),
        ("suffix", suffix_allowed),
        ("phonetic", phonetic_allowed),
        ("compound_type", compound_type_allowed),
        ("compound_construction", compound_construction_allowed),
        # ("non_root_in_comps", )
        ("source_1", source_allowed),
        ("sutta_1", sutta_allowed),
        ("example_1", example_allowed),
        ("source_2", source_allowed),
        ("sutta_2", sutta_allowed),
        ("example_2", example_allowed),
        ("antonym", ant_syn_var_allowed),
        ("synonym", ant_syn_var_allowed),
        ("variant", ant_syn_var_allowed),
        ("var_phonetic", ant_syn_var_allowed),
        ("var_text", ant_syn_var_allowed),
        ("commentary", commentary_allowed),
        ("notes", notes_allowed),
        ("cognate", cognate_allowed),
        ("link", link_allowed),
        ("origin", origin_allowed),
        ("stem", stem_allowed),
        ("pattern", pattern_allowed), 
    ]

    sbs_data = [
        ("sbs_meaning", meaning_1_allowed),
        ("sbs_category", sbs_category_allowed),
        
        ("sbs_source_1", sbs_source_allowed),
        ("sbs_sutta_1", sutta_allowed),
        ("sbs_example_1", example_allowed),
        ("sbs_chant_pali_1", sbs_chant_pali_allowed),
        ("sbs_chant_eng_1", sbs_chant_english_allowed),
        ("sbs_chapter_1", sbs_chapter_allowed),

        ("sbs_source_2", sbs_source_allowed),
        ("sbs_sutta_2", sutta_allowed),
        ("sbs_example_2", example_allowed),
        ("sbs_chant_pali_2", sbs_chant_pali_allowed),
        ("sbs_chant_eng_2", sbs_chant_english_allowed),
        ("sbs_chapter_2", sbs_chapter_allowed),

        ("sbs_source_3", sbs_source_allowed),
        ("sbs_sutta_3", sutta_allowed),
        ("sbs_example_3", example_allowed),
        ("sbs_chant_pali_3", sbs_chant_pali_allowed),
        ("sbs_chant_eng_3", sbs_chant_english_allowed),
        ("sbs_chapter_3", sbs_chapter_allowed),

        ("sbs_source_4", sbs_source_allowed),
        ("sbs_sutta_4", sutta_allowed),
        ("sbs_example_4", example_allowed),
        ("sbs_chant_pali_4", sbs_chant_pali_allowed),
        ("sbs_chant_eng_4", sbs_chant_english_allowed),
        ("sbs_chapter_4", sbs_chapter_allowed),

        ("sbs_notes", notes_allowed),
    ]

    ru_data = [
        ("ru_meaning", ru_meaning_allowed),
        ("ru_meaning_lit", ru_meaning_allowed),
        ("ru_meaning_raw", ru_meaning_allowed),
        ("ru_notes", ru_notes_allowed),
    ]

    roots_data = [
        ("sanskrit_root_ru_meaning", root_meaning_ru_allowed),
        ("root_ru_meaning", root_meaning_ru_allowed)
    ]

    dps_tests_data = sbs_data + ru_data

    if config_test("user", "username", "deva"):
        tests_data = dps_tests_data

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    if config_test("user", "username", "deva"):
        db = db_session.query(DpdHeadwords).options(joinedload(DpdHeadwords.sbs), joinedload(DpdHeadwords.ru)).all()
    else:
        db = db_session.query(DpdHeadwords)

    a = AllowableCharacters()

    debug = False
    error_list = []

    for test_data in a.tests_data:
        # setup variables
        column, allowed = test_data
        print(f"[green]{column:<40}", end="")
        allowed = join_allowed(allowed)
        if debug:
            print()
            print(allowed)
        remainder = "" 
        
        for i in db:    
            # grab the text from the column
            if column.startswith("sbs_"):
                if i.sbs:
                    text = getattr(i.sbs, column)
                else:
                    text = ""
            elif column.startswith("ru_"):
                if i.ru:
                    text = getattr(i.ru, column)
                else:
                    text = ""
            else:
                text = getattr(i, column)
            
            # remove all allowable characters
            oops = re.sub(allowed, "", text)
            
            # compile the remaining characters
            if oops:
                if debug:
                    print(f"{i.lemma_1} '{oops}'")
                remainder += oops
                error_list += [i.lemma_1]

        print(f"[white]{[char for char in set(remainder)]}", end=" ")

        # unicode numbers for obscure characters
        unicode_remainder = [ord(char) for char in set(remainder)]
        for error in unicode_remainder:
            print("\\u{:04x}".format(error), end=" ")
        print()    

        if debug:
            # print db serach string
            error_search_string = db_search_string(error_list)
            pyperclip.copy(error_search_string)
            print("[green]db search string copied to clipboard")


def test_allowable_characters_gui(values: dict[str, str]) -> dict[str, str]:
    """Test allowabl characters in gui values dict.
    Return a dict of probems."""
    a = AllowableCharacters()

    error_dict: dict[str, str] = {}
    for test_data in a.tests_data:
        column, allowed = test_data
        allowed = join_allowed(allowed)
        
        if column in values:
            # grab the text from the column
            text = values[column]
            
            # remove all allowable characters
            oops = re.sub(allowed, "", text)
            
            # add to error dict
            error_string = ""
            if oops:
                error_list = []
                error_list.extend(char + unicode_char(char) for char in set(oops))
                error_string = " ".join(error_list)
                error_dict[column] = error_string
    
    return error_dict


def test_allowable_characters_gui_dps(values: dict[str, str]) -> dict[str, str]:
    """Test allowabl characters in dps tab gui values dict.
    Return a dict of probems."""
    a = AllowableCharacters()

    error_dict: dict[str, str] = {}
    for dps_test_data in a.dps_tests_data:
        column, allowed = dps_test_data
        allowed = join_allowed(allowed)

        # Strip the 'dps_' prefix from the keys in the values dictionary
        dps_values = {key.replace('dps_', ''): value for key, value in values.items()}

        if column in dps_values:
            # grab the text from the column
            text = dps_values[column]
            
            # remove all allowable characters
            oops = re.sub(allowed, "", text)
            
            # add to error dict
            error_string = ""
            if oops:
                error_list = []
                error_list.extend(char + unicode_char(char) for char in set(oops))
                error_string = " ".join(error_list)
                error_dict[column] = error_string
        else:
            print(f"{column} not in dps_values")
    
    return error_dict


def check_root_db():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdRoots)

    a = AllowableCharacters()

    debug = False
    error_list = []

    for root_data in a.roots_data:
        # setup variables
        column, allowed = root_data
        print(f"[green]{column:<40}", end="")
        allowed = join_allowed(allowed)
        if debug:
            print()
            print(allowed)
        remainder = "" 
        
        for i in db:    
            # grab the text from the column
            text = getattr(i, column)
            
            # remove all allowable characters
            oops = re.sub(allowed, "", text)
            
            # compile the remaining characters
            if oops:
                if debug:
                    print(f"{i.root} '{oops}'")
                remainder += oops
                error_list += [i.root]

        print(f"[white]{[char for char in set(remainder)]}", end=" ")

        # unicode numbers for obscure characters
        unicode_remainder = [ord(char) for char in set(remainder)]
        for error in unicode_remainder:
            print("\\u{:04x}".format(error), end=" ")
        print()    

        if debug:
            # print db serach string
            error_search_string = db_search_string(error_list)
            pyperclip.copy(error_search_string)
            print("[green]db search string copied to clipboard")


def join_allowed(allowed: list) -> str:
    """Turn a list into a compiled string for regex 
    find and replace."""
    return f"({'|'.join(allowed)})"

if __name__ == "__main__":
    main()
    if config_test("user", "username", "deva"):
        check_root_db()

    # x = test_allowable_characters_gui({"lemma_1": "®±²£¥"})
    # print(x)
