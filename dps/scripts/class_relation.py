# Make sbs_class according to class topics

import re

from db.models import PaliWord, SBS
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session
from rich.console import Console
from tools.tic_toc import tic, toc
from typing import Optional

console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]changing sbs_class accordingly")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    count = 0

    # Iterate over all PaliWord instances and update their sbs_class
    for word in db_session.query(PaliWord).all():


            # debug check all sbs_class_anki which has not sbs.sbs_class
            # if (
            #     word.sbs and 
            #     word.sbs.sbs_class_anki and 
            #     not word.sbs.sbs_class and
            #     word.sbs.sbs_class_anki == 14
            # ):
            #     count += 1
            #     print(f"{count} for {word.pali_1} || {word.sbs.sbs_class_anki} || {word.grammar} || 'stem': {word.stem}")


            sbs_class: Optional[int]
            sbs_class = determine_sbs_class(word)
            if sbs_class is not None:


                # debug check inconsistency with existing sbs.sbs_class
                # if (
                #     word.sbs and 
                #     # word.sbs.sbs_class and 
                #     # word.sbs.sbs_class != sbs_class and
                #     word.sbs.sbs_class_anki and
                #     sbs_class == 15
                # ):
                #     count += 1
                #     print(f"{count} for {word.pali_1} || old sbs_class: {word.sbs.sbs_class} || new is {sbs_class}")

            
                if word.sbs and not word.sbs.sbs_class:
                    word.sbs.sbs_class = int(sbs_class)

                if word.sbs:
                    word.sbs.sbs_class = int(sbs_class)
                    # print(f"for {word.pali_1} new sbs_class: {sbs_class}")
                if not word.sbs:
                    word.sbs = SBS(id=word.id)
                    word.sbs.sbs_class = int(sbs_class)
                    # print(f"for {word.pali_1} new sbs_class: {sbs_class}")

            else:
                if word.sbs and word.sbs.sbs_class:
                    word.sbs.sbs_class = ""

    # db_session.commit()

    db_session.close()
    toc()

