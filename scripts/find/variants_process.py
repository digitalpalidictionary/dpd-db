#!/usr/bin/env python3
"""Process unclassified variant field entries interactively.

Each entry is a pair: the source headword (the one with the variant field set)
plus one target headword (the variant looked up in the DB). If a variant string
matches 3 DB headwords, that produces 3 separate pairs.

Entries are pre-sorted:
  1. Synonym candidates — 2+ shared meanings (suggest s)
  2. Phonetic rule matches (suggest p)
  3. In DB with freq / meaning_1
  4. Not in DB (variant not a known headword)
  5. Zero freq, no meaning_1 (hardest — last)

The variant is opened in GoldenDict and copied to clipboard automatically.

Keys: (p)honetic  (t)ext  (s)ynonym  (d)elete  (pass)  (q)uit
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.goldendict_tools import open_in_goldendict
from tools.printer import printer as pr


# ── phonetic rules (same list as add_phonetic_variants.py) ──────────────────

PHONETIC_RULES: list[tuple[str, str]] = [
    ("e", "aya"),
    ("o", "ava"),
    ("ā", "a"),
    ("ī", "i"),
    ("ū", "u"),
    ("t", "ṭ"),
    ("d", "ḍ"),
    ("n", "ṇ"),
    ("n", "ṅ"),
    ("n", "ñ"),
    ("l", "ḷ"),
    ("ṃ", "ṅ"),
    ("ṃ", "n"),
    ("ṃ", "ṇ"),
    ("ṃ", "m"),
    ("ṃ", "ñ"),
    ("ūl", "ull"),
    ("ūḷ", "ull"),
    ("nh", "h"),
    ("ny", "ññ"),
    ("dy", "jj"),
    ("ty", "cc"),
    ("ṃy", "ññ"),
    ("nah", "nh"),
    ("nāh", "nh"),
    ("h", ""),
    ("y", ""),
    ("v", ""),
]

_FREQ_KEYS = ("CstFreq", "BjtFreq", "SyaFreq", "ScFreq")

_BUCKET_SYNONYM = 0
_BUCKET_PHONETIC = 1
_BUCKET_IN_DB = 2
_BUCKET_NO_DB = 3
_BUCKET_ZERO = 4


# ── helpers ──────────────────────────────────────────────────────────────────


def _split_field(value: str) -> set[str]:
    return {t.strip() for t in value.split(",") if t.strip()}


def _clean_meaning(text: str) -> frozenset[str]:
    text = re.sub(r"\(comm\).*$", "", text)
    text = re.sub(r" \(.*?\) | \(.*?\)|\(.*?\) ", "", text)
    return frozenset(m.strip() for m in text.split("; ") if m.strip())


def _matches_rule(a: str, b: str) -> str | None:
    for x, y in PHONETIC_RULES:
        if x and a.replace(x, y) == b:
            return f"{x}<->{y}"
        if y and a.replace(y, x) == b:
            return f"{x}<->{y}"
    return None


def _freq_total(hw: DpdHeadword) -> int:
    freq = hw.freq_data_unpack
    return sum(sum(val) for key in _FREQ_KEYS if isinstance(val := freq.get(key), list))


def _entry_label(hw: DpdHeadword) -> str:
    family_root = f" [magenta]{hw.family_root}" if hw.family_root else ""
    root_meaning = (
        f" [magenta]{hw.rt.root_meaning}" if hw.rt and hw.rt.root_meaning else ""
    )
    freq = _freq_total(hw)
    freq_str = f" [dim white]freq:{freq}" if freq else " [dim red]freq:0"
    return (
        f"[yellow]{hw.lemma_1} [blue]{hw.pos} "
        f"[green]{hw.meaning_combo} [white]({hw.degree_of_completion})"
        f"{family_root}{root_meaning}{freq_str}"
    )


def _format_fields(hw: DpdHeadword) -> str:
    syn = hw.synonym.split(", ") if hw.synonym else []
    var = hw.variant.split(", ") if hw.variant else []
    var_text = hw.var_text.split(", ") if hw.var_text else []
    phon = sorted(_split_field(hw.var_phonetic))
    return f"  syn:{syn}\n  var:{var}\n  var_text:{var_text}\n  var_phon:{phon}"


def _show_result(hw: DpdHeadword) -> None:
    print()
    print(f"[green]{hw.lemma_1}:")
    print(f"[green]{_format_fields(hw)}")


def _assign(hw: DpdHeadword, other: str, target: str) -> None:
    """Assign other to target field on hw, maintaining field consistency rules."""
    syn = _split_field(hw.synonym)
    var = _split_field(hw.variant)
    var_phon = _split_field(hw.var_phonetic)
    var_text = _split_field(hw.var_text)

    if target == "synonym":
        syn.add(other)
        var_phon.discard(other)
        if other not in var_text and other not in var_phon:
            var.discard(other)

    elif target == "var_phonetic":
        var_phon.add(other)
        var.add(other)
        syn.discard(other)

    elif target == "var_text":
        var_text.add(other)
        var.add(other)

    hw.synonym = ", ".join(sorted(syn))
    hw.variant = ", ".join(sorted(var))
    hw.var_phonetic = ", ".join(sorted(var_phon))
    hw.var_text = ", ".join(sorted(var_text))


def _assign_pair(
    hw: DpdHeadword,
    variant: str,
    target: DpdHeadword | None,
    field_name: str,
) -> None:
    """Assign bidirectionally: source gets variant, target gets hw.lemma_clean."""
    _assign(hw, variant, field_name)
    if target is not None:
        _assign(target, hw.lemma_clean, field_name)


def _remove_from_variant(hw: DpdHeadword, variant: str) -> None:
    parts = [
        v.strip() for v in hw.variant.split(",") if v.strip() and v.strip() != variant
    ]
    hw.variant = ", ".join(parts)


# ── entry dataclass ───────────────────────────────────────────────────────────


@dataclass
class VariantEntry:
    hw: DpdHeadword
    variant: str
    bucket: int
    rule: str = ""
    shared_meanings: list[str] = field(default_factory=list)
    target: DpdHeadword | None = None
    note: str = ""

    @property
    def suggested(self) -> str:
        if self.bucket == _BUCKET_SYNONYM:
            return "s"
        if self.bucket == _BUCKET_PHONETIC:
            return "p"
        return ""


# ── build and classify entries ────────────────────────────────────────────────


def build_entries(db) -> list[VariantEntry]:
    pr.green_tmr("loading headwords")
    all_words: list[DpdHeadword] = db.query(DpdHeadword).all()
    pr.yes(str(len(all_words)))

    by_lemma_clean: dict[str, list[DpdHeadword]] = {}
    for hw in all_words:
        by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)

    pr.green_tmr("classifying unclassified variants")
    source_words = [
        hw for hw in all_words if hw.variant and not hw.var_phonetic and not hw.var_text
    ]

    entries: list[VariantEntry] = []

    for hw in source_words:
        variants = [v.strip() for v in hw.variant.split(",") if v.strip()]
        src_meanings = _clean_meaning(hw.meaning_1) if hw.meaning_1 else frozenset()

        for variant in variants:
            targets = by_lemma_clean.get(variant, [])

            if not targets:
                entries.append(
                    VariantEntry(hw=hw, variant=variant, bucket=_BUCKET_NO_DB)
                )
                continue

            for t in targets:
                same_pos = hw.pos == t.pos
                rule = _matches_rule(hw.lemma_clean, variant) if same_pos else None

                shared: list[str] = []
                if same_pos and src_meanings and t.meaning_1:
                    shared = sorted(src_meanings & _clean_meaning(t.meaning_1))

                note = "" if same_pos else f"different pos: {hw.pos} / {t.pos}"

                if len(shared) >= 2:
                    entries.append(
                        VariantEntry(
                            hw=hw,
                            variant=variant,
                            bucket=_BUCKET_SYNONYM,
                            shared_meanings=shared,
                            target=t,
                        )
                    )
                elif rule:
                    entries.append(
                        VariantEntry(
                            hw=hw,
                            variant=variant,
                            bucket=_BUCKET_PHONETIC,
                            rule=rule,
                            target=t,
                        )
                    )
                else:
                    freq = _freq_total(t)
                    has_meaning = bool(t.meaning_1)
                    bucket = (
                        _BUCKET_ZERO
                        if (freq == 0 and not has_meaning)
                        else _BUCKET_IN_DB
                    )
                    entries.append(
                        VariantEntry(
                            hw=hw,
                            variant=variant,
                            bucket=bucket,
                            target=t,
                            note=note,
                        )
                    )

    entries.sort(key=lambda e: (e.bucket, e.hw.lemma_1))
    pr.yes(str(len(entries)))
    return entries


# ── main loop ────────────────────────────────────────────────────────────────

_BUCKET_LABELS = {
    _BUCKET_SYNONYM: "[magenta]synonym candidate",
    _BUCKET_PHONETIC: "[cyan]phonetic rule match",
    _BUCKET_IN_DB: "[white]in db",
    _BUCKET_NO_DB: "[yellow]not in db",
    _BUCKET_ZERO: "[red]zero freq / no meaning",
}

_BUCKET_COUNTS = {
    _BUCKET_SYNONYM: "synonym",
    _BUCKET_PHONETIC: "phonetic",
    _BUCKET_IN_DB: "in db",
    _BUCKET_NO_DB: "not in db",
    _BUCKET_ZERO: "zero freq",
}


def main() -> None:
    pr.tic()
    print(
        "[bright_yellow]variants processor — reclassify unclassified variant field entries"
    )

    db_path = Path("dpd.db")
    db = get_db_session(db_path)

    entries = build_entries(db)
    total = len(entries)

    counts = {b: sum(1 for e in entries if e.bucket == b) for b in range(5)}
    for b, label in _BUCKET_COUNTS.items():
        print(f"  [dim]{label}: {counts[b]}")

    print("\n[dim](p)honetic  (t)ext  (s)ynonym  (d)elete  (pass)  (q)uit")

    for counter, entry in enumerate(entries):
        hw = entry.hw
        variant = entry.variant
        target = entry.target

        current_vp = _split_field(hw.var_phonetic)
        current_vt = _split_field(hw.var_text)
        if variant in current_vp or variant in current_vt:
            continue

        open_in_goldendict(hw.lemma_clean)
        open_in_goldendict(variant)
        pyperclip.copy(variant)

        print("\n" + "-" * 70 + "\n")
        print(
            "[dim]synonym: different construction.  phonetic: same construction, different spelling.  textual: manuscript variant."
        )
        print()
        print(
            f"[white]{counter + 1} / {total}  "
            f"{_BUCKET_LABELS[entry.bucket]}"
            + (f"  [cyan]{entry.rule}" if entry.rule else "")
            + (
                f"  [magenta]shared: {', '.join(entry.shared_meanings[:3])}"
                if entry.shared_meanings
                else ""
            )
            + (f"  [dim red]{entry.note}" if entry.note else "")
        )
        print(_entry_label(hw))
        print(f"[cyan]{_format_fields(hw)}")

        if target is not None:
            print(_entry_label(target))
            print(f"[cyan]{_format_fields(target)}")
        else:
            print(f"[yellow]{variant} [dim](not found in db)")

        lemmas = [hw.lemma_1, target.lemma_1] if target else [hw.lemma_1]
        gui_string = db_search_string(lemmas, gui=True)
        print(f"\n[white]{gui_string}")
        print()

        suggested = entry.suggested
        prompt_str = (
            "[white](p)honetic, (t)ext, (s)ynonym, (d)elete, (pass), (q)uit"
            + (f"  [dim][{suggested}]" if suggested else "")
        )
        choice = Prompt.ask(prompt_str, default=suggested)

        if choice == "p":
            _assign_pair(hw, variant, target, "var_phonetic")
            _show_result(hw)
            if target:
                _show_result(target)
            db.commit()

        elif choice == "t":
            _assign_pair(hw, variant, target, "var_text")
            _show_result(hw)
            if target:
                _show_result(target)
            db.commit()

        elif choice == "s":
            _assign_pair(hw, variant, target, "synonym")
            _show_result(hw)
            if target:
                _show_result(target)
            db.commit()

        elif choice == "d":
            _remove_from_variant(hw, variant)
            _show_result(hw)
            if target:
                _show_result(target)
            db.commit()

        elif choice == "q":
            break

    db.commit()
    pr.toc()


if __name__ == "__main__":
    main()
