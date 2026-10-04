#!/usr/bin/env python3

"""Keep every derived form's grammar pointing at the right thing.

The rule: a derived form's `grammar` names the present-tense verb it comes from
when that verb is a headword, and the prefixes plus root when it is not.

Adding or removing a present verb changes what other entries should say. Add
`onandhati` and everything at that root should stop naming the root and name the
verb. Remove it and they go back to the root. This script finds those entries and
corrects them.

A causative or passive form follows the same rule, and must name a verb of its
own kind (caus, pass, caus pass) and exactly its own stem: *e with *e, *aya
with *aya, never one for the other. With no such verb it names its root
family, with the kind written in: "aor of caus of pa √dhaṃs".

Four groups come out of a run:

1. Clear cases, corrected and printed as before and after.
2. Entries naming a verb that is gone but that the corpus still attests. These
   are NOT corrected. The verb is probably worth re-adding, and repointing them
   at a root would throw that away.
3. Causative or passive forms no rule can settle: the verb is a draft, the
   entry and its finished verb disagree on the kind, or the root form needs
   two kinds or a negative written in. Listed for you to fix.
4. Entries where more than one verb fits. You pick one, skip it, or dismiss it.

It writes to dpd.db, like the other maintenance scripts here.

CLOSE gui2 BEFORE RUNNING — it writes to the same database.

Usage:
    uv run python db_tests/single/test_verb_grammar_sync.py
    uv run python db_tests/single/test_verb_grammar_sync.py --dry-run
"""

import argparse
import json
from dataclasses import dataclass, field

from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from scripts.fix.verb_finder import (
    FROM_A_VERB,
    build_pr_verb_index,
    lemma_clean,
    load_all_lemmas,
    load_cst_word_freq,
    merge_present_buckets,
    parse_grammar,
    parse_present_grammar,
    scan_derived_forms,
    scan_present_verbs,
    verb_kind,
)
from scripts.fix.verb_grammar_fixer import apply_changes
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# The two groups where the correct answer follows without judgement.
FIXABLE = (
    "would_change_to_root",
    "would_change_to_verb",
    "present_verb_to_root",
)

# What each group means, in the editor's terms.
DIRECTION = {
    "would_change_to_root": "no present verb exists — point at the root",
    "would_change_to_verb": "a present verb exists — point at the verb",
    "present_verb_to_root": "causative or passive naming a verb that is gone — point at the root",
}


@dataclass
class VerbGrammarSync:
    """Holds one run. Built in main(), never at import time."""

    pth: ProjectPaths = field(default_factory=ProjectPaths)
    exceptions: dict[str, str] = field(default_factory=dict)

    def load_exceptions(self) -> None:
        """Entries you have dismissed.

        Keyed by lemma with the grammar that was dismissed, so the dismissal
        lapses by itself if that entry's grammar later changes.
        """
        path = self.pth.verb_grammar_sync_exceptions_path
        if not path.exists():
            self.exceptions = {}
            return
        with path.open(encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            pr.red(f"{path.name} is not a mapping — ignoring it")
            loaded = {}
        self.exceptions = loaded

    def save_exceptions(self) -> None:
        path = self.pth.verb_grammar_sync_exceptions_path
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.exceptions, f, indent=2, ensure_ascii=False)


def pause(message: str) -> None:
    """Wait for the editor to read the stage above before moving on."""
    pr.white("")
    try:
        input(f"{message} — press Enter to continue: ")
    except EOFError:
        # Run from a pipe. Nothing is waiting to read it.
        pr.white("")


def grammar_naming(grammar: str, pos: str, verb: str) -> str:
    """The same grammar string, but naming `verb` instead of what it names now.

    Keeps the negation particle and any trailing text such as ", in comps".
    """
    # A grammar string never carries a homonym number, so "uḍḍeti 2.1" is
    # written as "uḍḍeti". Measured: 0 of the current grammar targets use one.
    ref = parse_grammar(grammar, pos)
    if ref is not None:
        na = "na " if ref.na else ""
        # The chosen verb carries its own kind, so "caus of" / "pass of" goes.
        return f"{ref.head} of {na}{lemma_clean(verb)}{ref.suffix}"
    # A present verb's "pr, caus of X" has its marker before " of ", which
    # parse_grammar does not read.
    present = parse_present_grammar(grammar)
    if present is not None:
        head, _target, suffix, negated = present
        na = "na " if negated else ""
        return f"{head} of {na}{lemma_clean(verb)}{suffix}"
    return ""


