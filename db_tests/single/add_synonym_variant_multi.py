#!/usr/bin/env python3
"""Find synonyms for words that share 2+ cleaned meanings and same pos/grammar signature."""

import json
import sys

import pyperclip
from rich import print
from rich.prompt import Prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.synonym_variant import (
    TILINGA_POS,
    assign_relationship,
    clean_meaning,
    grammar_signature,
    pos_class,
    split_field,
)

# Temporary review filter: when True, only show cross-pos pairs from the
# tiliṅga class (adj/pp/ptp/prp). Set to False to see everything.
ONLY_TILINGA_CROSS_POS = False


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.exceptions: list[str] = self._load_exceptions()
        self.pairs: list[tuple[DpdHeadword, DpdHeadword, list[str]]] = []

    def _load_exceptions(self) -> list[str]:
        try:
            with open(self.pth.syn_var_exceptions_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_exceptions(self) -> None:
        with open(self.pth.syn_var_exceptions_path, "w") as f:
            json.dump(self.exceptions, f, ensure_ascii=False, indent=2)

    def add_exception(self, key: str) -> None:
        self.exceptions.append(key)
        self._save_exceptions()


def _pair_key(pos: str, hw_a: DpdHeadword, hw_b: DpdHeadword, sig: str) -> str:
    lemmas = sorted([hw_a.lemma_clean, hw_b.lemma_clean])
    return f"{pos}:{lemmas[0]}|{lemmas[1]}:{sig}"


def _general_key(pos: str, meanings: list[str]) -> str:
    return f"[{pos}] {'; '.join(sorted(meanings))}"


def find_multi_meaning_pairs(g: GlobalVars) -> None:
    """Find pairs of multi-meaning headwords sharing ≥2 cleaned meanings and same pos/grammar sig."""
    pr.green_tmr("finding multi-meaning pairs")

    buckets: dict[tuple[str, str], list[tuple[DpdHeadword, frozenset[str]]]] = {}

    syn_sets: dict[int, set[str]] = {}
    phon_sets: dict[int, set[str]] = {}
    text_sets: dict[int, set[str]] = {}

    for hw in g.dpd_db:
        syn_sets[hw.id] = set(hw.synonym_list)
        phon_sets[hw.id] = split_field(hw.var_phonetic)
        text_sets[hw.id] = split_field(hw.var_text)
        if not hw.meaning_1 or "; " not in hw.meaning_1:
            continue
        cleaned: frozenset[str] = frozenset(
            m for raw in hw.meaning_1.split("; ") if (m := clean_meaning(raw))
        )
        if not cleaned:
            continue
        sig = grammar_signature(hw.grammar)
        bucket_key = (pos_class(hw.pos), sig)
        buckets.setdefault(bucket_key, []).append((hw, cleaned))

    pairs: list[tuple[DpdHeadword, DpdHeadword, list[str]]] = []
    seen: set[frozenset[int]] = set()

    for (pos, sig), entries in buckets.items():
        meaning_to_hws: dict[str, list[DpdHeadword]] = {}
        for hw, meanings in entries:
            for m in meanings:
                meaning_to_hws.setdefault(m, []).append(hw)

        for hw_a, meanings_a in entries:
            candidates: dict[int, DpdHeadword] = {}
            for m in meanings_a:
                for hw_b in meaning_to_hws[m]:
                    if hw_b.id != hw_a.id:
                        candidates[hw_b.id] = hw_b

            for hw_b in candidates.values():
                if ONLY_TILINGA_CROSS_POS and not (
                    hw_a.pos != hw_b.pos
                    and hw_a.pos in TILINGA_POS
                    and hw_b.pos in TILINGA_POS
                ):
                    continue
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                seen.add(edge)
                if hw_a.lemma_clean == hw_b.lemma_clean:
                    continue
                meanings_b = frozenset(
                    m for raw in hw_b.meaning_1.split("; ") if (m := clean_meaning(raw))
                )
                shared = meanings_a & meanings_b
                if len(shared) < 2:
                    continue
                key = _pair_key(pos, hw_a, hw_b, sig)
                gen_key = _general_key(pos, list(shared))
                if key in g.exceptions or gen_key in g.exceptions:
                    continue
                b_clean = hw_b.lemma_clean
                a_clean = hw_a.lemma_clean
                a_has_b = (
                    b_clean in syn_sets[hw_a.id]
                    or b_clean in phon_sets[hw_a.id]
                    or b_clean in text_sets[hw_a.id]
                )
                b_has_a = (
                    a_clean in syn_sets[hw_b.id]
                    or a_clean in phon_sets[hw_b.id]
                    or a_clean in text_sets[hw_b.id]
                )
                already_related = a_has_b and b_has_a
                if already_related:
                    continue
                pairs.append((hw_a, hw_b, sorted(shared)))

    g.pairs = pairs
    pr.yes(str(len(g.pairs)))


def find_identical_meaning_clusters(
    g: GlobalVars,
) -> list[tuple[str, str, frozenset[str], list[DpdHeadword]]]:
    """Group headwords with identical cleaned meaning-sets into clusters.

    Within a cluster, every member is a true synonym of every other,
    so one user decision can write all N×(N-1)/2 syn relationships.
    Returns clusters sorted by size descending.
    """
    pr.green_tmr("finding identical-meaning clusters")

    buckets: dict[tuple[str, str, frozenset[str]], list[DpdHeadword]] = {}
    for hw in g.dpd_db:
        if not hw.meaning_1 or "; " not in hw.meaning_1:
            continue
        cleaned = frozenset(
            m for raw in hw.meaning_1.split("; ") if (m := clean_meaning(raw))
        )
        if len(cleaned) < 2:
            continue
        sig = grammar_signature(hw.grammar)
        buckets.setdefault((pos_class(hw.pos), sig, cleaned), []).append(hw)

    clusters: list[tuple[str, str, frozenset[str], list[DpdHeadword]]] = []
    exceptions = set(g.exceptions)
    for (pcls, sig, meanings), members in buckets.items():
        if len(members) < 3:
            continue
        if ONLY_TILINGA_CROSS_POS and not (
            pcls == "tiliṅga" and len({m.pos for m in members}) >= 2
        ):
            continue
        # skip if cluster has a general exception
        if _general_key(pcls, sorted(meanings)) in exceptions:
            continue
        # skip if every pair is already related (syn/var_phon/var_text)
        if _all_pairs_related(members):
            continue
        clusters.append((pcls, sig, meanings, members))

    clusters.sort(key=lambda c: -len(c[3]))
    pr.yes(str(len(clusters)))
    return clusters


def _all_pairs_related(members: list[DpdHeadword]) -> bool:
    """Cluster is fully resolved if every pair is already related — in syn,
    var_phonetic, or var_text. Curated phonetic/textual variants count as
    'no work needed' just as much as synonyms do.
    """
    related: dict[int, set[str]] = {
        m.id: set(m.synonym_list)
        | split_field(m.var_phonetic)
        | split_field(m.var_text)
        for m in members
    }
    for i, a in enumerate(members):
        for b in members[i + 1 :]:
            if b.lemma_clean not in related[a.id]:
                return False
            if a.lemma_clean not in related[b.id]:
                return False
    return True


def prompt_clusters(
    g: GlobalVars,
    clusters: list[tuple[str, str, frozenset[str], list[DpdHeadword]]],
) -> bool:
    """One prompt per cluster — (a)ccept all pairwise / (pass) / (r)estart / (q)uit.

    Returns True if a restart was requested.
    """
    if not clusters:
        return False
    pr.green("approving identical-meaning clusters")

    total = len(clusters)
    for counter, (pcls, sig, meanings, members) in enumerate(clusters):
        print("\n" + "=" * 100)
        print(
            f"[white]cluster {counter + 1} / {total}  "
            f"[blue][{pcls}]  [green]{'; '.join(sorted(meanings))}  "
            f"[white]({len(members)} members)"
        )
        print("=" * 100)
        for m in members:
            print(_entry_label(m))
            print(f"[cyan]{_format_fields(m)}")

        gui_string = db_search_string([m.lemma_1 for m in members], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](s)ynonym all pairwise, (g)eneral exception, (pass), (r)estart, (q)uit"
        )

        if choice == "s":
            written = 0
            skipped_phon = 0
            for i, a in enumerate(members):
                a_syn = set(a.synonym_list)
                a_phon = split_field(a.var_phonetic)
                for b in members[i + 1 :]:
                    if a.lemma_clean == b.lemma_clean:
                        continue
                    b_phon = split_field(b.var_phonetic)
                    if b.lemma_clean in a_phon or a.lemma_clean in b_phon:
                        skipped_phon += 1
                        print(
                            f"  [yellow]kept as phonetic variant: "
                            f"{a.lemma_1} ↔ {b.lemma_1}"
                        )
                        continue
                    if b.lemma_clean in a_syn and a.lemma_clean in set(b.synonym_list):
                        continue
                    assign_relationship(a, b.lemma_clean, "synonym")
                    assign_relationship(b, a.lemma_clean, "synonym")
                    written += 1
            g.db_session.commit()
            print(
                f"  [green]wrote {written} new pairwise syn relationships"
                f"  [yellow]({skipped_phon} preserved as phonetic variants)"
            )

        elif choice == "g":
            gen_key = _general_key(pcls, sorted(meanings))
            if gen_key not in g.exceptions:
                g.add_exception(gen_key)
                print(f"  [red]general exception added: {gen_key!r}")
            else:
                print(f"  [yellow]general exception already present: {gen_key!r}")

        elif choice == "r":
            return True

        elif choice == "q":
            pr.toc()
            sys.exit(0)

    return False


