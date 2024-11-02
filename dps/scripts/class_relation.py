# Make sbs_class according to class topics
# Use debug print before commit!

import re

from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from rich.console import Console
from tools.tic_toc import tic, toc
from typing import Optional

from sqlalchemy.orm import joinedload
from sqlalchemy import or_

console = Console()


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).filter(
        or_(
            SBS.sbs_class_anki != "",
            SBS.sbs_patimokkha != "",
            SBS.sbs_index != "",
            SBS.sbs_category != "",
        )
    ).all()


def debug_print_sbs_class():
    tic()
    console.print("[bold bright_yellow]changing sbs_class accordingly")

    console.print(f"[green]filtered db {len(db)}")

    count = 0

    # Iterate over all DpdHeadword instances and update their sbs_class
    for word in db:


            # debug check all sbs_class_anki which has not sbs.sbs_class
            # if (
            #     word.sbs 
            #     and word.sbs.sbs_class_anki 
            #     and not word.sbs.sbs_class
            #     # and word.sbs.sbs_class_anki == 14
            # ):
            #     count += 1
            #     print(f"{count} for {word.lemma_1} || {word.sbs.sbs_class_anki} || {word.grammar} || 'stem': {word.stem}")


            sbs_class: Optional[int]
            sbs_class = determine_sbs_class(word)
            if sbs_class is not None:

                # debug check if have a new number but it is not the same as old
                if (
                    word.sbs
                    and word.sbs.sbs_class_anki 
                    and word.sbs.sbs_class
                    and word.sbs.sbs_class != sbs_class
                ):
                    count += 1
                    print(f"(changed) {count} for {word.lemma_1} || old sbs_class: {word.sbs.sbs_class} || new is {sbs_class}")

                # debug for new words
                # if (
                #     not word.sbs
                # ):
                #     count += 1
                #     print(f"(added) {count} for {word.lemma_1} || old sbs_class: None || new is {sbs_class}")

            
                if word.sbs and not word.sbs.sbs_class:
                    word.sbs.sbs_class = int(sbs_class)
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

                if word.sbs:
                    word.sbs.sbs_class = int(sbs_class)
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

                if not word.sbs:
                    word.sbs = SBS(id=word.id)
                    word.sbs.sbs_class = int(sbs_class)
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

            else:
                if word.sbs and word.sbs.sbs_class:
                    word.sbs.sbs_class = ""
                    # print(f"(del) for {word.lemma_1} new sbs_class: {sbs_class}")

                    # debug check if does not have a new number but have old
                    if (
                        word.sbs.sbs_class_anki
                    ):
                        count += 1
                        print(f"(removed) {count} for {word.lemma_1} || old sbs_class: {word.sbs.sbs_class} || new is {sbs_class}")

    # db_session.commit()

    db_session.close()
    toc()


def filling_sbs_class():
    tic()
    console.print("[bold bright_yellow]changing sbs_class accordingly")

    console.print(f"[green]filtered db {len(db)}")

    count_same = 0
    count_added = 0
    count_changed = 0
    count_new = 0
    count_delete = 0
    count_empty = 0

    # Iterate over all DpdHeadword instances and update their sbs_class
    for word in db:

            sbs_class: Optional[int]
            sbs_class = determine_sbs_class(word)
            if sbs_class is not None:

                if word.sbs.sbs_class == int(sbs_class):
                    count_same += 1

                elif word.sbs and not word.sbs.sbs_class:
                    word.sbs.sbs_class = int(sbs_class)
                    count_added += 1
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

                elif word.sbs:
                    word.sbs.sbs_class = int(sbs_class)
                    count_changed += 1
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

                elif not word.sbs:
                    word.sbs = SBS(id=word.id)
                    word.sbs.sbs_class = int(sbs_class)
                    count_new += 1
                    # print(f"(added) for {word.lemma_1} new sbs_class: {sbs_class}")

            else:
                if word.sbs and word.sbs.sbs_class:
                    word.sbs.sbs_class = ""
                    count_delete += 1
                    # print(f"(del) for {word.lemma_1} new sbs_class: {sbs_class}")

                elif not word.sbs.sbs_class:
                    count_empty += 1


    console.print(f"[green]{count_same} rows same")
    console.print(f"[green]{count_added} rows added")
    console.print(f"[green]{count_changed} rows changed")
    console.print(f"[green]{count_new} rows new")
    console.print(f"[green]{count_delete} rows removed")
    console.print(f"[green]{count_empty} rows have no sbs_class")


    db_session.commit()

    db_session.close()
    toc()


