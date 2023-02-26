
import re

from rich import print

from db.models import PaliWord, FamilyRoot
from tools.superscripter import superscripter_uni


def generate_root_matrix(db_session):
    print("[green]generating root matrix")
    root_matrix = {}
    total_counter = 0
    counter = 0

    dpd_db = db_session.query(PaliWord).all()

    for enum, i in enumerate(dpd_db):

        headword = i.pali_1
        # root_clean = re.sub(" \\d.*$", "", i.root_key)

        if enum % 10000 == 0:
            print(f"{enum:>9,} / {len(dpd_db):<9,} {headword}")

        if i.root_key != "":
            if i.root_key not in root_matrix:
                root_matrix[i.root_key] = {
                    'verbs': {
                        'pr': [],
                        'pr caus': [],
                        'pr caus & pass': [],
                        'pr pass': [],
                        'pr desid': [],
                        'pr desid & caus': [],
                        'pr intens': [],
                        'pr intens & caus': [],
                        'pr deno': [],
                        'pr deno & caus': [],
                        'pr ✗': [],

                        'imp': [],
                        'imp caus': [],
                        'imp caus & pass': [],
                        'imp pass': [],
                        'imp desid': [],
                        'imp desid & caus': [],
                        'imp intens': [],
                        'imp deno': [],
                        'imp deno & caus': [],
                        'imp ✗': [],

                        'opt': [],
                        'opt caus': [],
                        'opt caus & pass': [],
                        'opt pass': [],
                        'opt desid': [],
                        'opt desid & caus': [],
                        'opt intens': [],
                        'opt deno': [],
                        'opt deno & caus': [],
                        'opt ✗': [],

                        'perf': [],
                        'perf caus': [],
                        'perf caus & pass': [],
                        'perf pass': [],
                        'perf desid': [],
                        'perf desid & caus': [],
                        'perf intens': [],
                        'perf deno': [],
                        'perf deno & caus': [],
                        'perf ✗': [],

                        'imperf': [],
                        'imperf caus': [],
                        'imperf caus & pass': [],
                        'imperf pass': [],
                        'imperf desid': [],
                        'imperf desid & caus': [],
                        'imperf intens': [],
                        'imperf deno': [],
                        'imperf deno & caus': [],
                        'imperf ✗': [],

                        'aor': [],
                        'aor caus': [],
                        'aor caus & pass': [],
                        'aor pass': [],
                        'aor desid': [],
                        'aor desid & caus': [],
                        'aor intens': [],
                        'aor deno': [],
                        'aor deno & caus': [],
                        'aor ✗': [],

                        'fut': [],
                        'fut caus': [],
                        'fut caus & pass': [],
                        'fut pass': [],
                        'fut desid': [],
                        'fut desid & caus': [],
                        'fut intens': [],
                        'fut deno': [],
                        'fut deno & caus': [],
                        'fut ✗': [],

                        'cond': [],
                        'cond caus': [],
                        'cond caus & pass': [],
                        'cond pass': [],
                        'cond desid': [],
                        'cond desid & caus': [],
                        'cond intens': [],
                        'cond deno': [],
                        'cond deno & caus': [],
                        'cond ✗': [],

                        'abs': [],
                        'abs caus': [],
                        'abs caus & pass': [],
                        'abs pass': [],
                        'abs desid': [],
                        'abs desid & caus': [],
                        'abs intens': [],
                        'abs deno': [],
                        'abs deno & caus': [],
                        'abs ✗': [],

                        'ger': [],
                        'ger caus': [],
                        'ger caus & pass': [],
                        'ger pass': [],
                        'ger desid': [],
                        'ger desid & caus': [],
                        'ger intens': [],
                        'ger deno': [],
                        'ger deno & caus': [],
                        'ger ✗': [],

                        'inf': [],
                        'inf caus': [],
                        'inf caus & pass': [],
                        'inf pass': [],
                        'inf desid': [],
                        'inf desid & caus': [],
                        'inf intens': [],
                        'inf deno': [],
                        'inf deno & caus': [],
                        'inf ✗': [],
                    },

                    'participles': {
                        'prp': [],
                        'prp caus': [],
                        'prp caus & pass': [],
                        'prp pass': [],
                        'prp desid': [],
                        'prp desid & caus': [],
                        'prp desid & pass': [],
                        'prp intens': [],
                        'prp deno': [],
                        'prp deno & caus': [],
                        'prp ✗': [],

                        'pp': [],
                        'pp caus': [],
                        'pp caus & pass': [],
                        'pp pass': [],
                        'pp desid': [],
                        'pp desid & caus': [],
                        'pp intens': [],
                        'pp deno': [],
                        'pp deno & caus': [],
                        'pp ✗': [],

                        'app': [],
                        'app ✗': [],

                        'ptp': [],
                        'ptp caus': [],
                        'ptp caus & pass': [],
                        'ptp pass': [],
                        'ptp desid': [],
                        'ptp desid & caus': [],
                        'ptp intens': [],
                        'ptp deno': [],
                        'ptp deno & caus': [],
                        'ptp ✗': [],

                    },

                    'nouns': {
                        'masc': [],
                        'masc caus': [],
                        'masc caus & pass': [],
                        'masc pass': [],
                        'masc desid': [],
                        'masc desid & caus': [],
                        'masc intens': [],
                        'masc deno': [],
                        'masc deno & caus': [],
                        'masc ✗': [],

                        'fem': [],
                        'fem caus': [],
                        'fem caus & pass': [],
                        'fem pass': [],
                        'fem desid': [],
                        'fem desid & caus': [],
                        'fem intens': [],
                        'fem deno': [],
                        'fem deno & caus': [],
                        'fem ✗': [],

                        'nt': [],
                        'nt caus': [],
                        'nt caus & pass': [],
                        'nt pass': [],
                        'nt desid': [],
                        'nt desid & caus': [],
                        'nt intens': [],
                        'nt deno': [],
                        'nt deno & caus': [],
                        'nt ✗': [],
                        },

                    'adjectives': {
                        'adj': [],
                        'adj caus': [],
                        'adj caus & pass': [],
                        'adj pass': [],
                        'adj desid': [],
                        'adj desid & caus': [],
                        'adj intens': [],
                        'adj deno': [],
                        'adj deno & caus': [],
                        'adj ✗': [],
                    },

                    'adverbs': {
                        'ind': [],
                        'ind caus': [],
                        'ind caus & pass': [],
                        'ind pass': [],
                        'ind desid': [],
                        'ind desid & caus': [],
                        'ind intens': [],
                        'ind deno': [],
                        'ind deno & caus': [],
                        'ind ✗': [],
                        }
                    }

            # assign words to dict categories
            if i.pos == 'pr':
                # first caus & pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['pr caus & pass'] += [headword]
                    counter += 1

                # desid & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdesid\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['pr desid & caus'] += [headword]
                    counter += 1

                # intens & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bintens\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['pr intens & caus'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['pr deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['pr caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['pr pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['pr intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['pr desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['pr deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['pr'] += [headword]
                    counter += 1

            elif i.pos == 'imp':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['imp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['imp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['imp'] += [headword]
                    counter += 1

            elif i.pos == 'opt':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['opt caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['opt deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['opt caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['opt pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['opt intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['opt desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['opt deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['opt'] += [headword]
                    counter += 1

            elif i.pos == 'perf':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['perf caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['perf deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['perf caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['perf pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['perf intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['perf desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['perf deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['perf'] += [headword]
                    counter += 1

            elif i.pos == 'imperf':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['imperf caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['imperf deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imperf caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imperf pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imperf intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imperf desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['imperf deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['imperf'] += [headword]
                    counter += 1

            elif i.pos == 'aor':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['aor caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['aor deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['aor caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['aor pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['aor intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['aor desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['aor deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['aor'] += [headword]
                    counter += 1

            elif i.pos == 'fut':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['fut caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['aor deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['fut caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['fut pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['fut intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['fut desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['fut deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['fut'] += [headword]
                    counter += 1

            elif i.pos == 'cond':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['cond caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['cond deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['cond caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['cond pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['cond intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['cond desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['cond deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['cond'] += [headword]
                    counter += 1

            elif i.pos == 'abs':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['abs caus & pass'] += [headword]
                    counter += 1

                # desid & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdesid\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['abs desid & caus'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['abs deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['abs caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['abs pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['abs intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['abs desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['abs deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['abs'] += [headword]
                    counter += 1

            elif i.pos == 'ger':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['ger caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['ger deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['ger caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['ger pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['ger intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['ger desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['ger deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['ger'] += [headword]
                    counter += 1

            elif i.pos == 'inf':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['inf caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['verbs']['inf deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['inf caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['inf pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['inf intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['inf desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['verbs']['inf deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['verbs']['inf'] += [headword]
                    counter += 1

            elif i.pos == 'prp':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['prp caus & pass'] += [headword]
                    counter += 1

                # desid and pass
                elif (re.findall(r"\bdesid\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['prp desid & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['prp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['prp'] += [headword]
                    counter += 1

            elif i.pos == 'adj' and re.findall("prp", i.grammar):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['prp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['prp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['prp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['prp'] += [headword]
                    counter += 1

            elif i.pos == 'pp':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['pp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['pp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['pp'] += [headword]
                    counter += 1

            # adj and pp
            elif i.pos == 'adj' and re.findall(r"\bpp\b", i.grammar):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['pp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['pp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['pp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['pp'] += [headword]
                    counter += 1

            # app
            elif re.findall(r"\bapp\b", i.grammar):
                root_matrix[i.root_key]['participles']['app'] += [headword]
                counter += 1

            elif i.pos == 'ptp':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['ptp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['ptp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['ptp'] += [headword]
                    counter += 1

            elif i.pos == 'adj' and re.findall("ptp", i.grammar):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['ptp caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['participles']['ptp deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['participles']['ptp deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['participles']['ptp'] += [headword]
                    counter += 1

            elif i.pos == 'masc':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['masc caus & pass'] += [headword]
                    counter += 1

                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['masc deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['nouns']['masc'] += [headword]
                    counter += 1

            elif i.pos == 'root' and re.findall('masc', i.grammar):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['masc caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['masc deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['masc deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['nouns']['masc'] += [headword]
                    counter += 1

            elif i.pos == 'fem':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['fem caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['fem deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['nouns']['fem'] += [headword]
                    counter += 1

            elif i.pos == 'card' and re.findall("fem", i.grammar):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['fem caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['fem deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['fem deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['nouns']['fem'] += [headword]
                    counter += 1

            elif i.pos == 'nt':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['nt caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['nouns']['nt deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['nt caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['nt pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['nt intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['nt desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['nouns']['nt deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['nouns']['nt'] += [headword]
                    counter += 1
            
            # special case
            elif headword == 'sogandhika 3':
                root_matrix[i.root_key]['nouns']['nt'] += [headword]
                counter += 1


            elif i.pos == 'adj':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['adjectives']['adj caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['adjectives']['adj deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['adjectives']['adj'] += [headword]
                    counter += 1

            elif i.pos == 'suffix' and re.findall('adj', i.root_base):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['adjectives']['adj caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['adjectives']['adj deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['adjectives']['adj deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['adjectives']['adj'] += [headword]
                    counter += 1
            
            elif i.pos == 'ind':
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['adverbs']['ind caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['adverbs']['ind deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['adverbs']['ind'] += [headword]
                    counter += 1
    
            elif i.pos == 'suffix': # and re.findall('ind', 'root_base'):
                # first caus and pass
                if (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bpass\b", i.root_base)):
                    root_matrix[i.root_key]['adverbs']['ind caus & pass'] += [headword]
                    counter += 1
                
                # deno & caus
                elif (re.findall(r"\bcaus\b", i.root_base) and re.findall(r"\bdeno\b", i.root_base)):
                    root_matrix[i.root_key]['adverbs']['ind deno & caus'] += [headword]
                    counter += 1

                # caus
                elif re.findall(r"\bcaus\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind caus'] += [headword]
                    counter += 1

                # pass
                elif re.findall(r"\bpass\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind pass'] += [headword]
                    counter += 1

                # intens
                elif re.findall(r"\bintens\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind intens'] += [headword]
                    counter += 1

                # desid
                elif re.findall(r"\bdesid\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind desid'] += [headword]
                    counter += 1

                # deno
                elif re.findall(r"\bdeno\b", i.root_base):
                    root_matrix[i.root_key]['adverbs']['ind deno'] += [headword]
                    counter += 1

                # normal
                else:
                    root_matrix[i.root_key]['adverbs']['ind'] += [headword]
                    counter += 1

            else:
                print(f"  [bright_red]ERROR: {headword}[white]")
            
            total_counter += 1

    print(f"  roots added: {counter:,} / {total_counter:,}")
    
    # generate html

    print(f"  generating html and adding to db")

    add_to_db = []

    for root_key, data1 in root_matrix.items():
        html = ""
        html += f"<table class='root_matrix'>"
        total_count = 0

        for category, data2 in data1.items():
            cflag = True
            for i.pos, words  in data2.items():
                total_count += len(words)
                if words != []:

                    if cflag == True:
                        html += f"<tr><th colspan='2'>{category}</th></tr>"
                        html += f"<tr><td><b>{i.pos}</b></td><td>"
                        cflag = False

                    elif cflag == False:
                        html += f"<tr><td><b>{i.pos}</b></td><td>"

                    for word in words:
                        if word != words[-1]:
                            html += f"{superscripter_uni(word)}, "
                        else:
                            html += f"{superscripter_uni(word)}</td></tr>"

        html += f"</table>"

        root_mx = FamilyRoot(
            root_id=root_key,
            root_family="matrix",
            html=html,
            count=total_count)
        
        add_to_db.append(root_mx)

        with open(f"xxx delete/root_matrix/{root_key}.html", "w") as words:
            words.write(html)

    db_session.add_all(add_to_db)
    db_session.commit()
