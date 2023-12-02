"""Process Critical Pali Dictionary and add missing words to DPD."""

import csv
import re

from pathlib import Path
from rich import print
from typing import Dict, List

from db.models import PaliWord, InflectionTemplates
from db.get_db_session import get_db_session
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


cpd_path = Path("../other dictionaries/cpd/output/cpd_for_db.csv")
pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def main():
    print("[yellow]testing cpd data")

    (headwords, headwords_clean, pos, roots, root_fam,
        word_fam, infl_pattern, dpd_length) = get_db_lists()
    cpd: List[Dict[str, str]] = read_tsv_dot_dict(cpd_path)
    test_1(cpd, headwords)
    test_2(cpd, pos)
    test_3(cpd, roots)
    test_4(cpd, root_fam)
    test_5(cpd)
    test_6(cpd, word_fam)
    test_7(cpd)
    test_8(cpd, infl_pattern)
    test_9(cpd)
    test_10(cpd)
    test_11(cpd)
    test_12(cpd, headwords_clean)
    cpd = add_grammar(cpd)
    add_to_db(cpd, dpd_length)


def get_db_lists():
    dpd_db = db_session.query(PaliWord).all()
    dpd_length = len(dpd_db)
    headwords = [i.pali_1 for i in dpd_db]
    headwords_clean = [i.pali_clean for i in dpd_db]
    pos = sorted(set([i.pos for i in dpd_db]))
    roots = sorted(set([i.root_key for i in dpd_db]))
    root_fam = sorted(set([i.family_root for i in dpd_db]))
    word_fam = sorted(set([i.family_word for i in dpd_db if i.family_word]))

    inflection_temp = db_session.query(InflectionTemplates).all()
    infl_pattern = [i.pattern for i in inflection_temp]
    return headwords, headwords_clean, pos, roots, root_fam, word_fam, infl_pattern, dpd_length


def regex_results(list):
    results = "^("
    results += "|".join(list)
    results += ")$"
    return results


def test_1(cpd, headwords):
    """Test if cpd.pali_1 in db headwords."""
    test_1 = []
    for i in cpd:
        if i.stem:
            if i.pali_1 in headwords:
                test_1 += [i.pali_1]
    print(f"[green]{'test 01: pali_1 already in db':<40}", end="")
    if test_1:
        print()
        print(f"[red]{regex_results(test_1)}")
    else:
        print("OK")


def test_2(cpd, pos):
    """Test if cpd.pos is legit."""
    test_2 = []
    for i in cpd:
        if i.stem:
            if i.pos not in pos:
                test_2 += [i.pali_1]
    print(f"[green]{'test 02: pos is wonky':<40}", end="")
    if test_2:
        print()
        print(f"[red]{regex_results(test_2)}")
    else:
        print("OK")


def test_3(cpd, roots):
    """Test if cpd.roots is legit."""
    test_3 = []
    for i in cpd:
        if i.stem:
            if i.root_key not in roots:
                test_3 += [i.pali_1]
    print(f"[green]{'test 03: root_key is wonky':<40}", end="")
    if test_3:
        print()
        print(f"[red]{regex_results(test_3)}")
    else:
        print("OK")


def test_4(cpd, root_fam):
    """Test if cpd.family_root is legit."""
    test_4 = []
    for i in cpd:
        if i.stem and "√" in i.family_root:
            if i.family_root not in root_fam:
                test_4 += [i.pali_1]
    print(f"[green]{'test 04: check root_family':<40}", end="")
    if test_4:
        print()
        print(f"[red]{regex_results(test_4)}")
    else:
        print("OK")


def test_5(cpd):
    """Test if cpd.family_root has a root sign."""
    test_5 = []
    for i in cpd:
        if i.stem:
            if i.family_root and "√" not in i.family_root:
                test_5 += [i.pali_1]
    print(f"[green]{'test 05: check root sign in family root':<40}", end="")
    if test_5:
        print()
        print(f"[red]{regex_results(test_5)}")
    else:
        print("OK")


def test_6(cpd, word_fam):
    """Test if cpd.family_word is legit."""
    test_6 = []
    for i in cpd:
        if i.stem and i.family_word:
            if i.family_word not in word_fam:
                test_6 += [i.pali_1]
    print(f"[green]{'test 06: check word_family':<40}", end="")
    if test_6:
        print()
        print(f"[red]{regex_results(test_6)}")
    else:
        print("OK")


def test_7(cpd):
    """Test if stem + pattern = pali_1 clean."""
    test_7 = []
    for i in cpd:
        if i.stem and i.stem != "-":
            pali_clean = re.sub(r" \d.*$", "", i.pali_1)
            pattern_clean = re.sub(" .*$", "", i.pattern)
            stem_pattern = f"{i.stem}{pattern_clean}"
            if pali_clean != stem_pattern:
                test_7 += [i.pali_1]
    print(f"[green]{'test 07: stem pattern equals pali_1':<40}", end="")
    if test_7:
        print()
        print(f"[red]{regex_results(test_7)}")
    else:
        print("OK")