def root_choice(row: dict[str, str]) -> str | None:
    """The grammar naming the entry's root family, or None to write it by hand.

    A causative or passive root form must say its kind in the grammar: "aor of
    caus of pa √dhaṃs". Two kinds, or a negative, have no settled form. A
    present verb already says its kind before "of": "pr, caus of ...".
    """
    kind = (
        []
        if row["pos"] == "pr"
        else sorted(
            (verb_kind(row["verb_col"]) | verb_kind(row["grammar_current"]))
            & set(FROM_A_VERB)
        )
    )
    if len(kind) > 1 or (kind and " of na " in f" {row['grammar_current']} "):
        return None
    root = f"{kind[0]} of {row['family_root']}" if kind else row["family_root"]
    return grammar_naming(row["grammar_current"], row["pos"], root)


def gather(
    db: Session, pth: ProjectPaths
) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    """Recompute every derived form's correct grammar from the live database.

    Returns the clear corrections, and every bucket by name for the groups
    left to the editor.
    """
    pr_index, pr_lemma_map = build_pr_verb_index(db)
    cst_freq = load_cst_word_freq(pth)
    buckets = scan_derived_forms(
        db, pr_index, pr_lemma_map, cst_freq, load_all_lemmas(db)
    )
    # A causative or passive names a verb too, and the same rule governs it.
    merge_present_buckets(
        buckets, scan_present_verbs(db, pr_index, pr_lemma_map, cst_freq)
    )

    changes: list[dict[str, str]] = []
    for bucket in FIXABLE:
        for row in buckets[bucket]:
            if not row["grammar_proposed"]:
                continue
            if row["grammar_proposed"] == row["grammar_current"]:
                continue
            changes.append({**row, "bucket": bucket})
    changes.sort(key=lambda row: row["lemma_1"])

    return changes, buckets


def show_changes(changes: list[dict[str, str]]) -> None:
    """Print every correction as before and after, grouped by which way it goes."""
    if not changes:
        pr.green("no verbal form needs repointing")
        return

    for bucket in FIXABLE:
        rows = [row for row in changes if row["bucket"] == bucket]
        if not rows:
            continue
        pr.white("")
        pr.amber(f"{DIRECTION[bucket]} ({len(rows)})")
        pr.white("")
        for row in rows:
            pr.cyan(f"{row['lemma_1']} {row['pos']}")
            pr.red(f"    was  {row['grammar_current']}")
            pr.green(f"    now  {row['grammar_proposed']}")


def show_verb_in_cst(rows: list[dict[str, str]]) -> None:
    """Entries naming a verb that is gone but that the corpus still attests.

    Never corrected. Sending these to a root would discard the evidence that the
    verb belongs in the dictionary. Re-add the verb instead.
    """
    if not rows:
        return

    pr.white("")
    pr.amber(f"verb is missing but the texts have it — add the verb ({len(rows)})")
    pr.white("")
    for row in rows:
        pr.cyan(f"{row['lemma_1']} {row['pos']}")
        pr.white(f"    grammar now  {row['grammar_current']}")
        pr.white(f"    missing verb {row['candidates']} — {row['reason']}")


# Groups no rule can settle. Shown, never corrected.
MANUAL = {
    "draft_verb": "the verb is a draft — finish it, then run this again",
    "kind_mismatch": "the entry and its verb disagree on caus/pass — fix one of them",
    "root_by_hand": "no verb of this kind and stem — write the root form by hand",
}


