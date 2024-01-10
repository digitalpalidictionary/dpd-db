
import re

from db.models import PaliWord
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
        if word.sbs and not word.sbs.sbs_class:
            word.sbs.sbs_class = determine_sbs_class(word)
            if word.sbs.sbs_class == "14":
                print(f"{word.pali_1}: {word.sbs.sbs_class}")

    # Commit the changes to the database
    # db_session.commit()

    # Close the session
    db_session.close()
    toc()

def determine_sbs_class(word):


    
    # BPC:
    if (
    "comp" not in word.grammar and
    word.pos != "sandhi" and
    "reflx" not in word.grammar and
    "desid" not in word.grammar and
    "irreg" not in word.grammar and
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
                    return "5"
                if word.pattern == "ī masc":
                    return "5"
                if word.pattern == "u masc":
                    return "6"
                if word.pattern == "ar masc":
                    return "6"
                if word.pattern == "ar2 masc":
                    return "6"
                
                # filter not neg < 5
                if not word.neg == "neg":

                    # filter masc < 5
                    if word.pattern == "a masc":
                        return "2"
                    if word.pattern == "i masc":
                        return "4"

                    # filter pr < 5
                    if "hoti" in word.pattern:
                        return "4"
                    elif "atthi" in word.pattern:
                        return "4"
                    else:
                        if (
                            word.pos == "pr" and 
                            "brūti" not in word.pattern and 
                            "dakkhati" not in word.pattern and 
                            "hanati" not in word.pattern and 
                            "kubbati" not in word.pattern
                        ):
                            return "3"

                    # filter imp < 5
                    if word.pos == "imp":
                        return "4"

                    # filter aor < 5
                    if (
                        word.pos == "aor" and 
                        "avoca" not in word.pattern and 
                        "assosi" not in word.pattern and 
                        "ddasa" not in word.pattern
                    ):
                        return "4"
                
                # filter neg > 5

                elif word.neg == "neg":
                    if word.pos == "aor":
                        return "5"
                    if word.pos == "pr":
                        return "5"
                    if word.pos == "masc":
                        return "5"

            # filter pers pron
            if word.pattern == "ahaṃ pron":
                return "5"
            if word.pattern == "tvaṃ pron":
                return "5"

            # filter fut

            if word.pos == "fut":
                return "5"

            # filter ū masc + ū adj
            if word.pattern == "ū adj":
                return "6"
            if word.pattern == "ū masc":
                return "6"

            # filter substantives (ant)
            if word.pattern == "ant adj":
                return "6"
            if word.pattern == "ant masc":
                return "6"

            # filter opt
            if word.pattern == "opt":
                return "7"

            # filter ger and abs
            if word.pattern == "ger":
                return "8"
            if word.pattern == "abs":
                return "8"

            # filter fem
            if word.pattern == "ā fem":
                return "7"

            if word.pattern == "ī fem":
                return "8"
            if word.pattern == "u fem":
                return "8"
            if word.pattern == "ar fem":
                return "8"
            if word.pattern == "ū fem":
                return "8" 

            if (
                "irreg" not in word.pattern and 
                "kamma" not in word.pattern and 
                "east" not in word.pattern and 
                word.pos == "nt"
            ):
                return "9"

            # filter inf
            if word.pos == "inf":
                return "9"

            # filter +inf
            if "+inf" in word.plus_case:
                return "9"

            # filter inf kāma
            if word.pos == "adj" and not word.root_key and word.construction.endswith("kāma"):
                return "9"

            # filter dat of purpose
            if "dat " in word.grammar and "āya" in word.pali_1:
                return "9"

            # filter until-then
            if re.match(r"^y.{1,6} t.{1,6}$", word.grammar):
                return "9"

            # filter interr
            if (
                ("interr" in word.grammar) and 
                (word.pos == "ind" or word.pos == "pron")
            ):
                return "9"

            # filter prp
            if (
                word.pos == "prp" and 
                "caus" not in word.verb and 
                "caus" not in word.grammar and 
                "pass " not in word.grammar
            ):
                return "10"

            # filter pron
            if word.pos == "pron" and "interr" not in word.grammar:
                return "10"

            # loc & gen abs
            if "loc abs" in word.grammar or "gen abs" in word.grammar:
                return "10"

            # filter pp
            if word.pos == "pp":
                return "11"

            # filter adj
            if word.pos == "adj" and word.pattern != "ant adj" and word.pattern != "ī adj":
                return "11"

            # filter abl of separation
            if "abl" in word.grammar and word.pali_1.endswith("o"):
                return "11"

            # filter numbers
            if word.pos == "card" or word.pos == "ordin":
                return "12"

            # filter adv
            if word.pos == "ind" and ", adv" in word.grammar:
                return "13"

        # caus or pass > 13
        
        # filter pass
        if (
            word.verb == "pass" and 
            ", caus" not in word.grammar and 
            ", pass" in word.grammar and 
            word.verb != "caus"
        ):
            return "13"
        
        # filter caus
        if (
            word.verb == "caus" and 
            ", pass" not in word.grammar and 
            ", caus" in word.grammar and 
            word.verb != "pass"
        ):
            return "14"

        # filter caus pass
        if (
            word.verb == "caus" and 
            "pass" in word.grammar and 
            word.verb == "pass" and 
            "caus" in word.grammar
        ):
            return "14"

        if word.verb == "caus, pass":
            return "14"

        # filter ptp
        if word.pos == "ptp":
            return "14"

    else:
        return ""

    return word.sbs.sbs_class


if __name__ == "__main__":
    main()