def determine_sbs_class(word) -> Optional[int]:

    # BPC:

    # filter inf kāma
    if (
        word.pos == "adj" and 
        word.construction.endswith("kāma")
    ):
        # print(f"Pattern: inf kāma, Word: {word.pali_1}")
        return 9

    # filter ū masc + ū adj
    if (
        (word.pattern == "ū adj" or
        word.pattern == "ū masc") and
        "app " not in word.grammar 
    ):
        # print(f"Pattern: ū masc & adj, Word: {word.pali_1}")
        return 6

    # filter dat of purpose
    if (
        "dat " in word.grammar and 
        "āya" in word.pali_1
    ):
        # print(f"Pattern: dat of purpose, Word: {word.pali_1}")
        return 9

    # loc & gen abs
    if (
        "loc abs" in word.grammar or 
        "gen abs" in word.grammar
    ):
        # print(f"Pattern: loc & gen abs, Word: {word.pali_1}")
        return 10

    # filter numbers
    if (
        (word.pos == "card" or word.pos == "ordin") and
        "!" not in word.stem
    ):
        # print(f"Pattern: numbers, Word: {word.pali_1}")
        return 12

    # filter imp < 5
    if (
        word.pos == "imp" and
        not word.neg == "neg" and
        "reflx" not in word.grammar and
        "irreg" not in word.grammar and
        word.verb != "caus" and
        word.verb != "pass"
    ):
        # print(f"Pattern: imp, Word: {word.pali_1}")
        return 4

    # filter fut
    if (
        word.pos == "fut" and
        "reflx" not in word.grammar and
        "irreg" not in word.grammar and
        "irreg" not in word.root_base and
        word.verb != "caus" and
        word.verb != "pass"
    ):
        # print(f"Pattern: fut, Word: {word.pali_1}")
        return 5

    # filter opt
    if (
        word.pos == "opt" and
        "reflx" not in word.grammar and
        "irreg" not in word.grammar and
        word.verb != "caus" and
        word.verb != "pass"
    ):
        # print(f"Pattern: opt, Word: {word.pali_1}")
        return 7

    # filter opt be
    if (
            (word.pattern == "siyā opt" or 
            word.pattern == "ssa opt") and
        ", comp" not in word.grammar
        
    ):
        # print(f"Pattern: be opt, Word: {word.pali_1}")
        return 7

    # filter, compar
    if (
        "adj, compar" in word.grammar
    ):
        # print(f"Pattern: adj, compar, Word: {word.pali_1}")
        return 11

    if (
        "adv, compar" in word.grammar
    ):
        # print(f"Pattern: adj, compar, Word: {word.pali_1}")
        return 13

    # filter particles

    neg_part = ["mā", "na", "no", "neva"]
    with_part = ["saddhiṃ", "saha"]
    conj_part = ["ca", "vā"]

    if (
        word.neg == "neg" and
        word.pali_2 in neg_part and
        "interr" not in word.grammar and
        (word.pos == "ind" or word.pos == "sandhi")
    ):
        # print(f"Pattern: neg_part, Word: {word.pali_1}")
        return 5

    if (
        word.pali_2 in with_part and
        word.pos == "ind" and
        "prep" in word.grammar
    ):
        # print(f"Pattern: with_part, Word: {word.pali_1}")
        return 5

    if (
        word.pali_2 in conj_part and
        word.pos == "ind" and
        "emph" not in word.grammar
    ):
        # print(f"Pattern: conj_part, Word: {word.pali_1}")
        return 6


    # rest of BPC:

    if (
    ", comp" not in word.grammar and
    word.pos != "sandhi" and
    "reflx" not in word.grammar and
    "desid" not in word.grammar and
    "irreg" not in word.grammar and
    "!" not in word.stem
    ):
        # not caus or pass < 13
        if (
            word.verb != "caus" and
            ", pass" not in word.grammar and
            word.verb != "pass" and
            ", caus" not in word.grammar and
            word.verb != "caus, pass"
        ):
        
            if "dat " not in word.grammar:
                # filter masc > 5
                if (
                    word.pattern == "ī adj" and
                    "app " not in word.grammar 
                ):
                    # print(f"Pattern: ī adj, Word: {word.pali_1}")
                    return 5
                if word.pattern == "ī masc":
                    # print(f"Pattern: ī masc, Word: {word.pali_1}")
                    return 5
                if word.pattern == "u masc":
                    # print(f"Pattern: u masc, Word: {word.pali_1}")
                    return 6
                if word.pattern == "ar masc":
                    # print(f"Pattern: ar masc, Word: {word.pali_1}")
                    return 6
                if word.pattern == "ar2 masc":
                    # print(f"Pattern: ar2 masc, Word: {word.pali_1}")
                    return 6
                
                # filter not neg < 5
                if not word.neg == "neg":

                    # filter masc < 5
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        (word.pattern == "a masc" or word.pattern == "a masc east")
                    ):
                        # print(f"Pattern: a masc, Word: {word.pali_1}")
                        return 2
                    if word.pattern == "i masc":
                        # print(f"Pattern: i masc, Word: {word.pali_1}")
                        return 4

                    # filter pr < 5
                    if "hoti" in word.pattern:
                        # print(f"Pattern: hoti, Word: {word.pali_1}")
                        return 4
                    elif "atthi" in word.pattern:
                        # print(f"Pattern: atthi, Word: {word.pali_1}")
                        return 4
                    else:
                        #! think how to divide pr, imp for classes 3 and 4 based on root sign (1 8 4 5 6 - 3 class ; 2 3 7 - 4 class)
                        if (
                            word.pos == "pr" and 
                            "brūti" not in word.pattern and 
                            "dakkhati" not in word.pattern and 
                            "hanati" not in word.pattern and 
                            "kubbati" not in word.pattern
                        ):
                            # print(f"Pattern: pr, Word: {word.pali_1}")
                            return 3

                    # filter aor < 5
                    if (
                        word.pos == "aor" and 
                        "avoca" not in word.pattern and 
                        "assosi" not in word.pattern and 
                        "ddasa" not in word.pattern
                    ):
                        # print(f"Pattern: aor, Word: {word.pali_1}")
                        return 4

                # filter neg > 5
                if word.neg == "neg":
                    if word.pos == "aor":
                        # print(f"Pattern: aor neg, Word: {word.pali_1}")
                        return 5
                    if word.pos == "pr":
                        # print(f"Pattern: pr neg, Word: {word.pali_1}")
                        return 5
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        word.pattern == "a masc"
                    ):
                        # print(f"Pattern: masc neg, Word: {word.pali_1}")
                        return 5

                # filter fem
                if word.pattern == "ā fem":
                    # print(f"Pattern: ā fem, Word: {word.pali_1}")
                    return 7
                if word.pattern == "ī fem":
                    # print(f"Pattern: ī fem, Word: {word.pali_1}")
                    return 8
                if word.pattern == "i fem":
                    # print(f"Pattern: i fem, Word: {word.pali_1}")
                    return 8
                if word.pattern == "u fem":
                    # print(f"Pattern: u fem, Word: {word.pali_1}")
                    return 8
                if word.pattern.endswith("ar fem"):
                    # print(f"Pattern: ar fem, Word: {word.pali_1}")
                    return 8
                if word.pattern == "ū fem":
                    # print(f"Pattern: ū fem, Word: {word.pali_1}")
                    return 8 

            # filter pers pron
            if word.pattern == "ahaṃ pron":
                # print(f"Pattern: ahaṃ pron, Word: {word.pali_1}")
                return 5
            if word.pattern == "tvaṃ pron":
                # print(f"Pattern: tvaṃ pron, Word: {word.pali_1}")
                return 5

            # filter substantives (ant)
            if word.pattern == "ant adj":
                # print(f"Pattern: ant adj, Word: {word.pali_1}")
                return 6
            if word.pattern == "ant masc":
                # print(f"Pattern: ant masc, Word: {word.pali_1}")
                return 6

            # filter ger and abs
            if word.pos == "ger":
                # print(f"Pattern: ger, Word: {word.pali_1}")
                return 8
            if word.pos == "abs":
                # print(f"Pattern: abs, Word: {word.pali_1}")
                return 8

            if (
                "irreg" not in word.pattern and 
                "kamma" not in word.pattern and 
                "ptp " not in word.grammar and
                "pp " not in word.grammar and
                
                word.pos == "nt"
            ):
                # print(f"Pattern: nt, Word: {word.pali_1}")
                return 9

            # filter inf
            if word.pos == "inf":
                # print(f"Pattern: inf, Word: {word.pali_1}")
                return 9

            # filter +inf
            if (
                "+inf" in word.plus_case and
                word.pos != "adj" and
                word.pos != "pp" and
                word.pos != "ptp" and
                word.pos != "prp"
            ):
                # print(f"Pattern: +inf, Word: {word.pali_1}")
                return 9

            # filter until-then
            if re.match(r"^y.{1,6} t.{1,6}$", word.pali_1):
                # print(f"Pattern: until-then, Word: {word.pali_1}")
                return 9

            # filter prp
            if (
                word.pos == "prp"
            ):
                # print(f"Pattern: prp, Word: {word.pali_1}")
                return 10

            # filter pron
            if (
                word.pos == "pron" and 
                "interr" not in word.grammar and
                word.pattern != "ahaṃ pron" and
                word.pattern != "tvaṃ pron"
            ):
                # print(f"Pattern: pron rest, Word: {word.pali_1}")
                return 10

            # filter pp
            if word.pos == "pp":
                # print(f"Pattern: pp, Word: {word.pali_1}")
                return 11

            if (
                "pp " in word.grammar and
                word.pattern == "a masc"
            ):
                # print(f"Pattern: masc a from pp, Word: {word.pali_1}")
                return 11

            if (
                "pp " in word.grammar and
                word.pos == "nt"
            ):
                # print(f"Pattern: nt from pp, Word: {word.pali_1}")
                return 11

            # filter adj
            if (
                word.pos == "adj" and 
                word.pattern != "ant adj" and 
                word.pattern != "ī adj" and
                word.pattern != "ū adj" and
                "app " not in word.grammar and
                not word.construction.endswith("kāma")
            ):
                # print(f"Pattern: adj, Word: {word.pali_1}")
                return 11

            # adv
            adv_of_time = ["pubbe", "āyatiṃ", "dāni", "yadā", "pacchā", "ajja", "tadā", "sadā", "sāyaṃ", "kadā", "idāni", "pāto", "ekadā", "suve", "purā", "atippago", "aciraṃ", "ciraṃ", "atisāyaṃ", "kālena", "pure"]

            adv_of_place = ["tattha", "tatra", "ettha", "yattha", "yatra", "kattha", "sabbattha", "ekattha", "aññattha", "kuto", "tato", "yato", "ekato", "parito", "purato", "samantato", "kuhiṃ", "tahiṃ", "yahiṃ", "ittha", "idha", "katthaci", "pure"]

            adv_until_then = ["yāva", "tāva", "yena", "tena"]

            # adv of time
            if (
                word.pali_2 in adv_of_time and
                word.pos == "ind" and 
                ", adv" in word.grammar
            ):
                # print(f"Pattern: adv of time, Word: {word.pali_1}")
                return 6

            # adv of place
            elif (
                word.pali_2 in adv_of_place and
                word.pos == "ind" and 
                (", adv" in word.grammar or "prep" in word.grammar)
            ):
                # print(f"Pattern: adv of time, Word: {word.pali_1}")
                return 8

            # filter interr
            elif (
                "interr" in word.grammar and 
                "ptp " not in word.grammar and 
                (word.pos == "ind" or word.pos == "pron")
            ):
                # print(f"Pattern: interr, Word: {word.pali_1}")
                return 9

            elif (
                "interr" in word.grammar 
            ):
                # print(f"Pattern: interr, Word: {word.pali_1}")
                return 9

            # filter until-then
            elif (
                word.pali_2 in adv_until_then and
                word.pos == "ind" and 
                ", adv" in word.grammar
            ):
                # print(f"Pattern: until-then, Word: {word.pali_1}")
                return 9

            # filter abl of separation
            elif (
                "abl" in word.grammar and 
                word.pos == "ind" and
                word.pali_2.endswith("to") and
                word.derived_from != "ya" and
                word.derived_from != "ta" and
                word.derived_from != "ka" and
                word.derived_from != "ima"  and
                word.derived_from != "sabba" and
                word.derived_from != "para"
            ):
                # print(f"Pattern: abl of separation, Word: {word.pali_1}")
                return 11

            # filter other adv
            elif (
                word.pos == "ind" and 
                (", adv" in word.grammar or "excl" in word.grammar or "emph" in word.grammar)
            ):
                # print(f"Pattern: adv, Word: {word.pali_1}")
                return 13

            # filter other ind
            elif (
                word.pos == "ind"
            ):
                # print(f"Pattern: ind, Word: {word.pali_1}")
                return 13

        # caus or pass > 13
        
        # filter pass
        if (
            word.verb == "pass" and 
            ", caus" not in word.grammar and
            word.pos != "ptp" and
            "ptp " not in word.grammar
        ):
            # print(f"Pattern: pass, Word: {word.pali_1}")
            return 13

        if (
            ", pass" in word.grammar and 
            word.verb != "caus" and
            word.pos != "ptp" and
            "ptp " not in word.grammar
        ):
            # print(f"Pattern: pass, Word: {word.pali_1}")
            return 13

        # filter caus
        if (
            (word.verb == "caus" and 
            ", pass" not in word.grammar) or 
            (", caus" in word.grammar and 
            word.verb != "pass")
        ):
            # print(f"Pattern: caus, Word: {word.pali_1}")
            return 14

        # filter caus pass
        if (
            word.verb == "caus" and 
            ", pass" in word.grammar 
        ):
            # print(f"Pattern: caus pass, Word: {word.pali_1}")
            return 14

        # filter caus pass
        if (
            word.verb == "pass" and 
            ", caus" in word.grammar 
        ):
            # print(f"Pattern: caus pass, Word: {word.pali_1}")
            return 14

        if word.verb == "caus, pass":
            # print(f"Pattern: caus, pass, Word: {word.pali_1}")
            return 14

        # filter ptp
        if (
            word.pos == "ptp" or
            "ptp " in word.grammar
        ):
            # print(f"Pattern: ptp, Word: {word.pali_1}")
            return 14

    # Return None if none of the conditions are met
    return None


if __name__ == "__main__":
    main()
