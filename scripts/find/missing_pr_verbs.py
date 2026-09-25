"""Find present-tense verbs the texts attest but the dictionary lacks.

Derived forms name the present verb they come from in their `grammar` — "pp of
russati". When that verb has no `pos='pr'` headword the entry is dangling: either
the verb needs adding, or the grammar should point at a root instead. Which one
depends on whether the corpora attest the verb, so this script collects every
referenced-but-missing verb, counts it across CST, SuttaCentral and BJT, fills in
what follows mechanically, and queues the attested ones for manual completion in
gui2's pass2add X button.

Read-only against dpd.db. No headwords are created — the editor adds them.

Two tiers of field, because most of the derivations are only mostly right:

- **Real fields** get values that follow with certainty from the entries naming
  the verb: lemma, pos, grammar, root, family root, stem, pattern.
- **`_add` fields** get proposals the editor accepts or rejects with the transfer
  button. Measured against the 3975 plain present verbs already in the
  dictionary: root sign from the root record is right 70% of the time,
  construction 66%, the Sanskrit bracket 96% without a prefix and 64% with one.
  Prefix sandhi is what breaks them — the real entries spell it out
  ("ati > aty > acc + aya + ti"), which cannot be reconstructed from the parts.

`family_compound` and `family_idioms` are deliberately left empty: 3158 of those
3975 verbs leave both blank, and the field is used for genuine compounds holding
their components, not for the word itself.

Usage:
    uv run scripts/find/missing_pr_verbs.py              # reports, writes temp output
    uv run scripts/find/missing_pr_verbs.py --load-gui   # also fills gui2's X queue
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, InflectionTemplates, Lookup
from gui2.dpd_fields_lists import PASS1_FIELDS
from gui2.paths import Gui2Paths
from scripts.fix.verb_finder import (
    DERIVED_POS,
    lemma_clean,
    parse_grammar,
    write_tsv,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

CORPORA = ("cst", "sc", "bjt")

# The editor works these with pass2add's pass1-field filter on, so anything
# outside that list is invisible there. Each field's `_add` sibling is allowed
# too: that is where a derivation the editor should check goes.
QUEUE_FIELDS = set(PASS1_FIELDS) | {f"{name}_add" for name in PASS1_FIELDS}

# Longest first: pariniṭṭhāti must match "āti", not "ati".
PATTERN_ENDINGS = ("āti", "oti", "eti", "ati")


def collect_wanted_verbs(db: Session) -> dict[str, list[dict[str, str]]]:
    """Map each referenced-but-missing present verb to the entries that name it."""
    pr_lemmas = {
        lemma_clean(lemma)
        for (lemma,) in db.query(DpdHeadword.lemma_1)
        .filter(DpdHeadword.pos == "pr")
        .all()
    }

    rows = (
        db.query(
            DpdHeadword.lemma_1,
            DpdHeadword.pos,
            DpdHeadword.grammar,
            DpdHeadword.family_root,
            DpdHeadword.root_key,
            DpdHeadword.meaning_1,
        )
        .filter(DpdHeadword.pos.in_(DERIVED_POS))
        # Unfinished drafts would contribute guesses, not evidence.
        .filter(DpdHeadword.meaning_1 != "")
        .all()
    )

    wanted: dict[str, list[dict[str, str]]] = {}
    for lemma_1, pos, grammar, family_root, root_key, meaning_1 in rows:
        ref = parse_grammar(grammar or "", pos)
        if ref is None or ref.is_root:
            continue
        target = lemma_clean(ref.target)
        # Multi-word targets are compound verbs, not single lemmas; a bare
        # particle is a truncated grammar string.
        if not target or " " in target or target in ("na", "no"):
            continue
        if target in pr_lemmas:
            continue
        wanted.setdefault(target, []).append(
            {
                "lemma_1": lemma_1,
                "pos": pos,
                "grammar": grammar or "",
                "family_root": family_root or "",
                "root_key": root_key or "",
                "meaning_1": meaning_1 or "",
            }
        )
    return wanted


def load_corpus_freq(pth: ProjectPaths) -> dict[str, Counter[str]]:
    """Total occurrences of every word form in each corpus."""
    freqs: dict[str, Counter[str]] = {}
    for name in CORPORA:
        path: Path = getattr(pth, f"{name}_freq_json")
        with path.open(encoding="utf-8") as f:
            loaded = json.load(f)
        freqs[name] = Counter(loaded if isinstance(loaded, dict) else {})
    return freqs


def load_already_seen(db: Session) -> set[str]:
    """Verbs the editor has already been shown and chose not to add.

    The X button archives every entry it hands over, so the done file is a
    record of what has been looked at. Anything in it that is still not a
    present headword was a deliberate no — 19 of them after the first batch.
    """
    done_path = Gui2Paths().pass2_x_words_done_path
    if not done_path.exists():
        return set()
    try:
        with done_path.open(encoding="utf-8") as f:
            done = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()
    if not isinstance(done, dict):
        return set()

    added = {
        lemma_clean(lemma)
        for (lemma,) in db.query(DpdHeadword.lemma_1)
        .filter(DpdHeadword.pos == "pr")
        .all()
    }
    return {verb for verb in done if verb not in added}


def load_roots(db: Session) -> dict[str, DpdRoot]:
    return {root.root: root for root in db.query(DpdRoot).all()}


def split_stem(verb: str) -> tuple[str, str]:
    """Split a present verb into (stem, pattern), or ("", "") if the ending is unknown."""
    for ending in PATTERN_ENDINGS:
        if verb.endswith(ending) and len(verb) > len(ending):
            return verb[: -len(ending)], f"{ending} pr"
    return "", ""


def prefixes(family_root: str) -> list[str]:
    """The prefixes in a family_root: "ati ā √vad" -> ["ati", "ā"]."""
    if "√" not in family_root:
        return []
    return family_root.split("√")[0].split()


def _agreed(entries: list[dict[str, str]], field: str) -> tuple[str, bool]:
    """The value the referring entries agree on, and whether they disagreed."""
    values = Counter(e[field] for e in entries if e[field])
    if not values:
        return "", False
    return values.most_common(1)[0][0], len(values) > 1


def derive_certain(verb: str, entries: list[dict[str, str]]) -> dict[str, str]:
    """Fields that follow with certainty from the entries naming this verb."""
    stem, pattern = split_stem(verb)
    root_key, root_split = _agreed(entries, "root_key")
    family_root, family_split = _agreed(entries, "family_root")
    return {
        "lemma_1": verb,
        "lemma_2": verb,
        "pos": "pr",
        "grammar": "pr",
        "root_key": root_key,
        "family_root": family_root,
        "stem": stem,
        "pattern": pattern,
        "_root_disagreement": "yes" if root_split or family_split else "",
    }


def derive_proposals(
    verb: str,
    certain: dict[str, str],
    entries: list[dict[str, str]],
    roots: dict[str, DpdRoot],
) -> dict[str, str]:
    """Proposals for the `_add` fields — right most of the time, not always.

    The editor transfers the ones that hold. See the module docstring for the
    measured hit rates and why prefix sandhi caps them.
    """
    proposals: dict[str, str] = {}
    root = roots.get(certain["root_key"])
    pre = prefixes(certain["family_root"])
    # "ti" is the only part that strips cleanly; the prefix cannot be removed
    # from the front because sandhi has already reshaped it (ā √kam > akkamati).
    base = verb[:-2] if verb.endswith("ti") else ""

    if root and root.root_sign:
        proposals["root_sign_add"] = root.root_sign
        # A root carrying several signs ("e, aya") gives no single formula, and
        # splicing the list in produces a malformed one. Offer the signs alone.
        if base and "," not in root.root_sign:
            bare_root = certain["root_key"].split()[0]
            proposals["root_base_add"] = f"{bare_root} + {root.root_sign} > {base}"

    if base:
        proposals["construction_add"] = " + ".join([*pre, base, "ti"])

    if root and root.sanskrit_root:
        # The bracket is prefix + Sanskrit root; the inflected form in front of
        # it needs Sanskrit verb formation, so it is left to the editor.
        first = root.sanskrit_root.split()[0].lstrip("√")
        proposals["sanskrit_add"] = f"[{''.join(pre)}{first}]"

    # A past participle's meaning is the best available clue to its verb's.
    # pass1 shows meaning_2, so the proposal goes to its sibling.
    glosses = [f"{e['lemma_1']} ({e['pos']}): {e['meaning_1']}" for e in entries]
    if glosses:
        proposals["meaning_2_add"] = " | ".join(glosses)

    return proposals


def load_templates(db: Session) -> dict[str, list]:
    """Each present pattern's stem/ending grid, keyed by pattern name."""
    return {
        template.pattern: json.loads(template.data)
        for template in db.query(InflectionTemplates).all()
        if template.data
    }


