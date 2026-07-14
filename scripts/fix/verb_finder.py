"""Exploratory diagnostic for present-tense verbs and their derived forms.

Read-only. Produces TSV reports under temp/verb_finder/ and a terminal summary.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

DERIVED_POS = (
    "pp",
    "prp",
    "ptp",
    "abs",
    "ger",
    "inf",
    "aor",
    "fut",
    "imp",
    "opt",
    "perf",
    "imperf",
    "cond",
)
SPECIAL_VERB_MARKERS = ("caus", "pass", "intens", "desid", "deno", "impers")


# (family_root, root_key) -> list of pr lemmas (full lemma_1, may include " 1"/" 2" homonym suffix)
PrIndex = dict[tuple[str, str], list[str]]
# cleaned lemma (no trailing " <digit>") -> list of full pr lemma_1s
PrLemmaMap = dict[str, list[str]]


_HOMONYM_RE = re.compile(r"\s+\d+(?:\.\d+)*$")


def lemma_clean(lemma: str) -> str:
    """Strip a trailing homonym number (e.g. 'karoti 1', 'kaṅkhati 1.1' -> base)."""
    return _HOMONYM_RE.sub("", lemma)


@dataclass
class GrammarRef:
    """Parsed view of a derived-form `grammar` string."""

    original: str
    head: str  # e.g. "pp", "ptp"
    na: bool  # True when "of na X"
    is_root: bool  # True when target is "√xxx"
    target: str  # the verb lemma or the root (without √ prefix when is_root)
    suffix: (
        str  # preserved trailing text after the verb/root (", in comps", " ??", etc.)
    )
    special_verb: bool  # caus/pass/intens/desid/deno/impers detected in string


# ---------- TSV ----------


def write_tsv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------- Index ----------


def build_pr_verb_index(db) -> tuple[PrIndex, PrLemmaMap]:
    """Index every pos='pr' headword."""
    index: PrIndex = {}
    lemma_map: PrLemmaMap = {}
    rows = (
        db.query(
            DpdHeadword.lemma_1,
            DpdHeadword.family_root,
            DpdHeadword.root_key,
        )
        .filter(DpdHeadword.pos == "pr")
        .all()
    )
    for lemma_1, family_root, root_key in rows:
        key = (family_root or "", root_key or "")
        index.setdefault(key, []).append(lemma_1)
        lemma_map.setdefault(lemma_clean(lemma_1), []).append(lemma_1)
    return index, lemma_map


def find_roots_without_pr(db, pr_index: PrIndex) -> list[dict]:
    """Family_root + root_key pairs used by other headwords but with no pr verb."""
    pair_examples: dict[tuple[str, str], dict] = {}
    rows = (
        db.query(
            DpdHeadword.lemma_1,
            DpdHeadword.pos,
            DpdHeadword.family_root,
            DpdHeadword.root_key,
        )
        .filter(DpdHeadword.family_root != "")
        .filter(DpdHeadword.root_key != "")
        .all()
    )
    for lemma_1, pos, family_root, root_key in rows:
        key = (family_root, root_key)
        entry = pair_examples.setdefault(
            key,
            {
                "family_root": family_root,
                "root_key": root_key,
                "example_lemma": lemma_1,
                "example_pos": pos,
                "headword_count": 0,
            },
        )
        entry["headword_count"] += 1
    return [
        entry for key, entry in sorted(pair_examples.items()) if key not in pr_index
    ]


# ---------- Grammar parser ----------


# Two patterns: root form ("<head> of [na ]<prefixes…> √<root><suffix>")
# and verb form ("<head> of [na ]<lemma><suffix>"). Root form is detected by √.
_HEAD_OF_RE = re.compile(r"^\s*(?P<head>\w+)\s+of\s+(?P<rest>.+)$")


def parse_grammar(grammar: str, pos: str) -> GrammarRef | None:
    """Parse a derived-form `grammar` string into a `GrammarRef`.

    Returns None when the string does not match the canonical "<head> of ..." pattern.
    """
    if not grammar:
        return None
    text = grammar.strip()
    special = any(f" {m} of " in f" {text} " for m in SPECIAL_VERB_MARKERS)

    m = _HEAD_OF_RE.match(text)
    if not m or m.group("head") != pos:
        return None

    rest = m.group("rest")

    # Split off a trailing suffix that begins at ", " (e.g. ", in comps", ", irreg").
    body, sep, tail = rest.partition(",")
    suffix = f"{sep}{tail}" if sep else ""
    body = body.strip()

    na = False
    if body.startswith("na "):
        na = True
        body = body[3:].lstrip()

    if "√" in body:
        # Root reference; target is the whole body (e.g. "√dhā" or "ati ā √dhā").
        return GrammarRef(
            original=grammar,
            head=m.group("head"),
            na=na,
            is_root=True,
            target=body,
            suffix=suffix,
            special_verb=special,
        )

    # Verb reference; target is the first whitespace-delimited token.
    target = body.split()[0] if body else ""
    return GrammarRef(
        original=grammar,
        head=m.group("head"),
        na=na,
        is_root=False,
        target=target,
        suffix=suffix,
        special_verb=special,
    )


# ---------- Scan derived forms ----------


def _build_proposed_to_root(ref: GrammarRef, family_root: str) -> str:
    na = "na " if ref.na else ""
    return f"{ref.head} of {na}{family_root}{ref.suffix}"


def _build_proposed_to_verb(ref: GrammarRef, verb_lemma: str) -> str:
    na = "na " if ref.na else ""
    return f"{ref.head} of {na}{verb_lemma}{ref.suffix}"


def scan_derived_forms(
    db,
    pr_index: PrIndex,
    pr_lemma_map: PrLemmaMap,
) -> dict[str, list[dict]]:
    """Bucket every derived form by what change (if any) it needs."""
    buckets: dict[str, list[dict]] = {
        "ok_verb_present": [],
        "would_change_to_root": [],
        "would_change_to_verb": [],
        "ambiguous": [],
        "special_verbs": [],
        "unparsed": [],
        "grammar_derived_from_mismatch": [],
    }

    rows = (
        db.query(
            DpdHeadword.id,
            DpdHeadword.lemma_1,
            DpdHeadword.pos,
            DpdHeadword.root_key,
            DpdHeadword.family_root,
            DpdHeadword.grammar,
            DpdHeadword.derived_from,
            DpdHeadword.verb,
        )
        .filter(DpdHeadword.pos.in_(DERIVED_POS))
        .all()
    )

    for (
        id_,
        lemma_1,
        pos,
        root_key,
        family_root,
        grammar,
        derived_from,
        verb_col,
    ) in rows:
        ref = parse_grammar(grammar or "", pos)
        base = {
            "id": id_,
            "lemma_1": lemma_1,
            "pos": pos,
            "root_key": root_key or "",
            "family_root": family_root or "",
            "verb_col": verb_col or "",
            "grammar_current": grammar or "",
            "derived_from": derived_from or "",
        }

        # Special verbs first (verb column OR grammar marker) — detect-only bucket.
        if (verb_col and verb_col.strip()) or (ref and ref.special_verb):
            buckets["special_verbs"].append(
                {
                    **base,
                    "grammar_proposed": "",
                    "reason": "special verb type",
                    "candidates": "",
                }
            )
            continue

        if ref is None:
            buckets["unparsed"].append(
                {
                    **base,
                    "grammar_proposed": "",
                    "reason": "no <pos> of <x> pattern",
                    "candidates": "",
                }
            )
            continue

        # Grammar/derived_from mismatch flag (recorded in addition to main bucket).
        if not ref.is_root and derived_from and ref.target != derived_from:
            buckets["grammar_derived_from_mismatch"].append(
                {
                    **base,
                    "grammar_target": ref.target,
                    "reason": "grammar target != derived_from",
                }
            )

        if ref.is_root:
            # Grammar already references a root form. Check if a pr verb exists for
            # this row's (family_root, root_key) pair — if so, it should reference the verb.
            key = (family_root or "", root_key or "")
            pair_candidates = pr_index.get(key, [])
            if len(pair_candidates) == 0:
                buckets["ok_verb_present"].append(
                    {
                        **base,
                        "grammar_proposed": grammar or "",
                        "reason": "no pr at (family_root,root_key); root form correct",
                        "candidates": "",
                    }
                )
            else:
                clean_pair = sorted({lemma_clean(lem) for lem in pair_candidates})
                if len(clean_pair) == 1:
                    proposed = _build_proposed_to_verb(ref, clean_pair[0])
                    buckets["would_change_to_verb"].append(
                        {
                            **base,
                            "grammar_proposed": proposed,
                            "reason": "single pr at (family_root,root_key)",
                            "candidates": clean_pair[0],
                        }
                    )
                else:
                    buckets["ambiguous"].append(
                        {
                            **base,
                            "grammar_proposed": "",
                            "reason": "multiple pr at (family_root,root_key)",
                            "candidates": "|".join(clean_pair),
                        }
                    )
        else:
            # Grammar references a verb lemma. Match on cleaned form to handle homonyms.
            matches = pr_lemma_map.get(lemma_clean(ref.target), [])
            if matches:
                clean_matches = sorted({lemma_clean(lem) for lem in matches})
                buckets["ok_verb_present"].append(
                    {
                        **base,
                        "grammar_proposed": grammar or "",
                        "reason": "verb exists as pr",
                        "candidates": "|".join(clean_matches),
                    }
                )
            else:
                # Referenced verb not in dict as pr. Look for a pr verb at this row's
                # (family_root, root_key) before falling back to a root proposal.
                key = (family_root or "", root_key or "")
                pair_candidates = pr_index.get(key, [])
                clean_pair = sorted({lemma_clean(lem) for lem in pair_candidates})
                if len(clean_pair) == 1:
                    proposed = _build_proposed_to_verb(ref, clean_pair[0])
                    buckets["would_change_to_verb"].append(
                        {
                            **base,
                            "grammar_proposed": proposed,
                            "reason": "referenced verb absent; single pr at (family_root,root_key)",
                            "candidates": clean_pair[0],
                        }
                    )
                elif len(clean_pair) > 1:
                    buckets["ambiguous"].append(
                        {
                            **base,
                            "grammar_proposed": "",
                            "reason": "referenced verb absent; multiple pr at (family_root,root_key)",
                            "candidates": "|".join(clean_pair),
                        }
                    )
                else:
                    fr = family_root or ""
                    proposed = _build_proposed_to_root(ref, fr) if fr else ""
                    reason = "referenced verb not in db as pr; no pr at (family_root,root_key)"
                    if not fr:
                        reason += " (no family_root on this entry)"
                    buckets["would_change_to_root"].append(
                        {
                            **base,
                            "grammar_proposed": proposed,
                            "reason": reason,
                            "candidates": ref.target,
                        }
                    )

    return buckets


# ---------- Self-tests for parser ----------


def _selftest_parse_grammar() -> None:
    cases = [
        ("pp of russati", "pp", False, False, "russati", ""),
        ("pp of na karoti", "pp", True, False, "karoti", ""),
        ("pp of √rus", "pp", False, True, "√rus", ""),
        ("pp of na karoti, in comps", "pp", True, False, "karoti", ", in comps"),
        ("ptp of √dis", "ptp", False, True, "√dis", ""),
        ("abs of √dis, irreg", "abs", False, True, "√dis", ", irreg"),
        ("ger of ati ā √dhā", "ger", False, True, "ati ā √dhā", ""),
    ]
    for text, head, na, is_root, target, suffix in cases:
        ref = parse_grammar(text, head)
        assert ref is not None, f"failed to parse: {text!r}"
        assert ref.head == head, (text, ref)
        assert ref.na == na, (text, ref)
        assert ref.is_root == is_root, (text, ref)
        assert ref.target == target, (text, ref)
        assert ref.suffix == suffix, (text, ref)


# ---------- Main ----------


def main() -> None:
    pr.yellow_title("verb finder")
    pr.tic()
    _selftest_parse_grammar()

    pth = ProjectPaths()
    db = get_db_session(pth.dpd_db_path)
    output_dir = pth.temp_dir / "verb_finder"

    pr.white("building pr verb index")
    pr_index, pr_lemma_map = build_pr_verb_index(db)
    pr.summary("pr verb count", str(sum(len(v) for v in pr_index.values())))
    pr.summary("unique (family_root, root_key) with pr", str(len(pr_index)))

    write_tsv(
        [
            {
                "family_root": fr,
                "root_key": rk,
                "pr_lemmas": "|".join(lemmas),
                "count": len(lemmas),
            }
            for (fr, rk), lemmas in sorted(pr_index.items())
        ],
        output_dir / "pr_verb_index.tsv",
    )

    pr.white("finding roots without pr")
    roots_without_pr = find_roots_without_pr(db, pr_index)
    write_tsv(roots_without_pr, output_dir / "roots_without_pr.tsv")
    pr.summary("(family_root, root_key) with no pr", str(len(roots_without_pr)))

    pr.white("scanning derived forms")
    buckets = scan_derived_forms(db, pr_index, pr_lemma_map)

    bucket_files = {
        "would_change_to_root": "would_change_to_root.tsv",
        "would_change_to_verb": "would_change_to_verb.tsv",
        "ambiguous": "ambiguous.tsv",
        "special_verbs": "special_verbs.tsv",
        "unparsed": "unparsed.tsv",
        "grammar_derived_from_mismatch": "grammar_derived_from_mismatch.tsv",
        "ok_verb_present": "ok_verb_present.tsv",
    }
    for name, fname in bucket_files.items():
        write_tsv(buckets[name], output_dir / fname)
        pr.summary(name, str(len(buckets[name])))

    total = sum(len(v) for v in buckets.values())
    pr.summary("total derived forms scanned", str(total))

    # Spotcheck the user's cited examples.
    pr.green_title("spotcheck")
    targets = {"ruṭṭha", "rusita", "akkanta 1"}
    for name, rows in buckets.items():
        for row in rows:
            if row["lemma_1"] in targets:
                pr.white(
                    f"  [{name}] {row['lemma_1']} | grammar='{row['grammar_current']}' "
                    f"| proposed='{row.get('grammar_proposed', '')}'"
                )

    pr.toc()


if __name__ == "__main__":
    main()
