"""Turn the probe output into the tables of results.md.

    make_tables.py --laptop <jsonl> --server <jsonl> --readings <jsonl> --out <md>

The server and readings files may be missing or empty: those parts print n/a.
Lines that start with `KEY ` are the numbers the fixture test compares.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mem_stats import point_delta, read_jsonl, reading, summarize

BASELINE_MB = 1066.0
USERS = (8, 16)
COMPONENTS = [
    "db_manager",
    "initialize_db",
    "corpus",
    "inflections_lists",
    "relationship_detector",
    "wordfinder",
    "ai_manager",
    "bold_search",
    "spellchecker",
]
PHASES = [
    "now",
    "plus15s",
    "db_loaded",
    "warmup_done",
    "one_book",
    "reload1",
    "reload2",
    "reload3",
]
# A judgement from reading the code, not a measurement (spec section 5).
CLASSES: dict[str, tuple[str, str]] = {
    "bare": ("read-only", "interpreter base; one copy per process (gui2/main.py:1-24)"),
    "imports": ("read-only", "module code; one copy per process (gui2/main.py:12-24)"),
    "db_manager": (
        "per-user",
        "holds one session and the own-edits overlay (gui2/database_manager.py:47-83)",
    ),
    "initialize_db": (
        "per-user",
        "db-derived sets, but all_lemma_1 adds the user's own additions; "
        "most of it is identical (gui2/database_manager.py:215-222)",
    ),
    "corpus": (
        "read-only",
        "full headword load, same for every user (gui2/database_manager.py:181-204)",
    ),
    "inflections_lists": (
        "read-only",
        "derived from the corpus only (gui2/database_manager.py:346-364)",
    ),
    "relationship_detector": (
        "read-only",
        "built from the corpus only (gui2/database_manager.py:781-799)",
    ),
    "wordfinder": (
        "read-only",
        "one shared JSON file (tools/wordfinder_manager.py:35,51-53)",
    ),
    "ai_manager": (
        "read-only",
        "providers from shared config; only small timing fields change "
        "(tools/ai_manager.py:58-107)",
    ),
    "bold_search": (
        "per-user",
        "holds one db session (tools/bold_definitions_search.py:16-19)",
    ),
    "spellchecker": (
        "per-user",
        "loads the user's own dictionary file (tools/spelling.py:49-55)",
    ),
    "book": (
        "read-only",
        "SC indexes are module-level (gui2/books.py:42-69); the CST list is "
        "per controller (gui2/pass1_auto_controller.py:290), not split here",
    ),
}
ROLE_JUDGEMENT = {
    "B": ("low", "low"),
    "C": ("medium", "medium"),
    "D": ("medium", "medium"),
    "E": ("high", "high"),
    "F": ("medium", "low"),
}


def ok_rows(rows: list[dict[str, Any]], point: str) -> list[dict[str, Any]]:
    return [
        r
        for r in rows
        if r.get("point") == point
        and r.get("outcome") == "ok"
        and r.get("run_id") != "warmup"
    ]


def deltas(
    rows: list[dict[str, Any]], label: str, field: str = "rss_mb"
) -> list[float]:
    found = [point_delta(r, label, field) for r in rows]
    return [v for v in found if v is not None]


def med(values: list[float]) -> float | None:
    return summarize(values)["median"] if values else None


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}"


def span(values: list[float]) -> str:
    if not values:
        return "n/a"
    s = summarize(values)
    mark = " ⚑" if s["flag"] else ""
    return f"{s['median']:.1f} ({s['min']:.1f}–{s['max']:.1f}){mark}"


def final_rss(rows: list[dict[str, Any]]) -> list[float]:
    return [float(r["readings"][-1]["rss_mb"]) for r in rows]


def growth_after_imports(row: dict[str, Any]) -> float | None:
    """Final RSS of a cumulative run minus its `imports` reading."""
    base = reading(row, "imports")
    if base is None:
        return None
    return float(row["readings"][-1]["rss_mb"]) - float(base["rss_mb"])


def build(
    laptop: list[dict[str, Any]],
    server: list[dict[str, Any]],
    unit: list[dict[str, Any]],
) -> tuple[list[str], dict[str, str]]:
    keys: dict[str, str] = {}
    out: list[str] = []
    stair = ok_rows(laptop, "staircase")
    sstair = ok_rows(server, "staircase")

    # ---- component table
    out += ["## Component table (MB, laptop)", ""]
    out += [
        "| Point | Isolated delta, median (min–max) | Staircase delta | PSS delta | Class |",
        "|---|---|---|---|---|",
    ]
    iso_med: dict[str, float] = {}
    names = ["bare", "imports", *COMPONENTS]
    for name in names:
        rows = ok_rows(laptop, name)
        values = deltas(rows, name)
        pss = deltas(rows, name, "pss_mb")
        stair_value = med(deltas(stair, name))
        cls, why = CLASSES[name]
        if values:
            iso_med[name] = summarize(values)["median"]
            keys[f"iso_{name}"] = fmt(iso_med[name])
            keys[f"flag_{name}"] = "yes" if summarize(values)["flag"] else "no"
        out.append(
            f"| {name} | {span(values)} | {fmt(stair_value)} | {fmt(med(pss))} | {cls} — {why} |"
        )
    book_names: list[str] = []
    for row in laptop:
        if row.get("point") == "book" and row.get("book") not in book_names:
            book_names.append(row["book"])
    book_med: dict[str, float] = {}
    for name in book_names:
        rows = [r for r in ok_rows(laptop, "book") if r.get("book") == name]
        values = deltas(rows, f"book:{name}")
        pss = deltas(rows, f"book:{name}", "pss_mb")
        if values:
            book_med[name] = summarize(values)["median"]
        cls, why = CLASSES["book"]
        out.append(
            f"| book:{name} | {span(values)} | n/a | {fmt(med(pss))} | {cls} — {why} |"
        )
    cumulative = ok_rows(laptop, "books_cumulative")
    grown = [growth_after_imports(r) for r in cumulative]
    four_books = med([v for v in grown if v is not None])
    one_book = med(list(book_med.values()))
    keys["one_book"] = fmt(one_book)
    keys["four_books"] = fmt(four_books)

    # ---- reconciliation
    lap_total = med(final_rss(stair))
    srv_total = med(final_rss(sstair))
    sum_iso = sum(iso_med.get(n, 0.0) for n in names) if iso_med else None
    gap = lap_total - sum_iso if lap_total is not None and sum_iso is not None else None
    warm_rss = max(
        (r["vm_rss_mb"] for r in unit if r.get("label") == "warmup_done"), default=None
    )
    one_book_rss = max(
        (r["vm_rss_mb"] for r in unit if r.get("label") == "one_book"), default=None
    )
    remainder_raw = warm_rss - srv_total if warm_rss and srv_total is not None else None
    # The app warm-up never builds the inflection lists (gui2/main.py:558-583);
    # Pass1 builds them on first use (gui2/pass1_auto_controller.py:120). The
    # staircase builds them, so take them out before comparing with the app.
    infl_stair = med(deltas(stair, "inflections_lists"))
    remainder = (
        warm_rss - (srv_total - infl_stair)
        if warm_rss is not None and srv_total is not None and infl_stair is not None
        else None
    )
    book_step = one_book_rss - warm_rss if one_book_rss and warm_rss else None
    four_server = (
        book_step + (four_books - one_book)
        if book_step is not None and four_books is not None and one_book is not None
        else None
    )
    keys["unbuilt_remainder_raw"] = fmt(remainder_raw)
    keys["server_book_step"] = fmt(book_step)
    keys["four_books_server"] = fmt(four_server)
    keys["laptop_staircase_total"] = fmt(lap_total)
    keys["sum_isolated"] = fmt(sum_iso)
    keys["interaction_gap"] = fmt(gap)
    keys["server_staircase_total"] = fmt(srv_total)
    keys["server_warm_rss"] = fmt(warm_rss)
    keys["unbuilt_remainder"] = fmt(remainder)
    out += ["", "## Reconciliation (MB)", ""]
    out += [
        "| Row | Value | How |",
        "|---|---|---|",
        f"| laptop staircase total | {fmt(lap_total)} | median final RSS of the staircase runs |",
        f"| sum of isolated deltas | {fmt(sum_iso)} | `bare` + `imports` + 9 components |",
        f"| interaction gap | {fmt(gap)} | staircase total − sum of isolated deltas |",
        f"| server staircase total | {fmt(srv_total)} | median final RSS, server runs |",
        f"| server warm RSS | {fmt(warm_rss)} | `warmup_done` reading, before any book |",
        f"| unbuilt remainder, raw | {fmt(remainder_raw)} | server warm RSS − server staircase total |",
        f"| inflection lists, staircase delta | {fmt(infl_stair)} | built by the probe, not by the app warm-up |",
        f"| unbuilt remainder | {fmt(remainder)} | server warm RSS − (server staircase total − inflection lists) |",
    ]
    over = remainder is not None and warm_rss and remainder > 0.2 * warm_rss
    keys["unbuilt_over_20pct"] = "yes" if over else "no"
    if over:
        out += [
            "",
            "The unbuilt remainder is more than 20 % of the server warm RSS. "
            "Follow-up proposed: one `tracemalloc` run on the largest piece.",
        ]

    # ---- projection
    shared = sum(iso_med.get(n, 0.0) for n in names if CLASSES[n][0] == "read-only")
    per_user = sum(
        iso_med.get(n, 0.0) for n in COMPONENTS if CLASSES[n][0] == "per-user"
    )
    keys["shared_read_only"] = fmt(shared if iso_med else None)
    keys["per_user"] = fmt(per_user if iso_med else None)
    out += ["", "## Projection (MB; baseline 1066 MB with no gui2 running)", ""]
    out += ["| Users | Books each | Today | Option E |", "|---|---|---|---|"]
    infl_iso = iso_med.get("inflections_lists", 0.0)
    shared_at_warm = shared - infl_iso
    for n in USERS:
        for label, books, step in (
            ("1", one_book, book_step),
            ("4", four_books, four_server),
        ):
            today = e_total = None
            if warm_rss is not None and step is not None:
                today = BASELINE_MB + n * (warm_rss + step)
            if remainder is not None and books is not None and iso_med:
                e_total = (
                    BASELINE_MB
                    + shared_at_warm
                    + infl_iso
                    + books
                    + n * (per_user + remainder)
                )
            keys[f"today_{n}_{label}"] = fmt(today)
            keys[f"e_{n}_{label}"] = fmt(e_total)
            out.append(f"| {n} | {label} | {fmt(today)} | {fmt(e_total)} |")
    out += [
        "",
        "Today: warm RSS plus the measured server step for opening books "
        "(the first book also builds the inflection lists). Option E: the "
        "read-only rows, the inflection lists and the books once, plus the "
        "per-user rows and the unbuilt remainder for each user. Each figure "
        "is an upper bound.",
        "",
    ]

    # ---- ranking
    def total(names_: list[str]) -> float | None:
        return (
            sum(iso_med[x] for x in names_)
            if all(x in iso_med for x in names_)
            else None
        )

    figures = {
        "B": total(
            ["wordfinder", "ai_manager", "bold_search", "relationship_detector"]
        ),
        "C": total(["inflections_lists"]),
        "D": total(["wordfinder"]),
    }
    out += ["## Ranking of B to F (MB; effort and risk are judgement)", ""]
    out += [
        "| Option | Saved per instance | At 8 users | At 16 users | Effort | Risk | Source |",
        "|---|---|---|---|---|---|---|",
    ]
    sources = {
        "B": "wordfinder + ai_manager + bold_search + relationship_detector",
        "C": "inflections_lists",
        "D": "wordfinder",
    }
    for opt, value in figures.items():
        keys[f"opt_{opt}"] = fmt(value)
        e, r = ROLE_JUDGEMENT[opt]
        at = [None if value is None else value * n for n in USERS]
        out.append(
            f"| {opt} | {fmt(value)} | {fmt(at[0])} | {fmt(at[1])} | {e} | {r} | {sources[opt]} |"
        )
    saved_e = [shared * (n - 1) if iso_med else None for n in USERS]
    keys["opt_E_8"], keys["opt_E_16"] = fmt(saved_e[0]), fmt(saved_e[1])
    e, r = ROLE_JUDGEMENT["E"]
    out.append(
        f"| E | n/a | {fmt(saved_e[0])} | {fmt(saved_e[1])} | {e} | {r} | read-only rows × (N − 1) |"
    )
    e, r = ROLE_JUDGEMENT["F"]
    out.append(
        f"| F | 0 | K × per-instance | K × per-instance | {e} | {r} | K comes from the owner |"
    )

    # ---- server phases
    out += ["", "## Server readings (MB)", ""]
    out += ["| Label | VmRSS | VmHWM | VmSwap | PSS | Private | Threads | Seconds up |"]
    out += ["|---|---|---|---|---|---|---|---|"]
    by_label: dict[str, dict[str, Any]] = {}
    for item in unit:
        if "label" in item and "vm_rss_mb" in item:
            old = by_label.get(item["label"])
            if old is None or item["vm_rss_mb"] > old["vm_rss_mb"]:
                by_label[item["label"]] = item
    for label in PHASES:
        i = by_label.get(label)
        if i:
            out.append(
                f"| {label} | {i['vm_rss_mb']} | {i['vm_hwm_mb']} | {i['vm_swap_mb']} | "
                f"{i['smaps_pss_mb']} | {i['smaps_private_mb']} | {i['threads']} | {i['elapsed_s']} |"
            )
    steps = [
        ("db load", "db_loaded", "plus15s"),
        ("tab views and managers", "warmup_done", "db_loaded"),
        ("one book", "one_book", "warmup_done"),
        ("reload 1", "reload1", "one_book"),
        ("reload 2", "reload2", "reload1"),
        ("reload 3", "reload3", "reload2"),
    ]
    out += ["", "| Step | RSS change |", "|---|---|"]
    for name, after, before in steps:
        if after in by_label and before in by_label:
            diff = by_label[after]["vm_rss_mb"] - by_label[before]["vm_rss_mb"]
            keys[f"step_{after}"] = fmt(diff)
            note = (
                " (leak: more than 100 MB)"
                if after.startswith("reload") and diff > 100
                else ""
            )
            out.append(f"| {name} | {diff:.1f}{note} |")

    # ---- laptop versus server
    out += ["", "## Laptop versus server", ""]
    out += [
        f"- Staircase total: laptop {fmt(lap_total)} MB, server {fmt(srv_total)} MB.",
        f"- Database size: laptop {meta_of(stair, 'db_size')}, server {meta_of(sstair, 'db_size')} bytes.",
        f"- AI providers built: laptop {meta_of(stair, 'providers_built')}, server {meta_of(sstair, 'providers_built')}.",
    ]
    return out, keys


def meta_of(rows: list[dict[str, Any]], key: str) -> Any:
    return rows[0]["meta"].get(key) if rows else "n/a"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--laptop", required=True)
    parser.add_argument("--server", default="")
    parser.add_argument("--readings", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    laptop = read_jsonl(Path(args.laptop))
    server = read_jsonl(Path(args.server)) if args.server else []
    unit = read_jsonl(Path(args.readings)) if args.readings else []
    lines, keys = build(laptop, server, unit)
    lines += ["", "## Key numbers", ""] + [
        f"KEY {k}={v}" for k, v in sorted(keys.items())
    ]
    text = "\n".join(lines) + "\n"
    Path(args.out).write_text(text, encoding="utf-8")
    sys.stdout.write(json.dumps({"written": args.out, "keys": len(keys)}) + "\n")


if __name__ == "__main__":
    main()