def _entry_label(hw: DpdHeadword) -> str:
    family_root = f" [magenta]{hw.family_root}" if hw.family_root else ""
    family_word = f" [magenta]{hw.family_word}" if hw.family_word else ""
    return (
        f"[yellow]{hw.lemma_1} [blue]{hw.pos} "
        f"[green]{hw.meaning_1} [white]({hw.degree_of_completion})"
        f"{family_root}{family_word}"
    )


def _format_fields(hw: DpdHeadword) -> str:
    syn = hw.synonym.split(", ") if hw.synonym else []
    var = hw.variant.split(", ") if hw.variant else []
    var_text = hw.var_text.split(", ") if hw.var_text else []
    phon = sorted(split_field(hw.var_phonetic))
    return f"  syn:{syn}\n  var:{var}\n  var_text:{var_text}\n  var_phon:{phon}"


def _show_result(hw: DpdHeadword) -> None:
    print()
    print(f"[green]{hw.lemma_1}:")
    print(f"[green]{_format_fields(hw)}")


def prompt_pairs(g: GlobalVars) -> bool:
    """Walk through pairs and prompt the user. Returns True if restart requested."""
    pr.green("adding synonyms to db")

    total = len(g.pairs)

    for counter, (hw_a, hw_b, shared) in enumerate(g.pairs):
        pos = pos_class(hw_a.pos)
        gen_key = _general_key(pos, shared)
        if gen_key in g.exceptions:
            continue

        print("\n" + "-" * 100)
        print("[white][dim]synonym: different construction.")
        print("[white][dim]phonetic: same construction, different spelling.")
        print("[white][dim]textual: manuscript variant.")
        print("-" * 100 + "\n")
        shared_label = " | ".join(shared)
        print(f"[white]{counter + 1} / {total}  [green]{shared_label}")
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        print(_entry_label(hw_b))
        print(f"[cyan]{_format_fields(hw_b)}")

        sig = grammar_signature(hw_a.grammar)
        key = _pair_key(pos, hw_a, hw_b, sig)

        gui_string = db_search_string([hw_a.lemma_1, hw_b.lemma_1], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](s)ynonym, (p)honetic, (t)extual, (e)xception, (g)eneral, (pass), (r)estart, (q)uit"
        )

        if choice == "s":
            assign_relationship(hw_a, hw_b.lemma_clean, "synonym")
            assign_relationship(hw_b, hw_a.lemma_clean, "synonym")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "p":
            assign_relationship(hw_a, hw_b.lemma_clean, "var_phonetic")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_phonetic")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "t":
            assign_relationship(hw_a, hw_b.lemma_clean, "var_text")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_text")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "e":
            g.add_exception(key)
            print(f"  [red]exception added: {key!r}")

        elif choice == "g":
            g.add_exception(gen_key)
            print(f"  [red]general exception added: {gen_key!r}")

        elif choice == "r":
            return True

        elif choice == "q":
            break

    return False


def main() -> None:
    pr.tic()
    print("[bright_yellow]synonym multi — finding and adding multi-meaning synonyms")
    while True:
        g = GlobalVars()
        # Phase 1: bulk-accept clusters of headwords with identical meaning sets.
        clusters = find_identical_meaning_clusters(g)
        if prompt_clusters(g, clusters):
            continue
        # Phase 2: existing pairwise pass for partial-overlap residual.
        # Re-run discovery so newly-syn pairs from Phase 1 are filtered out.
        find_multi_meaning_pairs(g)
        if prompt_pairs(g):
            continue
        break
    pr.toc()


if __name__ == "__main__":
    main()