def build_paradigm(
    stem: str, pattern: str, templates: dict[str, list]
) -> dict[str, str]:
    """Every inflected form the pattern generates for this stem, form -> label.

    Mirrors `generate_inflection_tables.generate_inflection_table`: row 0 is the
    header, odd columns hold the endings, and the grammar label sits in the
    column after them.
    """
    table = templates.get(pattern)
    if not table:
        return {}
    clean_stem = re.sub(r"[!*]", "", stem)

    forms: dict[str, str] = {}
    for row_number, row in enumerate(table):
        if row_number == 0:
            continue
        for column_number, cell in enumerate(row):
            if column_number == 0 or column_number % 2 == 0:
                continue
            label_cell = (
                row[column_number + 1] if column_number + 1 < len(row) else [""]
            )
            label = label_cell[0] if label_cell else ""
            for ending in cell:
                if ending:
                    forms.setdefault(f"{clean_stem}{ending}", label)
    return forms


def load_known_forms(db: Session) -> set[str]:
    """Every form the dictionary already accounts for.

    A generated form that some other headword already owns is not evidence for
    the missing verb — it is a collision, and treating it as attestation would
    manufacture verbs out of unrelated words.
    """
    return {
        key
        for (key,) in db.query(Lookup.lookup_key).filter(Lookup.headwords != "").all()
    }