def test_8(cpd, infl_pattern):
    """Test if pattern is legit."""
    test_8 = []
    for i in cpd:
        if i.stem and i.stem != "-":
            if i.pattern not in infl_pattern:
                test_8 += [i.pali_1]
    print(f"[green]{'test 08: pattern is wonky':<40}", end="")
    if test_8:
        print()
        print(f"[red]{regex_results(test_8)}")
    else:
        print("OK")


def test_9(cpd):
    """Test for dupplciate headwords."""
    test_9 = []
    headwords = []
    for i in cpd:
        if i.stem:
            if i.pali_1 in headwords:
                test_9 += [i.pali_1]
            headwords += [i.pali_1]
    print(f"[green]{'test 09: duplicate headwords':<40}", end="")
    if test_9:
        print()
        print(f"[red]{regex_results(test_9)}")
    else:
        print("OK")


def test_10(cpd):
    """Test pos == pattern."""
    test_10 = []
    indecl = ["abs", "ger", "inf", "ind", "prefix"]
    for i in cpd:
        if i.stem and i.pos not in indecl:
            pattern_pos = re.sub("^.* ", "", i.pattern)
            if i.pos != pattern_pos:
                test_10 += [i.pali_1]
    print(f"[green]{'test 10: pos does not match pattern':<40}", end="")
    if test_10:
        print()
        print(f"[red]{regex_results(test_10)}")
    else:
        print("OK")


def test_11(cpd):
    """Missing stem."""
    test_11 = []
    cpd = iter(cpd)
    for i in cpd:
        if not i.stem:
            if next(cpd).stem:
                test_11 += [i.pali_1]
    print(f"[green]{'test 11: missing stem':<40}", end="")
    if test_11:
        print()
        print(f"[red]{regex_results(test_11)}")
    else:
        print("OK")


def test_12(cpd, headwords_clean):
    """Headwords not in dpd."""
    headwords_clean = set(headwords_clean)
    test_12 = []
    for i in cpd:
        pali_clean = re.sub(r" /d.*$", "", i.pali_1)
        if pali_clean not in headwords_clean:
            test_12 += [i.pali_1]
    print(f"[green]{'test 12: headwords not in dpd':<40}", end="")
    print(f"{len(test_12):,}")



def add_grammar(cpd):
    """Add pos and comp to grammar."""
    for i in cpd:
        if i.stem:
            if i.grammar:
                grammar = f"{i.pos}, {i.grammar}"
            else:
                grammar = f"{i.pos}"
            if not i.family_root and not i.family_word:
                grammar += ", comp"
            i.grammar = grammar
    return cpd


def add_to_db(cpd, dpd_length):
    print(
        f"[cyan]{'have you spellchecked? (YES/NO)':<40}", end="")
    yes_no = input("")
    if yes_no != "YES":
        return
    print(
        f"[cyan]{'add words to db? (YES/NO)':<40}",
        end="")
    yes_no = input("")
    if yes_no == "YES":

        add_to_db = []

        for counter, i in enumerate(cpd):
            i.pali_1.replace("ṁ", "ṃ")
            i.stem.replace("ṁ", "ṃ")
            if "; lit" in i.meaning_2:
                meaning_lit = re.sub(r"(.+; lit\. )(.+)", r"\2", i.meaning_2)
            else:
                meaning_lit = ""

            if i.stem:
                cpd_data = PaliWord(
                    pali_1=i.pali_1,
                    pali_2=i.pali_1,
                    pos=i.pos,
                    grammar=i.grammar,
                    neg=i.neg,
                    verb=i.verb,
                    trans=i.trans,
                    plus_case=i.plus_case,
                    meaning_2=i.meaning_2,
                    meaning_lit=meaning_lit,
                    sanskrit=i.sanskrit,
                    root_key=i.root_key,
                    family_root=i.family_root,
                    family_word=i.family_word,
                    construction=i.construction,
                    antonym=i.antonym,
                    origin="cpd",
                    stem=i.stem,
                    pattern=i.pattern,
                )
                add_to_db.append(cpd_data)

        db_session.add_all(add_to_db)
        db_session.commit()
        db_session.close()
        print(f"[green]{'words added to db':<40}{len(add_to_db)}")

        write_csv(cpd, cpd_path)

    else:
        print("nothing added to db")


def write_csv(cpd, cpd_path):
    with open(cpd_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cpd[0].keys(), delimiter='\t')
        writer.writeheader()
        for i in cpd:
            if not i.stem:
                writer.writerow(i)


if __name__ == "__main__":
    main()