def show_manual(bucket: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    pr.white("")
    pr.amber(f"{MANUAL[bucket]} ({len(rows)})")
    pr.white("")
    for row in rows:
        pr.cyan(f"{row['lemma_1']} {row['pos']}")
        pr.white(f"    grammar now  {row['grammar_current']}")
        pr.white(f"    why          {row['reason']}")
        if bucket == "root_by_hand":
            pr.white(f"    root         {row['candidates']}")


def still_pending(
    sync: VerbGrammarSync, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    """The entries you have not already dismissed."""
    return [
        row
        for row in rows
        if sync.exceptions.get(row["lemma_1"]) != row["grammar_current"]
    ]


def choose_for_ambiguous(
    sync: VerbGrammarSync, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Show each entry with more than one candidate verb and take your choice.

    Returns the corrections you picked.
    """
    pending = still_pending(sync, rows)
    if not pending:
        return []

    pr.white("")
    pr.amber(f"more than one verb fits — you decide ({len(pending)})")

    picked: list[dict[str, str]] = []
    asking = True
    for count, row in enumerate(pending, start=1):
        # The full lemma says which homonym is on offer; the grammar field
        # never carries a homonym number, so the cleaned form is what is written.
        shown = (row.get("candidates_full") or row["candidates"]).split("|")
        pr.white("")
        pr.amber(f"{count} of {len(pending)}")
        pr.cyan(f"{row['lemma_1']} {row['pos']}")
        pr.white(f"    grammar now  {row['grammar_current']}")
        pr.white(f"    root         {row['family_root']}  {row['root_key']}")
        pr.white(f"    why          {row['reason']}")
        for number, candidate in enumerate(shown, start=1):
            pr.white(f"    {number:>3}  {candidate}")
        pr.white("")

        if not asking:
            continue

        # input() cannot render markup, so rich prints the prompt and input()
        # reads the answer on the same line.
        print(
            "[bright_yellow](e)[/bright_yellow]xception, "
            "[bright_yellow](a)[/bright_yellow]dd, "
            "[bright_yellow](r)[/bright_yellow]oot family, "
            "[bright_yellow]Enter[/bright_yellow] to pass, "
            "[bright_yellow](q)[/bright_yellow]uit: ",
            end="",
        )
        try:
            choice = input().strip()
        except EOFError:
            # Run from a pipe. Keep listing the rest, stop asking.
            asking = False
            continue

        if choice == "e":
            sync.exceptions[row["lemma_1"]] = row["grammar_current"]
            sync.save_exceptions()
        elif choice == "a":
            chosen = ask_which_verb(shown)
            if not chosen:
                continue
            proposed = grammar_naming(row["grammar_current"], row["pos"], chosen)
            if not proposed:
                pr.red("    could not read that grammar — skipped")
                continue
            pr.green(f"    now  {proposed}")
            picked.append({**row, "grammar_proposed": proposed})
        elif choice == "r":
            # None of the candidates is the source, so point at the root family.
            proposed = root_choice(row)
            if proposed is None:
                pr.red("    two kinds or a negative — write this root form by hand")
                continue
            if not proposed or not row["family_root"]:
                pr.red("    no root family to point at — skipped")
                continue
            if proposed == row["grammar_current"]:
                # Already names the root. Remember the decision, or it comes
                # back as undecided on every run.
                sync.exceptions[row["lemma_1"]] = row["grammar_current"]
                sync.save_exceptions()
                pr.green("    already the root family — kept, won't ask again")
                continue
            pr.green(f"    now  {proposed}")
            picked.append({**row, "grammar_proposed": proposed})
        elif choice == "q":
            asking = False

    return picked


def ask_which_verb(candidates: list[str]) -> str:
    """Ask which numbered verb to use. Empty string means no choice made."""
    try:
        answer = input(f"    which verb? 1-{len(candidates)}: ").strip()
    except EOFError:
        return ""
    if not answer.isdigit():
        return ""
    number = int(answer)
    if not 1 <= number <= len(candidates):
        pr.red(f"    {number} is not on the list")
        return ""
    return candidates[number - 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="show what would change without writing to the database",
    )
    args = parser.parse_args()

    pr.tic()
    pr.yellow_title("keep verbal forms pointing at the right thing")

    sync = VerbGrammarSync()
    sync.load_exceptions()
    db = get_db_session(sync.pth.dpd_db_path)

    changes, buckets = gather(db, sync.pth)
    verb_in_cst = buckets["verb_in_cst"]
    ambiguous = buckets["ambiguous"]

    # Stage 1: the clear corrections. Shown before they are written, so they can
    # be read and any one of them changed by hand first.
    show_changes(changes)
    if changes:
        pause(f"{len(changes)} to repoint")

    written = 0
    if changes and not args.dry_run:
        written = apply_changes(db, changes)
        pause(f"{written} written")

    # Stage 2: the verb is gone but the texts still have it. Never corrected.
    show_verb_in_cst(verb_in_cst)
    if verb_in_cst:
        pause(f"{len(verb_in_cst)} need the verb adding")

    # Stage 3: the cases no rule can settle. Never corrected.
    for bucket in MANUAL:
        show_manual(bucket, buckets[bucket])
        if buckets[bucket]:
            pause(f"{len(buckets[bucket])} to fix by hand")

    # Stage 4: one at a time, your choice.
    undecided = len(still_pending(sync, ambiguous))
    picked = choose_for_ambiguous(sync, ambiguous)
    if picked and not args.dry_run:
        written += apply_changes(db, picked)

    pr.white("")
    if args.dry_run:
        pr.amber(f"dry run — {len(changes)} changes not written")
    else:
        pr.summary("changes written", str(written))
        if written:
            pr.green("database updated — run `just backup` next")

    pr.summary("repointed", str(len(changes) + len(picked)))
    pr.summary("needs verb added", str(len(verb_in_cst)))
    for bucket in MANUAL:
        pr.summary(bucket.replace("_", " "), str(len(buckets[bucket])))
    pr.summary("you decide", str(undecided - len(picked)))
    pr.toc()


if __name__ == "__main__":
    main()