def search_paradigm(
    verb: str,
    certain: dict[str, str],
    templates: dict[str, list],
    freqs: dict[str, Counter[str]],
    known_forms: set[str],
) -> list[dict[str, str]]:
    """Corpus hits for this verb's other inflected forms, best first."""
    paradigm = build_paradigm(certain["stem"], certain["pattern"], templates)
    hits: list[dict[str, str]] = []
    for form, label in paradigm.items():
        # The 3rd singular is the exact-form check that already failed.
        if form == verb or form in known_forms:
            continue
        for name in CORPORA:
            count = freqs[name].get(form, 0)
            if count:
                hits.append(
                    {"form": form, "label": label, "corpus": name, "count": str(count)}
                )
    hits.sort(key=lambda h: -int(h["count"]))
    return hits


def build_report(
    wanted: dict[str, list[dict[str, str]]],
    freqs: dict[str, Counter[str]],
    roots: dict[str, DpdRoot],
) -> list[dict]:
    """One row per wanted verb: attestation evidence plus every derived value."""
    rows: list[dict] = []
    for verb, entries in sorted(wanted.items()):
        counts = {name: freqs[name].get(verb, 0) for name in CORPORA}
        certain = derive_certain(verb, entries)
        proposals = derive_proposals(verb, certain, entries, roots)
        root = roots.get(certain["root_key"])
        rows.append(
            {
                "verb": verb,
                **{f"{name}_count": counts[name] for name in CORPORA},
                "attested": "yes" if any(counts.values()) else "",
                "referring_count": len(entries),
                "referring_lemmas": "|".join(e["lemma_1"] for e in entries),
                "root_key": certain["root_key"],
                "family_root": certain["family_root"],
                "root_meaning": root.root_meaning if root else "",
                "stem": certain["stem"],
                "pattern": certain["pattern"],
                "root_sign_add": proposals.get("root_sign_add", ""),
                "root_base_add": proposals.get("root_base_add", ""),
                "construction_add": proposals.get("construction_add", ""),
                "sanskrit_add": proposals.get("sanskrit_add", ""),
                "root_disagreement": certain["_root_disagreement"],
                # No present-tense ending means the grammar names something that
                # is not a present verb at all — an infinitive, an absolutive, a
                # participle, or a broken string.
                "not_a_pr_verb": "" if certain["pattern"] else "yes",
            }
        )
    return rows


