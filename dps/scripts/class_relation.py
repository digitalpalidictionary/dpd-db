# Make sbs_class according to class topics

import re

from db.models import PaliWord, SBS
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session
from rich.console import Console
from tools.tic_toc import tic, toc

console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]changing sbs_class accordingly")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Iterate over all PaliWord instances and update their sbs_class
    for word in db_session.query(PaliWord).all():
            sbs_class = determine_sbs_class(word)
            if sbs_class:
                # if word.sbs and word.sbs.sbs_class and sbs_class == "9":
                #     print(f"for {word.pali_1} old sbs_class: {word.sbs.sbs_class}")
                if word.sbs and not word.sbs.sbs_class:
                    word.sbs.sbs_class = int(sbs_class)
                if not word.sbs:
                    word.sbs = SBS(id=word.id)
                    word.sbs.sbs_class = int(sbs_class)



    # Commit the changes to the database
    # db_session.commit()

    # Close the session
    db_session.close()
    toc()

def determine_sbs_class(word):


    
    # BPC:

    # filter inf kāma
    if (
        word.pos == "adj" and 
        word.construction.endswith("kāma")
    ):
        # print(f"Pattern: inf kāma, Word: {word.pali_1}")
        return "9"

    # filter ū masc + ū adj
    if (
        word.pattern == "ū adj" or
        word.pattern == "ū masc"
    ):
        # print(f"Pattern: ū masc & adj, Word: {word.pali_1}")
        return "6"

    # rest of BPC:

    if (
    ", comp" not in word.grammar and
    word.pos != "sandhi" and
    "reflx" not in word.grammar and
    "desid" not in word.grammar and
    "irreg" not in word.grammar and
    # "!" not in word.stem and
    "irreg" not in word.root_base
    ):
        # not caus or pass < 13
        if (
        word.verb != "caus" and
        ", pass" not in word.grammar and
        word.verb != "pass" and
        ", caus" not in word.grammar
        ):
        
            if "dat " not in word.grammar:
                # filter masc > 5
                if word.pattern == "ī adj":
                    # print(f"Pattern: ī adj, Word: {word.pali_1}")
                    return "5"
                if word.pattern == "ī masc":
                    # print(f"Pattern: ī masc, Word: {word.pali_1}")
                    return "5"
                if word.pattern == "u masc":
                    # print(f"Pattern: u masc, Word: {word.pali_1}")
                    return "6"
                if word.pattern == "ar masc":
                    # print(f"Pattern: ar masc, Word: {word.pali_1}")
                    return "6"
                if word.pattern == "ar2 masc":
                    # print(f"Pattern: ar2 masc, Word: {word.pali_1}")
                    return "6"
                
                # filter not neg < 5
                if not word.neg == "neg":

                    # filter masc < 5
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        word.pattern == "a masc"
                    ):
                        # print(f"Pattern: a masc, Word: {word.pali_1}")
                        return "2"
                    if word.pattern == "i masc":
                        # print(f"Pattern: i masc, Word: {word.pali_1}")
                        return "4"

                    # filter pr < 5
                    if "hoti" in word.pattern:
                        # print(f"Pattern: hoti, Word: {word.pali_1}")
                        return "4"
                    elif "atthi" in word.pattern:
                        # print(f"Pattern: atthi, Word: {word.pali_1}")
                        return "4"
                    else:
                        if (
                            word.pos == "pr" and 
                            "brūti" not in word.pattern and 
                            "dakkhati" not in word.pattern and 
                            "hanati" not in word.pattern and 
                            "kubbati" not in word.pattern
                        ):
                            # print(f"Pattern: pr, Word: {word.pali_1}")
                            return "3"

                    #! filter imp < 5
                    if word.pos == "imp":
                        if "!" in word.stem:
                            # print(f"Pattern: imp, Word: {word.pali_1}")
                            return "4"

                    # filter aor < 5
                    if (
                        word.pos == "aor" and 
                        "avoca" not in word.pattern and 
                        "assosi" not in word.pattern and 
                        "ddasa" not in word.pattern
                    ):
                        # print(f"Pattern: aor, Word: {word.pali_1}")
                        return "4"

                # filter neg > 5
                if word.neg == "neg":
                    if word.pos == "aor":
                        # print(f"Pattern: aor neg, Word: {word.pali_1}")
                        return "5"
                    if word.pos == "pr":
                        # print(f"Pattern: pr neg, Word: {word.pali_1}")
                        return "5"
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        word.pattern == "a masc"
                    ):
                        # print(f"Pattern: masc neg, Word: {word.pali_1}")
                        return "5"

                # filter fem
                if word.pattern == "ā fem":
                    # print(f"Pattern: ā fem, Word: {word.pali_1}")
                    return "7"
                if word.pattern == "ī fem":
                    # print(f"Pattern: ī fem, Word: {word.pali_1}")
                    return "8"
                if word.pattern == "u fem":
                    # print(f"Pattern: u fem, Word: {word.pali_1}")
                    return "8"
                if word.pattern.endswith("ar fem"):
                    # print(f"Pattern: ar fem, Word: {word.pali_1}")
                    return "8"
                if word.pattern == "ū fem":
                    # print(f"Pattern: ū fem, Word: {word.pali_1}")
                    return "8" 

            # filter pers pron
            if word.pattern == "ahaṃ pron":
                # print(f"Pattern: ahaṃ pron, Word: {word.pali_1}")
                return "5"
            if word.pattern == "tvaṃ pron":
                # print(f"Pattern: tvaṃ pron, Word: {word.pali_1}")
                return "5"

            # filter fut
            if word.pos == "fut":
                # print(f"Pattern: fut, Word: {word.pali_1}")
                return "5"

            # filter substantives (ant)
            if word.pattern == "ant adj":
                # print(f"Pattern: ant adj, Word: {word.pali_1}")
                return "6"
            if word.pattern == "ant masc":
                # print(f"Pattern: ant masc, Word: {word.pali_1}")
                return "6"

            # filter opt
            if word.pos == "opt":
                # print(f"Pattern: opt, Word: {word.pali_1}")
                return "7"

            # filter ger and abs
            if word.pos == "ger":
                # print(f"Pattern: ger, Word: {word.pali_1}")
                return "8"
            if word.pos == "abs":
                # print(f"Pattern: abs, Word: {word.pali_1}")
                return "8"

            if (
                "irreg" not in word.pattern and 
                "kamma" not in word.pattern and 
                "east" not in word.pattern and 
                "ptp " not in word.grammar and
                "pp " not in word.grammar and
                
                word.pos == "nt"
            ):
                # print(f"Pattern: nt, Word: {word.pali_1}")
                return "9"

            # filter inf
            if word.pos == "inf":
                # print(f"Pattern: inf, Word: {word.pali_1}")
                return "9"

            # filter +inf
            if "+inf" in word.plus_case:
                # print(f"Pattern: +inf, Word: {word.pali_1}")
                return "9"

            # filter dat of purpose
            if (
                "dat " in word.grammar and 
                "āya" in word.pali_1
            ):
                # print(f"Pattern: dat of purpose, Word: {word.pali_1}")
                return "9"

            # filter until-then
            if re.match(r"^y.{1,6} t.{1,6}$", word.pali_1):
                # print(f"Pattern: until-then, Word: {word.pali_1}")
                return "9"

            # filter interr
            if (
                ("interr" in word.grammar) and 
                (word.pos == "ind" or word.pos == "pron")
            ):
                # print(f"Pattern: interr, Word: {word.pali_1}")
                return "9"

            # filter prp
            if (
                word.pos == "prp"
            ):
                # print(f"Pattern: prp, Word: {word.pali_1}")
                return "10"

            # filter pron
            if (
                word.pos == "pron" and 
                "interr" not in word.grammar and
                word.pattern != "ahaṃ pron" and
                word.pattern != "tvaṃ pron"
            ):
                # print(f"Pattern: pron rest, Word: {word.pali_1}")
                return "10"

            # loc & gen abs
            if (
                "loc abs" in word.grammar or 
                "gen abs" in word.grammar
            ):
                # print(f"Pattern: loc & gen abs, Word: {word.pali_1}")
                return "10"

            # filter pp
            if word.pos == "pp":
                # print(f"Pattern: pp, Word: {word.pali_1}")
                return "11"

            if (
                "pp " in word.grammar and
                word.pattern == "a masc"
            ):
                # print(f"Pattern: masc a from pp, Word: {word.pali_1}")
                return "11"

            if (
                "pp " in word.grammar and
                word.pos == "nt"
            ):
                # print(f"Pattern: nt from pp, Word: {word.pali_1}")
                return "11"

            # filter adj
            if (
                word.pos == "adj" and 
                word.pattern != "ant adj" and 
                word.pattern != "ī adj" and
                word.pattern != "ū adj" and
                not word.construction.endswith("kāma")
            ):
                # print(f"Pattern: adj, Word: {word.pali_1}")
                return "11"

            # filter abl of separation
            if (
                "abl" in word.grammar and 
                word.pali_2.endswith("o")
            ):
                # print(f"Pattern: abl of separation, Word: {word.pali_1}")
                return "11"

            # filter numbers
            if word.pos == "card" or word.pos == "ordin":
                # print(f"Pattern: numbers, Word: {word.pali_1}")
                return "12"

            # filter adv
            if word.pos == "ind" and ", adv" in word.grammar:
                # print(f"Pattern: adv, Word: {word.pali_1}")
                return "13"

        # caus or pass > 13
        
        # filter pass
            if (
                word.verb == "pass" and 
                ", caus" not in word.grammar and 
                ", pass" in word.grammar and 
                word.verb != "caus"
            ):
                # print(f"Pattern: pass, Word: {word.pali_1}")
                return "13"

            # filter caus
            if (
                word.verb == "caus" and 
                ", pass" not in word.grammar and 
                ", caus" in word.grammar and 
                word.verb != "pass"
            ):
                # print(f"Pattern: caus, Word: {word.pali_1}")
                return "14"

            # filter caus pass
            if (
                word.verb == "caus" and 
                "pass" in word.grammar and 
                word.verb == "pass" and 
                "caus" in word.grammar
            ):
                # print(f"Pattern: caus pass, Word: {word.pali_1}")
                return "14"

            if word.verb == "caus, pass":
                # print(f"Pattern: caus, pass, Word: {word.pali_1}")
                return "14"

            # filter ptp
            if word.pos == "ptp":
                # print(f"Pattern: ptp, Word: {word.pali_1}")
                return "14"

            if (
                "ptp " in word.grammar and
                word.pattern == "a masc"
            ):
                # print(f"Pattern: masc a from ptp, Word: {word.pali_1}")
                return "14"

            if (
                "ptp " in word.grammar and
                word.pos == "nt"
            ):
                # print(f"Pattern: nt from ptp, Word: {word.pali_1}")
                return "14"


if __name__ == "__main__":
    main()
