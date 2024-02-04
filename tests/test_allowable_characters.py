import re
from rich import print
from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.pali_alphabet import pali_alphabet
from tools.pali_alphabet import english_alphabet
from tools.pali_alphabet import english_capitals
from tools.pali_alphabet import sanskrit_alphabet
from tools.paths import ProjectPaths


def join_allowed(allowed: list) -> str:
    """Turn a list into a compiled string 
    for regex find and replace."""
    return f"({'|'.join(allowed)})"


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    # --------------------------------------------------
    # lists of allowable characterss
    # --------------------------------------------------

    # letters 
    niggahitas = ["ṁ", "ŋ"]                 #   only in definition of niggahīta
    
    pali_capitals = ["Ā"]                   #   only one in use so far, updated as needed
    
    sanskrit_capitals = ["Ṛ"]               #   only one in use so far, updated as needed
    
    greek_characters = [                    #   in names of stars
        "α", "β", "ι", "γ", "δ", "θ"]       
    
    non_ia_char = [                         #   in Tamil, Munda, etc. alphabets
        "ṉ", "ḻ", "ō", "ḵ", "ḱ", "", '̱', '̤']

    # digits
    digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

    one_two_three = ["1", "2", "3"]         #   in grammar 1st 2nd and 3rd person         
    
    super_digits = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]

    # punctuation
    space = [" "]
    comma = [","]
    semicolon = [";"]
    fullstop = ["\\."]
    question = ["\\?"]
    exclamation = ["!"]
    brackets = ["\\(", "\\)"]
    dash = ["\\-"]
    ampersand = ["&"]
    root = ["√"]
    plus = ["\\+"]
    equals = ["\\="]                        #   used in measures 7 x = 1 y
    percent = ["%"]                         #   100% 
    forward_slash = ["\\/"]                 #   used in factions 1/16th
    dot_dot_dot = ["…"]                     #   rather than ...
    star = ["\\*"]                          #   used as ṇ anubandha in grammatical terms
    apostrophe = ["'"]                      #   FIXME this should get upgraded to quotation marks etc

    # special groups
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

    # --------------------------------------------------
    # allowable characters in each field
    # --------------------------------------------------

    pali_1_allowed = (
        pali_alphabet + 
        fullstop + 
        space + 
        digits
    )
    
    pali_2_allowed = (
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
        space +
        plus
    )

    # --------------------------------------------------
    # test data, tuple of column and allowable characters
    # --------------------------------------------------
 
    tests_data = [
        ("pali_1", pali_1_allowed),
        ("pali_2", pali_2_allowed),
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
    ]

    # --------------------------------------------------
    # the sharp end of the stick
    # --------------------------------------------------

    for test_data in tests_data:
        # setup variables
        column, allowed = test_data
        allowed = join_allowed(allowed)
        remainder = "" 
        print(f"[green]{column:<40}", end="")
        
        for i in db:    
            # grab the text from the column
            text = getattr(i, column)
            
            # remove all allowable characters
            oops = re.sub(allowed, "", text)

            # compile the remaining characters
            if oops:
                # print(i.pali_1, oops)
                remainder += oops

        print(f"[white]{[char for char in set(remainder)]}")

if __name__ == "__main__":
    main()

    # root_key_allowed = ()
    # root_sign_allowed = ()
    # root_base_allowed = ()
    # family_root_allowed = ()
    # family_word_allowed = ()
    # family_compound_allowed = ()
    # family_set_allowed = ()
    # construction_allowed = ()
    # derivative_allowed = ()
    # suffix_allowed = ()
    # phonetic_allowed = ()
    # compound_type_allowed = ()
    # compound_construction_allowed = ()
    # non_root_in_comps_allowed = ()
    # source_1_allowed = ()
    # sutta_1_allowed = ()
    # example_1_allowed = ()
    # source_2_allowed = ()
    # sutta_2_allowed = ()
    # example_2_allowed = ()
    # antonym_allowed = ()
    # synonym_allowed = ()
    # variant_allowed = ()
    # commentary_allowed = ()
    # notes_allowed = ()
    # cognate_allowed = ()
    # link_allowed = ()
    # origin_allowed = ()
    # stem_allowed = ()
    # pattern_allowed = ()
    # created_at_allowed = ()
    # updated_at_allowed = ()