def build_x_queue(
    wanted: dict[str, list[dict[str, str]]],
    freqs: dict[str, Counter[str]],
    roots: dict[str, DpdRoot],
    paradigm_hits: dict[str, list[dict[str, str]]],
    already_seen: set[str],
) -> dict[str, dict[str, str]]:
    """The gui2 X-button queue: attested verbs only, keyed by lemma, no `id`."""
    queue: dict[str, dict[str, str]] = {}
    for verb, entries in sorted(wanted.items()):
        # Queued before and still not a headword — the editor looked at it and
        # said no. Re-queueing it every run wastes their time.
        if verb in already_seen:
            continue
        exact = any(freqs[name].get(verb, 0) for name in CORPORA)
        if not exact and verb not in paradigm_hits:
            continue
        certain = derive_certain(verb, entries)
        # Queueing a form that cannot be a present verb would put the editor to
        # work on a grammar error dressed up as a missing headword.
        if not certain["pattern"]:
            continue
        certain.pop("_root_disagreement")

        fields = dict(certain)
        fields.update(derive_proposals(verb, certain, entries, roots))

        root = roots.get(certain["root_key"])
        if exact:
            counts = ", ".join(
                f"{name} {freqs[name][verb]}"
                for name in CORPORA
                if freqs[name].get(verb)
            )
            note = f"attested {counts}"
        else:
            # Never seen as a 3rd singular, so name the form that was found —
            # the editor needs to see which part of the paradigm carries it.
            best = paradigm_hits[verb][0]
            note = (
                f"not attested as {verb}; found {best['form']}"
                f" ({best['label']}) {best['corpus']} {best['count']}"
            )
        if root and root.root_meaning:
            note += f"; {certain['root_key']} = {root.root_meaning}"
        # Why this verb is being suggested at all: the entries whose grammar
        # names it and has nowhere to point.
        note += "; named by " + ", ".join(
            f"{e['lemma_1']} ({e['pos']})" for e in entries
        )
        fields["comment"] = note

        queue[verb] = {
            name: value
            for name, value in fields.items()
            if name in QUEUE_FIELDS and value
        }
    return queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--load-gui",
        action="store_true",
        help="write the queue to gui2's X button file as well as the temp copy",
    )
    args = parser.parse_args()

    pr.yellow_title("missing pr verbs")
    pr.tic()

    pth = ProjectPaths()
    db = get_db_session(pth.dpd_db_path)
    output_dir: Path = pth.temp_dir / "missing_pr_verbs"

    pr.white("collecting referenced-but-missing verbs")
    wanted = collect_wanted_verbs(db)
    roots = load_roots(db)
    pr.summary("verbs wanted", str(len(wanted)))
    pr.summary("entries depending on them", str(sum(len(v) for v in wanted.values())))

    pr.white("loading corpus frequencies")
    freqs = load_corpus_freq(pth)
    for name in CORPORA:
        pr.summary(f"{name} distinct forms", str(len(freqs[name])))

    pr.white("searching other inflected forms")
    templates = load_templates(db)
    known_forms = load_known_forms(db)
    paradigm_hits: dict[str, list[dict[str, str]]] = {}
    for verb, entries in wanted.items():
        if any(freqs[name].get(verb, 0) for name in CORPORA):
            continue
        certain = derive_certain(verb, entries)
        if not certain["pattern"]:
            continue
        hits = search_paradigm(verb, certain, templates, freqs, known_forms)
        if hits:
            paradigm_hits[verb] = hits
    pr.summary("attested by another form", str(len(paradigm_hits)))

    write_tsv(
        [
            {
                "verb": verb,
                "form_found": hits[0]["form"],
                "label": hits[0]["label"],
                "corpus": hits[0]["corpus"],
                "count": hits[0]["count"],
                "other_forms": "|".join(
                    f"{h['form']}:{h['corpus']}:{h['count']}" for h in hits[1:6]
                ),
                "referring_lemmas": "|".join(e["lemma_1"] for e in wanted[verb]),
            }
            for verb, hits in sorted(paradigm_hits.items())
        ],
        output_dir / "paradigm_attested.tsv",
    )

    rows = build_report(wanted, freqs, roots)
    write_tsv(rows, output_dir / "wanted_verbs.tsv")

    attested = [r for r in rows if r["attested"]]
    pr.summary("attested by exact form", str(len(attested)))
    for name in CORPORA:
        pr.summary(f"  in {name}", str(sum(1 for r in rows if r[f"{name}_count"])))
    pr.summary("unattested", str(len(rows) - len(attested)))
    pr.summary("not a pr verb", str(sum(1 for r in rows if r["not_a_pr_verb"])))
    pr.summary("conflicting roots", str(sum(1 for r in rows if r["root_disagreement"])))

    already_seen = load_already_seen(db)
    pr.summary("previously shown and declined", str(len(already_seen)))
    queue = build_x_queue(wanted, freqs, roots, paradigm_hits, already_seen)
    for field in ("root_sign_add", "root_base_add", "construction_add"):
        pr.summary(f"  {field}", str(sum(1 for f in queue.values() if f.get(field))))

    queue_path = output_dir / "x_queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)
    pr.summary("x queue entries", str(len(queue)))

    if args.load_gui:
        gui_path = Gui2Paths().pass2_x_words_path
        with gui_path.open("w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4, ensure_ascii=False)
        pr.green(f"loaded {len(queue)} entries into gui2's X queue")
    else:
        pr.white(f"x queue written to {queue_path}")
        pr.white("pass --load-gui to load it into gui2")

    pr.toc()


if __name__ == "__main__":
    main()