def determine_sbs_class(word) -> Optional[int]:

    #! BPC:

    # filter inf kāma
    if (
        word.pos == "adj" and 
        word.construction.endswith("kāma")
    ):
        # print(f"Pattern: inf kāma, Word: {word.lemma_1}")
        return 9

    # filter ū masc + ū adj
    if (
        (word.pattern == "ū adj" or
        word.pattern == "ū masc") and
        "app " not in word.grammar 
    ):
        # print(f"Pattern: ū masc & adj, Word: {word.lemma_1}")
        return 6

    # filter dat of purpose
    if (
        "dat " in word.grammar and 
        "āya" in word.lemma_1 and
        word.pos != "ind"
    ):
        # print(f"Pattern: dat of purpose, Word: {word.lemma_1}")
        return 9

    # loc & gen abs
    if (
        "loc abs" in word.grammar or 
        "gen abs" in word.grammar
    ):
        # print(f"Pattern: loc & gen abs, Word: {word.lemma_1}")
        return 10

    # filter numbers
    if (
        (word.pos == "card" or word.pos == "ordin") and
        "!" not in word.stem
    ):
        # print(f"Pattern: numbers, Word: {word.lemma_1}")
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
        # print(f"Pattern: imp, Word: {word.lemma_1}")
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
        # print(f"Pattern: fut, Word: {word.lemma_1}")
        return 5

    # filter opt
    if (
        word.pos == "opt" and
        "reflx" not in word.grammar and
        "irreg" not in word.grammar and
        word.verb != "caus" and
        word.verb != "pass"
    ):
        # print(f"Pattern: opt, Word: {word.lemma_1}")
        return 7

    # filter opt be
    if (
            (word.pattern == "siyā opt" or 
            word.pattern == "ssa opt") and
        ", comp" not in word.grammar
        
    ):
        # print(f"Pattern: be opt, Word: {word.lemma_1}")
        return 7

    # filter, compar
    if (
        "adj, compar" in word.grammar
    ):
        # print(f"Pattern: adj, compar, Word: {word.lemma_1}")
        return 11

    if (
        "adv, compar" in word.grammar
    ):
        # print(f"Pattern: adj, compar, Word: {word.lemma_1}")
        return 13

    # filter particles

    neg_part = ["mā", "na", "no", "neva"]
    with_part = ["saddhiṃ", "saha"]
    conj_part = ["ca", "vā"]

    if (
        word.neg == "neg" and
        word.lemma_2 in neg_part and
        "interr" not in word.grammar and
        (word.pos == "ind" or word.pos == "sandhi")
    ):
        # print(f"Pattern: neg_part, Word: {word.lemma_1}")
        return 5

    if (
        word.lemma_2 in with_part and
        word.pos == "ind" and
        "prep" in word.grammar
    ):
        # print(f"Pattern: with_part, Word: {word.lemma_1}")
        return 5

    if (
        word.lemma_2 in conj_part and
        word.pos == "ind" and
        "emph" not in word.grammar
    ):
        # print(f"Pattern: conj_part, Word: {word.lemma_1}")
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
                    # print(f"Pattern: ī adj, Word: {word.lemma_1}")
                    return 5
                if word.pattern == "ī masc":
                    # print(f"Pattern: ī masc, Word: {word.lemma_1}")
                    return 5
                if word.pattern == "u masc":
                    # print(f"Pattern: u masc, Word: {word.lemma_1}")
                    return 6
                if word.pattern == "ar masc":
                    # print(f"Pattern: ar masc, Word: {word.lemma_1}")
                    return 6
                if word.pattern == "ar2 masc":
                    # print(f"Pattern: ar2 masc, Word: {word.lemma_1}")
                    return 6
                
                # filter not neg < 5
                if not word.neg == "neg":

                    # filter masc < 5
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        (word.pattern == "a masc" or word.pattern == "a masc east")
                    ):
                        # print(f"Pattern: a masc, Word: {word.lemma_1}")
                        return 2
                    if word.pattern == "i masc":
                        # print(f"Pattern: i masc, Word: {word.lemma_1}")
                        return 4

                    # filter pr < 5
                    if "hoti" in word.pattern:
                        # print(f"Pattern: hoti, Word: {word.lemma_1}")
                        return 4
                    elif "atthi" in word.pattern:
                        # print(f"Pattern: atthi, Word: {word.lemma_1}")
                        return 4
                    else:
                        #! TODO think how to divide pr, imp for classes 3 and 4 based on root sign (1 8 4 5 6 - 3 class ; 2 3 7 - 4 class)
                        if (
                            word.pos == "pr" and 
                            "brūti" not in word.pattern and 
                            "dakkhati" not in word.pattern and 
                            "hanati" not in word.pattern and 
                            "kubbati" not in word.pattern
                        ):
                            # print(f"Pattern: pr, Word: {word.lemma_1}")
                            return 3

                    # filter aor < 5
                    if (
                        word.pos == "aor" and 
                        "avoca" not in word.pattern and 
                        "assosi" not in word.pattern and 
                        "ddasa" not in word.pattern
                    ):
                        # print(f"Pattern: aor, Word: {word.lemma_1}")
                        return 4

                # filter neg > 5
                if word.neg == "neg":
                    if word.pos == "aor":
                        # print(f"Pattern: aor neg, Word: {word.lemma_1}")
                        return 5
                    if word.pos == "pr":
                        # print(f"Pattern: pr neg, Word: {word.lemma_1}")
                        return 5
                    if (
                        "ptp " not in word.grammar and
                        "pp " not in word.grammar and
                        word.pattern == "a masc"
                    ):
                        # print(f"Pattern: masc neg, Word: {word.lemma_1}")
                        return 5

                # filter fem
                if word.pattern == "ā fem":
                    # print(f"Pattern: ā fem, Word: {word.lemma_1}")
                    return 7
                if word.pattern == "ī fem":
                    # print(f"Pattern: ī fem, Word: {word.lemma_1}")
                    return 8
                if word.pattern == "i fem":
                    # print(f"Pattern: i fem, Word: {word.lemma_1}")
                    return 8
                if word.pattern == "u fem":
                    # print(f"Pattern: u fem, Word: {word.lemma_1}")
                    return 8
                if word.pattern.endswith("ar fem"):
                    # print(f"Pattern: ar fem, Word: {word.lemma_1}")
                    return 8
                if word.pattern == "ū fem":
                    # print(f"Pattern: ū fem, Word: {word.lemma_1}")
                    return 8 

            # filter pers pron
            if word.pattern == "ahaṃ pron":
                # print(f"Pattern: ahaṃ pron, Word: {word.lemma_1}")
                return 5
            if word.pattern == "tvaṃ pron":
                # print(f"Pattern: tvaṃ pron, Word: {word.lemma_1}")
                return 5

            # filter substantives (ant)
            if word.pattern == "ant adj":
                # print(f"Pattern: ant adj, Word: {word.lemma_1}")
                return 6
            if word.pattern == "ant masc":
                # print(f"Pattern: ant masc, Word: {word.lemma_1}")
                return 6

            # filter ger and abs
            if word.pos == "ger":
                # print(f"Pattern: ger, Word: {word.lemma_1}")
                return 8
            if word.pos == "abs":
                # print(f"Pattern: abs, Word: {word.lemma_1}")
                return 8

            if (
                "irreg" not in word.pattern and 
                "kamma" not in word.pattern and 
                "ptp " not in word.grammar and
                "pp " not in word.grammar and
                
                word.pos == "nt"
            ):
                # print(f"Pattern: nt, Word: {word.lemma_1}")
                return 9

            # filter inf
            if word.pos == "inf":
                # print(f"Pattern: inf, Word: {word.lemma_1}")
                return 9

            # filter +inf
            if (
                "+inf" in word.plus_case and
                word.pos != "adj" and
                word.pos != "pp" and
                word.pos != "ptp" and
                word.pos != "prp"
            ):
                # print(f"Pattern: +inf, Word: {word.lemma_1}")
                return 9

            # filter until-then
            if (
                re.match(r"^y.{1,6} t.{1,6}$", word.lemma_1) or 
                word.lemma_2 == "yo so"
            ):
                # print(f"Pattern: until-then, Word: {word.lemma_1}")
                return 9

            # filter prp
            if (
                word.pos == "prp"
            ):
                # print(f"Pattern: prp, Word: {word.lemma_1}")
                return 10

            # filter pron
            if (
                word.pos == "pron" and 
                "interr" not in word.grammar and
                word.pattern != "ahaṃ pron" and
                word.pattern != "tvaṃ pron"
            ):
                # print(f"Pattern: pron rest, Word: {word.lemma_1}")
                return 10

            if (
                word.lemma_2 == "eva"
            ):
                # print(f"Pattern: eva, Word: {word.lemma_1}")
                return 10

            # filter pp
            if word.pos == "pp":
                # print(f"Pattern: pp, Word: {word.lemma_1}")
                return 11

            if (
                "pp " in word.grammar and
                word.pattern == "a masc"
            ):
                # print(f"Pattern: masc a from pp, Word: {word.lemma_1}")
                return 11

            if (
                "pp " in word.grammar and
                word.pos == "nt"
            ):
                # print(f"Pattern: nt from pp, Word: {word.lemma_1}")
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
                # print(f"Pattern: adj, Word: {word.lemma_1}")
                return 11

            # adv
            adv_of_time = ["pubbe", "āyatiṃ", "dāni", "yadā", "pacchā", "ajja", "tadā", "sadā", "sāyaṃ", "kadā", "idāni", "pāto", "ekadā", "suve", "purā", "atippago", "aciraṃ", "ciraṃ", "atisāyaṃ", "kālena", "pure"]

            adv_of_place = ["tattha", "tatra", "ettha", "yattha", "yatra", "kattha", "sabbattha", "ekattha", "aññattha", "kuto", "tato", "yato", "ekato", "parito", "purato", "samantato", "kuhiṃ", "tahiṃ", "yahiṃ", "ittha", "idha", "katthaci", "pure", "amutra"]

            adv_until_then = ["yāva", "tāva", "yena", "tena"]

            # adv of time
            if (
                word.lemma_2 in adv_of_time and
                word.pos == "ind" and 
                ", adv" in word.grammar
            ):
                # print(f"Pattern: adv of time, Word: {word.lemma_1}")
                return 6

            # adv of place
            elif (
                word.lemma_2 in adv_of_place and
                word.pos == "ind" and 
                (", adv" in word.grammar or "prep" in word.grammar)
            ):
                # print(f"Pattern: adv of time, Word: {word.lemma_1}")
                return 8

            # filter interr
            elif (
                "interr" in word.grammar and 
                "ptp " not in word.grammar and 
                (word.pos == "ind" or word.pos == "pron")
            ):
                # print(f"Pattern: interr, Word: {word.lemma_1}")
                return 9

            elif (
                "interr" in word.grammar 
            ):
                # print(f"Pattern: interr, Word: {word.lemma_1}")
                return 9

            # filter until-then
            elif (
                word.lemma_2 in adv_until_then and
                word.pos == "ind" and 
                ", adv" in word.grammar
            ):
                # print(f"Pattern: until-then, Word: {word.lemma_1}")
                return 9

            # filter abl of separation
            elif (
                "abl" in word.grammar and 
                word.pos == "ind" and
                word.lemma_2.endswith("to") and
                word.derived_from != "ya" and
                word.derived_from != "ta" and
                word.derived_from != "ka" and
                word.derived_from != "ima"  and
                word.derived_from != "sabba" and
                word.derived_from != "para"
            ):
                # print(f"Pattern: abl of separation, Word: {word.lemma_1}")
                return 11

            # filter other adv
            elif (
                word.pos == "ind" and 
                (", adv" in word.grammar or "excl" in word.grammar or "emph" in word.grammar)
            ):
                # print(f"Pattern: adv, Word: {word.lemma_1}")
                return 13

            # filter other ind
            elif (
                word.pos == "ind"
            ):
                # print(f"Pattern: ind, Word: {word.lemma_1}")
                return 13

        # caus or pass > 13
        
        # filter pass
        if (
            word.verb == "pass" and 
            ", caus" not in word.grammar and
            word.pos != "ptp" and
            "ptp " not in word.grammar
        ):
            # print(f"Pattern: pass, Word: {word.lemma_1}")
            return 13

        if (
            ", pass" in word.grammar and 
            word.verb != "caus" and
            word.pos != "ptp" and
            "ptp " not in word.grammar
        ):
            # print(f"Pattern: pass, Word: {word.lemma_1}")
            return 13

        # filter caus
        if (
            (word.verb == "caus" and 
            ", pass" not in word.grammar) or 
            (", caus" in word.grammar and 
            word.verb != "pass")
        ):
            # print(f"Pattern: caus, Word: {word.lemma_1}")
            return 14

        # filter caus pass
        if (
            word.verb == "caus" and 
            ", pass" in word.grammar 
        ):
            # print(f"Pattern: caus pass, Word: {word.lemma_1}")
            return 14

        # filter caus pass
        if (
            word.verb == "pass" and 
            ", caus" in word.grammar 
        ):
            # print(f"Pattern: caus pass, Word: {word.lemma_1}")
            return 14

        if word.verb == "caus, pass":
            # print(f"Pattern: caus, pass, Word: {word.lemma_1}")
            return 14

        # filter ptp
        if (
            word.pos == "ptp" or
            "ptp " in word.grammar
        ):
            # print(f"Pattern: ptp, Word: {word.lemma_1}")
            return 14

    #! IPC:
    # sandhi
    if (
        word.pos == "sandhi"
        and "ṃ +" not in word.construction
        and "tad +" not in word.construction
        and "yad +" not in word.construction
        and "ṃ >" not in word.construction
    ):
        # print(f"Pattern: vowel sandhi, Word: {word.lemma_1}")
        return 16

    elif (
        word.pos == "sandhi" and
        (
            "ṃ +" in word.construction or 
            "tad +" in word.construction or
            "yad +" in word.construction or
            "ṃ >" in word.construction
        )
    ):
        # print(f"Pattern: ṃ sandhi, Word: {word.lemma_1}")
        return 17

    if (
        (
            ", comp" in word.grammar or 
            "comp vb" in word.grammar) and
        "compar" not in word.grammar and
        word.compound_type == "" and
        (
            "ṃ +" in word.construction or 
            "tad +" in word.construction or 
            "yad +" in word.construction)
    ):
        # print(f"Pattern: ṃ sandhi, Word: {word.lemma_1}")
        return 17

    if (
        (", comp" in word.grammar or "comp vb" in word.grammar) and
        "compar" not in word.grammar and
        word.compound_type == "" and
        (
            "√bhū" in word.phonetic
            or "√kar" in word.phonetic
        )
    ):
        # print(f"Pattern: √bhū and √kar a > i, Word: {word.lemma_1}")
        return 19

    vowel_sandhi_patterns = {
    "aa > a", "aa > ā", "aa > o", "aā > ā", "āa > ā", "āā > ā", "ai > a", "ai > ā", "ai > i", 
    "ai > e", "aī > e", "au > u", "au > ū", "au > o", "aū > o", "ae > e", "ao > o", "āi > ā", 
    "āi > i", "āi > ī", "āi > e", "āu > ū", "āe > ā", "ia > a", "ia > ā", "ia > i", "ia > ī", 
    "ia > ya", "iā > yā", "ii > i", "ii > ī", "iu > o", "ie > e", "io > o", "īa > yā", "īu > u", 
    "īi > ī", "ua > u", "ua > va", "ua > vā", "uā > ā", "uā > vā", "ui > u", "ui > ū", "uu > u", 
    "uu > ū", "ue > u", "ue > ve", "ūa > ū", "ea > a", "ea > ā", "ea > e", "ea > ya", "ea > yā", 
    "eā > ā", "ei > e", "ee > e", "oa > a", "oa > ā", "oa > o", "oa > va", "oa > vā", "oe > e", 
    "oe > o", "oi > o", "ou > u", "ya > yā", "va > vā", "+"
    }


    if (
        (
            ", comp" in word.grammar or 
            "comp vb" in word.grammar or 
            word.pos == "ind" or
            word.pos == "idiom" 
            ) and
        "compar" not in word.grammar and
        word.compound_type == "" and
        any(pattern in word.phonetic for pattern in vowel_sandhi_patterns)
    ):
        # print(f"Pattern: vowel sandhi comp, Word: {word.lemma_1}")
        return 16

    cons_patterns = {
        "tk > kk", "st > tth", "dv > dd", "rth > tth", "kh > kkh", "g > gg", "ch > cch", 
        "j > jj", "ñ > ññ", "ṭh > ṭṭh", "t > tt", "d > dd", "dh > ddh", "n > nn", 
        "p > pp", "b > bb", "l > ll", "s > ss", "āg > agg", "āp > app", "āb > abb", 
        "m > mm", "rv > vv > bb", "pi > py > pp", "tk > kk", "bh > bbh", "tp > pp", 
        "ṭh > ṭṭh"
    }

    if (
        (
            ", comp" in word.grammar or 
            "comp vb" in word.grammar or 
            word.pos == "ind" or
            word.pos == "idiom"
            ) and
        "compar" not in word.grammar and
        word.compound_type == "" and
        any(pattern in word.phonetic for pattern in cons_patterns)
    ):
        # print(f"Pattern: cons sandhi comp, Word: {word.lemma_1}")
        return 17


    # irreg nouns
    if (
        "comp," not in word.grammar
        and "mano group" in word.grammar
    ):
        # print(f"Pattern: mano group, Word: {word.lemma_1}")
        return 18

    if (
        word.pattern == "go masc"
    ):
        # print(f"Pattern: go masc, Word: {word.lemma_1}")
        return 18

    if (
        "comp," not in word.grammar
        and "atta group" in word.grammar
        and "brahma" not in word.pattern
    ):
        # print(f"Pattern: atta group, Word: {word.lemma_1}")
        return 18

    # comp
    if (
        word.compound_type == "kammadhāraya"
        or word.compound_type == "digu"
        or (
            "tappurisa" in word.compound_type 
            and "bahubbīhi" not in word.compound_type 
            and "abyayībhāva" not in word.compound_type
            and "missaka" not in word.compound_type
            )
        or word.compound_type == "dvanda"
    ):
        # print(f"Pattern: comp 1st part, Word: {word.lemma_1}")
        return 19

    elif (
        "abyayībhāva" in word.compound_type
        or "bahubbīhi" in word.compound_type
        or "missaka" in word.compound_type
    ):
        # print(f"Pattern: comp 2nd part, Word: {word.lemma_1}")
        return 20

    # Return None if none of the conditions are met
    return None



# debug_print_sbs_class()
filling_sbs_class()