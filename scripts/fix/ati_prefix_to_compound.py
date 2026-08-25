"""One-off migration: record `ati-` prefix words as compounds, not root derivations.

`ati` is a prefix that attaches to an already-existing word to intensify it
(`ati` + `bahu` -> `atibahu` "too much"). DPD records such a word as a
compound: `compound_type = kammadhāraya`, `family_compound = ati <base>`,
`construction = ati + <base>`, and the root fields left empty — even when the
base word is itself root-derived. `atijiṇṇa`, `atibhutta`, `atidhāta`,
`atitaruṇa` and some two hundred others already follow that convention.

A minority were instead entered as root derivations, with the prefix folded
into the root family (`ati √gar`, `ati √lubh`, `ati ni √puṇ`). `atisīta` shows
the inconsistency in one place: it is already converted, while its sibling
`nātisīta` still carries `ati √sid`.

Candidates are headwords whose root family begins with `ati ` in a family where
no member is a verb form. A prefixed verb *is* a root derivation and keeps its
family, and so do its participles and gerunds — hence the family-level test
rather than a per-word one.

The migration runs through a TSV so every judgement call stays with the editor:

    uv run scripts/fix/ati_prefix_to_compound.py generate
    # edit scripts/fix/ati_prefix_to_compound.tsv — set `do` to y or n,
    # correct any `base`, then regenerate to refresh the proposals
    uv run scripts/fix/ati_prefix_to_compound.py apply --dry-run
    uv run scripts/fix/ati_prefix_to_compound.py apply

Generate preserves the `do` and `base` columns of an existing TSV and
recomputes the `new_*` columns from the edited base. Apply writes only rows
marked `do = y`, and refuses any row whose current database values no longer
match the TSV's `old_*` columns.

CLOSE gui2 BEFORE RUNNING — it writes to the same database.
"""

import argparse
import csv
import re
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound
from tools.paths import ProjectPaths
from tools.printer import printer as pr

TSV_PATH = Path("scripts/fix/ati_prefix_to_compound.tsv")

VERB_POS = {
    "pr",
    "aor",
    "fut",
    "imperf",
    "opt",
    "imp",
    "perf",
    "cond",
    "ger",
    "abs",
    "inf",
    "caus",
}

# In `dpd_headwords` column order (`db/models.py`), so the TSV reads the same
# way the table does.
CHANGED_FIELDS = [
    "pos",
    "grammar",
    "derived_from",
    "neg",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    "family_compound",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    "compound_type",
    "compound_construction",
    "pattern",
]

# One row per *field*, so the editor reads field / old / new side by side.
# The `do` and `base` cells are repeated on every row of a word's block; edit
# either one anywhere in the block.
COLUMNS = [
    "do",
    "base",
    "id",
    "lemma_1",
    "field",
    "old",
    "new",
    "note",
]

CASE_RE = re.compile(r"\b(nom|acc|instr|dat|abl|gen|loc|voc) (sg|pl) of ")

# `ati` + a vowel-initial base contracts to `acc-`; the doubled consonant of a
# gemination like `ati` + `ṭhāna` -> `atiṭṭhāna` is undone the same way.
CONSONANT_PAIRS = "kkh|ggh|cch|jjh|ṭṭh|ḍḍh|tth|ddh|pph|bbh|kk|gg|cc|jj|ṭṭ|ḍḍ|tt|dd|pp|bb|mm|nn|ññ|ṇṇ|ll|ss|yy|vv|ṃl|ṃp"


def bare_root(root_key: str) -> str:
    """`√kas 1` -> `√kas` — the homonym number is not part of the root."""
    return re.sub(r" \d+$", "", root_key.strip())


def lemma_clean(lemma_1: str) -> str:
    return re.sub(r" \d.*$", "", lemma_1)


def denegate(word: str) -> str:
    """`nātikisa` -> `atikisa`, `nāccodāta` -> `accodāta`."""
    if word.startswith("nā"):
        return "a" + word[2:]
    return word.removeprefix("na")


def negate(word: str) -> str:
    """`atikisa` -> `nātikisa`."""
    if word.startswith("a"):
        return "nā" + word[1:]
    return "na" + word


def candidate_bases(word: str) -> list[str]:
    """Strip the `ati`/`acc` prefix from an already-joined form, undoing sandhi."""
    out: list[str] = []
    if word.startswith("acc"):
        rest = word[3:]
        # `acc` + `u/i` coalesces to `o/e`; also allow the vowel to survive.
        out.append(rest)
        if rest.startswith("o"):
            out.append("u" + rest[1:])
        if rest.startswith("e"):
            out.append("i" + rest[1:])
        out.append("a" + rest)
        out.append("ā" + rest)
    elif word.startswith("ati"):
        rest = word[3:]
        out.append(rest)
        match = re.match(f"^({CONSONANT_PAIRS})", rest)
        if match:
            pair = match.group(1)
            # `ṭṭhāna` -> `ṭhāna`: drop the first half of the doubled cluster.
            out.append(rest[len(pair) // 2 :] if len(pair) % 2 == 0 else rest[1:])
    return out


def is_acc_form(word: str) -> bool:
    return denegate(word).startswith("acc")


def strip_ati(word: str, base: str) -> str:
    """`word` with a literal leading `ati` removed, undoing gemination.

    `atiṭṭhāna` minus `ati` is `ṭṭhāna`, not `ṭhāna` — the doubled consonant is
    sandhi from joining `ati` + `ṭhāna`, so a plain slice leaves a spurious
    extra letter. Falls back to the plain slice when the base does not confirm
    a doubled-consonant collapse (an irregular case-ending row like `atikāle`,
    where the ending itself is the reason the tail no longer matches `base`).
    """
    if not word.startswith("ati"):
        return word
    rest = word[3:]
    if base and rest.startswith(base):
        return rest
    match = re.match(f"^({CONSONANT_PAIRS})", rest)
    if match:
        pair = match.group(1)
        undone = rest[len(pair) // 2 :] if len(pair) % 2 == 0 else rest[1:]
        if not base or undone.startswith(base):
            return undone
    return rest


FINAL_VOWELS = "aāiīuū"


def vowel_variants(word: str) -> list[str]:
    """`kāl` -> `kāla`, `kālā`, `kāli`... — a case ending eats the stem vowel."""
    if not word:
        return []
    out = [word]
    stem = word[:-1] if word[-1] in FINAL_VOWELS else word
    out.extend(stem + vowel for vowel in FINAL_VOWELS)
    return out


def case_ending(hw: DpdHeadword) -> str:
    """The inflectional ending, taken from the last term of the old construction.

    It cannot be recovered by comparing strings: the accusative singular of
    `aticira` is written `cira + aṃ`, not `cira + ṃ`, because the ending
    replaces the stem-final vowel rather than following it.
    """
    first_line = hw.construction.split("\n")[0]
    if "+" not in first_line:
        return ""
    return first_line.rsplit("+", 1)[1].strip()


def derive_base(hw: DpdHeadword, form: str, by_clean: dict[str, DpdHeadword]) -> str:
    """Best guess at the base word this `ati-` word was built on."""
    candidates: list[str] = []

    df = denegate(hw.derived_from.strip())
    # For a case form `derived_from` may hold the inflected word itself
    # (`atikāle` -> `kāle`), which would be taken as the base. Ignore it.
    if df and "√" not in df and form != "case":
        df = df.removeprefix("ati ").strip()
        # `derived_from` may name the base (`cira`) or the joined form
        # (`aticira`) — the joined form has to be stripped again.
        candidates.extend(candidate_bases(df))
        candidates.append(df)

    bare = denegate(lemma_clean(hw.lemma_1))
    if form == "abstr":
        bare = bare.removesuffix(abstract_suffix(bare))
    elif form == "case":
        ending = case_ending(hw)
        if ending and bare.endswith(ending):
            bare = bare.removesuffix(ending)
    candidates.extend(candidate_bases(bare))

    for candidate in candidates:
        for variant in vowel_variants(candidate):
            base_hw = by_clean.get(variant)
            # A verb base means the old root analysis, not a compound member.
            if base_hw is not None and base_hw.pos not in VERB_POS:
                return variant
    return ""


def classify(hw: DpdHeadword) -> tuple[str, bool]:
    """Return the form (`plain`/`case`/`abstr`) and whether it is negated."""
    is_neg = hw.neg.strip() == "neg" or lemma_clean(hw.lemma_1).startswith("nā")
    if hw.pos == "ind" and CASE_RE.search(hw.grammar):
        return "case", is_neg
    if "abstr" in hw.grammar and abstract_suffix(denegate(lemma_clean(hw.lemma_1))):
        return "abstr", is_neg
    return "plain", is_neg


def insert_comp(grammar: str, base: str, is_neg: bool, new_pos: str = "") -> str:
    """Insert `comp` as the last qualifier and refresh a `from`/`pp of` clause.

    A compound is never "pp of <verb>" — that phrasing describes a genuine
    root derivation, and a pp/ptp used as a compound member is simply an
    adjective: `sumanasikata` ("adj, from manasikata, comp") is built on the pp
    `manasikata` and carries no trace of "pp" at all. `new_pos` carries that
    replacement in; passing it also drops the now-redundant "pp"/"ptp" that
    would otherwise survive as a bare tail token. A case-form reference
    ("acc sg of atisīta") is not this — it names the word's own inflected
    source and is left alone.
    """
    parts = [p.strip() for p in grammar.split(",") if p.strip()]
    if not parts:
        return "comp"
    tail_at = len(parts)
    for i, part in enumerate(parts):
        if part.startswith("from ") or " of " in part:
            tail_at = i
            break
    head = parts[:tail_at]
    tail = parts[tail_at:]
    from_clause = f"from na {base}" if is_neg else f"from {base}"
    if tail and CASE_RE.search(tail[0]):
        pass
    elif base:
        # Every compound names its base, whether the old grammar already had
        # a "from X" clause, an "of X" clause (a genuine root/verb
        # derivation, or a pp/ptp relabelled adj), or no clause at all.
        tail = [from_clause]
    elif tail and not tail[0].startswith("from "):
        # No known base to substitute: strip an "of X" clause down to its
        # bare pos word rather than assert a base that was never found.
        tail[0] = tail[0].split(" of ", 1)[0]
    if new_pos:
        head = [new_pos] + head[1:]
    if "comp" not in head:
        head.append("comp")
    return ", ".join(head + tail)


def abstract_suffix(word: str) -> str:
    for suffix in ("tta", "tā"):
        if word.endswith(suffix):
            return suffix
    return ""


class Proposal:
    """The new field values for one headword, plus the notes the editor needs."""

    def __init__(
        self,
        hw: DpdHeadword,
        base: str,
        base_ok: bool,
        compound_token: str,
        token_known: bool,
        base_root: str = "",
        word_root: str = "",
        homonyms: int = 1,
    ) -> None:
        self.form, self.is_neg = classify(hw)
        self.base = base
        self.base_ok = base_ok
        self.blocked = False
        self.review: list[str] = []

        word = lemma_clean(hw.lemma_1)
        bare = denegate(word)
        acc = is_acc_form(word)
        prefix_written = "ati > aty > acc" if acc else "ati"
        inner = ("acc" if acc else "ati") + base

        if not base:
            self.review.append("no base found")
        elif not base_ok:
            self.review.append("base is not a headword")
        if not token_known:
            self.review.append(
                f"compound family not in family_compound table"
                f" ({homonyms} homonyms of the base)"
            )
        if acc:
            self.review.append("check phonetic at the acc- junction")
        if base_root and word_root and base_root != word_root:
            self.review.append(
                f"base is built on {base_root}, this word on {word_root}"
            )

        # A pp/ptp used as a compound member is just an adjective — the same
        # relabelling `sumanasikata` already carries for its pp base.
        new_pos = "adj" if hw.pos in ("pp", "ptp") else ""

        # `pattern` ends with the same pos token as `pos` itself
        # (`sumanasikata`: pos `adj`, pattern `a adj`) and must track it.
        pattern_head, _, pattern_pos = hw.pattern.rpartition(" ")
        new_pattern = (
            f"{pattern_head} {new_pos}"
            if new_pos and pattern_pos in ("pp", "ptp")
            else hw.pattern
        )

        self.fields: dict[str, str] = {
            "pos": new_pos or hw.pos,
            "pattern": new_pattern,
            "neg": "neg" if self.is_neg else hw.neg,
            "root_key": "",
            "root_sign": "",
            "root_base": "",
            "family_root": "",
            "family_compound": f"ati {compound_token}" if compound_token else "",
            "derivative": "",
            "suffix": "",
            "phonetic": "ti > ty > cc" if acc else "",
            # A frozen case form (an indeclinable) is a kammadhāraya that has
            # also become an abyayībhāva; any other shape is plain kammadhāraya.
            "compound_type": (
                "kammadhāraya > abyayībhāva" if self.form == "case" else "kammadhāraya"
            ),
        }

        na = "na + " if self.is_neg else ""

        # Always "na + <surface>" or "ati + <surface>", one whole word on the
        # right — never decomposed into base + ending/suffix. For a negated
        # word the surface is the positive counterpart as spelled (sandhi and
        # all: `nāccogāḷhaṃ` -> `na + accogāḷhaṃ`); for a plain word it is the
        # lemma with a literal leading `ati` stripped, or left whole when the
        # prefix survives only as sandhi (`acc-`, `aty-`).
        if self.is_neg:
            self.fields["compound_construction"] = f"na + {bare}"
        else:
            self.fields["compound_construction"] = f"ati + {strip_ati(word, base)}"

        self.blocked = not base
        if self.form == "case":
            ending = case_ending(hw)
            if not ending:
                self.review.append("case ending not recoverable from construction")
                self.blocked = True
            outer = negate(inner) if self.is_neg else inner
            self.fields["derived_from"] = inner
            self.fields["construction"] = (
                f"{na}{prefix_written} + {base} + {ending}\n{outer} + {ending}"
            )
        elif self.form == "abstr":
            sfx = abstract_suffix(bare)
            if not sfx:
                self.review.append("abstract suffix not recognised")
            stem = bare.removesuffix(sfx)
            outer = negate(stem) if self.is_neg else stem
            self.fields["derived_from"] = stem if self.is_neg else base
            self.fields["derivative"] = "taddhita"
            self.fields["suffix"] = sfx
            self.fields["construction"] = (
                f"{na}{prefix_written} + {base} + {sfx}\n{outer} + {sfx}"
            )
        else:
            self.fields["derived_from"] = base
            self.fields["construction"] = f"{na}{prefix_written} + {base}"

        self.fields["grammar"] = insert_comp(
            hw.grammar, self.fields["derived_from"], self.is_neg, new_pos
        )


def select_candidates(db: Session) -> list[DpdHeadword]:
    """Headwords in an `ati` root family that contains no verb form."""
    in_ati = (
        db.query(DpdHeadword).filter(DpdHeadword.family_root.startswith("ati ")).all()
    )
    verb_families = {hw.family_root for hw in in_ati if hw.pos in VERB_POS}
    return sorted(
        (hw for hw in in_ati if hw.family_root not in verb_families),
        key=lambda hw: (hw.family_root, hw.lemma_1),
    )


def compound_token(base_hw: DpdHeadword | None, base: str) -> str:
    """The token that represents the base word in a compound family."""
    if base_hw is not None and base_hw.family_compound.strip():
        return base_hw.family_compound.strip()
    return base


def read_existing() -> dict[int, tuple[str, str, bool]]:
    """Carry the editor's `do` and `base` edits across a regenerate.

    The third value flags a row that was previously blocked (its only line
    was the `(none)` placeholder) — used to tell "the editor declined this on
    purpose" from "this was auto-set to n because there was nothing to
    propose yet", so fixing `base` for a blocked row un-blocks it instead of
    silently staying declined.
    """
    if not TSV_PATH.exists():
        return {}
    overrides: dict[int, tuple[str, str, bool]] = {}
    with open(TSV_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            hw_id = int(row["id"])
            # A blocked or already-matching word writes exactly one row, with
            # field == "(none)"; a word with real changes writes one row per
            # changed field, none of them "(none)". The two never mix for one
            # id, so the last row read still carries the right flag.
            overrides[hw_id] = (row["do"], row["base"], row["field"] == "(none)")
    return overrides


def build_rows(db: Session) -> list[dict[str, str]]:
    headwords = select_candidates(db)
    by_clean: dict[str, DpdHeadword] = {}
    homonym_count: dict[str, int] = {}
    for hw in db.query(DpdHeadword).all():
        by_clean.setdefault(hw.lemma_clean, hw)
        homonym_count[hw.lemma_clean] = homonym_count.get(hw.lemma_clean, 0) + 1
    families = {f.compound_family for f in db.query(FamilyCompound).all()}
    overrides = read_existing()

    rows: list[dict[str, str]] = []
    for hw in headwords:
        do, base, was_blocked = overrides.get(hw.id, ("y", "", False))
        if not base:
            base = derive_base(hw, classify(hw)[0], by_clean)
        base_hw = by_clean.get(base)
        token = compound_token(base_hw, base)
        proposal = Proposal(
            hw,
            base,
            base_hw is not None,
            token,
            token in families,
            bare_root(base_hw.root_key) if base_hw is not None else "",
            bare_root(hw.root_key),
            homonym_count.get(base, 0),
        )

        note = "; ".join(proposal.review)
        if was_blocked and do == "n" and not proposal.blocked:
            # The editor fixed `base` for a row that was blocked (no other
            # reason to decline it was recorded) — it now has a real
            # proposal, so don't leave it silently stuck on "n".
            do = "y"
        # Every field, every word — an unchanged field still has to be visible
        # for the editor to judge the row.
        changed = [
            field
            for field in CHANGED_FIELDS
            if not proposal.blocked and getattr(hw, field) != proposal.fields[field]
        ]
        # A blocked word, or one every field of which already matches the
        # proposal, still needs a row so it appears in the TSV at all.
        shown_fields = changed or ["(none)"]
        for n, field in enumerate(shown_fields):
            rows.append(
                {
                    "do": do if not proposal.blocked else "n",
                    "base": base,
                    "id": str(hw.id),
                    "lemma_1": hw.lemma_1,
                    "field": field,
                    "old": (
                        ""
                        if field == "(none)"
                        else getattr(hw, field).replace("\n", "\\n")
                    ),
                    "new": (
                        ""
                        if field == "(none)"
                        else proposal.fields[field].replace("\n", "\\n")
                    ),
                    "note": note if n == 0 else "",
                }
            )

    return rows


def generate(db_path: Path) -> None:
    db = get_db_session(db_path)
    rows = build_rows(db)
    with open(TSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        # A blank line between words; `csv.DictReader` skips empty rows.
        previous = ""
        for row in rows:
            if previous and row["id"] != previous:
                f.write("\n")
            writer.writerow(row)
            previous = row["id"]

    seen: set[str] = set()
    heads: list[dict[str, str]] = []
    for row in rows:
        if row["id"] not in seen:
            seen.add(row["id"])
            heads.append(row)
    pr.green_title(f"wrote {TSV_PATH}")
    pr.summary("words", str(len(heads)))
    pr.summary("blocked (do=n)", str(sum(1 for r in heads if r["do"] != "y")))

    flagged = [r for r in heads if r["note"]]
    if flagged:
        pr.cyan(f"{len(flagged)} words need a look:")
        for row in flagged:
            pr.white(f"  {row['lemma_1']:<20} {row['note']}")


def apply(db_path: Path, dry_run: bool) -> None:
    if not TSV_PATH.exists():
        pr.red(f"{TSV_PATH} not found — run `generate` first")
        return

    db = get_db_session(db_path)
    with open(TSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    blocks: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        blocks.setdefault(int(row["id"]), []).append(row)

    applied = skipped = declined = stale = 0
    for hw_id, block in blocks.items():
        if not any(r["do"].strip().lower() == "y" for r in block):
            declined += 1
            continue
        hw = db.get(DpdHeadword, hw_id)
        if hw is None:
            pr.red(f"  id {hw_id} not in the database")
            skipped += 1
            continue

        edits = [r for r in block if r["field"] in CHANGED_FIELDS]
        drifted = [
            r["field"]
            for r in edits
            if getattr(hw, r["field"]).replace("\n", "\\n") != r["old"]
        ]
        if drifted:
            pr.amber(f"  {hw.lemma_1}: changed since generate ({', '.join(drifted)})")
            stale += 1
            continue

        pr.white(hw.lemma_1)
        for row in edits:
            new = row["new"].replace("\\n", "\n")
            pr.white(f"    {row['field']}: {getattr(hw, row['field'])!r} -> {new!r}")
            if not dry_run:
                setattr(hw, row["field"], new)
        applied += 1

    if dry_run:
        db.rollback()
        pr.amber("dry run — nothing written")
    else:
        db.commit()
        pr.green("committed — run `just backup` next")

    pr.summary("applied", str(applied))
    pr.summary("declined (do != y)", str(declined))
    pr.summary("stale (db moved on)", str(stale))
    pr.summary("skipped (missing id)", str(skipped))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("generate", help="write the proposal TSV")
    apply_parser = sub.add_parser("apply", help="write the approved rows to the db")
    apply_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="report what would change without writing to the database",
    )
    args = parser.parse_args()

    pth = ProjectPaths()
    if args.mode == "generate":
        generate(pth.dpd_db_path)
    else:
        apply(pth.dpd_db_path, args.dry_run)


if __name__ == "__main__":
    main()
