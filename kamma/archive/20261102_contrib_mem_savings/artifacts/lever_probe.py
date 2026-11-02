"""Measure the memory saved by each lever, one variant per fresh process.

See spec.md and plan.md in the parent folder. Run from the repo root.

    --variant <name>   run one variant in this process (the child)
    --all              the driver: every variant, three fresh processes each
    --report <jsonl>   turn the rows into the lever table
    --selftest         check the probe itself
"""

import argparse
import ctypes
import gc
import importlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import psutil

MB = 1024 * 1024
DRIVER_TIMEOUT_S = 40 * 60
CHILD_TIMEOUT_S = 600
SPREAD_LIMIT = 0.10
WHOLE_BUILD = ("contributor_", "warm_")
DEFAULT_COLUMNS_MD = "kamma/threads/20261102_contrib_mem_savings/artifacts/columns.md"
BASELINE_MB = 1066.0
SERVER_WARM_MB = 1165.9
SERVER_ONE_BOOK_MB = 1485.0

CONTRIBUTOR_TODAY = [
    "db_manager",
    "initialize_db",
    "corpus_full",
    "sets_today",
    "wordfinder_today",
    "ai_manager",
    "bold_search",
    "detector",
    "spellchecker",
]
CONTRIBUTOR_LEVERS = [
    "db_manager",
    "initialize_db",
    "corpus_slim",
    "sets_direct",
    "wordfinder_interned",
    "ai_manager",
    "bold_search",
    "detector",
    "spellchecker",
]


def without(steps: list[str], *names: str) -> list[str]:
    return [s for s in steps if s not in names]


def swap(steps: list[str], old: str, new: str) -> list[str]:
    return [new if s == old else s for s in steps]


# variant name -> steps after `bare` and `imports`; a reading follows each step
VARIANTS: dict[str, list[str]] = {
    "corpus_full": ["db_manager", "corpus_full"],
    "corpus_slim": ["db_manager", "corpus_slim"],
    "corpus_slim_nofreq": ["db_manager", "corpus_slim_nofreq"],
    "sets_today": ["db_manager", "corpus_full", "sets_today"],
    "sets_today_slim": ["db_manager", "corpus_slim", "sets_today"],
    "sets_direct": ["db_manager", "sets_direct"],
    "sets_direct_both": ["db_manager", "sets_direct_both"],
    "detector_full": ["db_manager", "corpus_full", "detector"],
    "detector_slim": ["db_manager", "corpus_slim", "detector"],
    "wordfinder_today": ["wordfinder_today"],
    "wordfinder_interned": ["wordfinder_interned"],
    "reload_full": ["db_manager", "corpus_full", "detector", "reload_full"],
    "reload_slim": ["db_manager", "corpus_slim", "detector", "reload_slim"],
    "contributor_today": CONTRIBUTOR_TODAY,
    "contributor_levers": CONTRIBUTOR_LEVERS,
    "contributor_levers_l5": without(CONTRIBUTOR_LEVERS, "sets_direct"),
    "contributor_lazy": without(
        CONTRIBUTOR_TODAY, "ai_manager", "bold_search", "detector"
    ),
    "warm_today": without(CONTRIBUTOR_TODAY, "sets_today"),
    "warm_levers": without(CONTRIBUTOR_LEVERS, "sets_direct"),
    # one lever at a time, whole build, so the allocator's reuse between steps
    # cannot hide or invent a saving
    "corpus_slim_noinfl": ["db_manager", "corpus_slim_noinfl"],
    "warm_slim": swap(
        without(CONTRIBUTOR_TODAY, "sets_today"), "corpus_full", "corpus_slim"
    ),
    "warm_slim_noinfl": swap(
        without(CONTRIBUTOR_TODAY, "sets_today"), "corpus_full", "corpus_slim_noinfl"
    ),
    "warm_slim_nofreq": swap(
        without(CONTRIBUTOR_TODAY, "sets_today"), "corpus_full", "corpus_slim_nofreq"
    ),
    "warm_interned": swap(
        without(CONTRIBUTOR_TODAY, "sets_today"),
        "wordfinder_today",
        "wordfinder_interned",
    ),
    "contributor_slim": swap(CONTRIBUTOR_TODAY, "corpus_full", "corpus_slim"),
    "contributor_sets_direct": swap(CONTRIBUTOR_TODAY, "sets_today", "sets_direct"),
    # round 3: freq_data only for headwords with an empty meaning, and a compact set
    "corpus_slim_split": ["db_manager", "corpus_slim_split"],
    "sets_hash": ["db_manager", "sets_hash"],
    "warm_slim_split": swap(
        without(CONTRIBUTOR_TODAY, "sets_today"), "corpus_full", "corpus_slim_split"
    ),
    "contributor_hash": swap(CONTRIBUTOR_TODAY, "sets_today", "sets_hash"),
    "contributor_split_direct": swap(
        swap(CONTRIBUTOR_TODAY, "corpus_full", "corpus_slim_split"),
        "sets_today",
        "sets_direct",
    ),
    "contributor_split_hash": swap(
        swap(CONTRIBUTOR_TODAY, "corpus_full", "corpus_slim_split"),
        "sets_today",
        "sets_hash",
    ),
    # task 3.8: the real code (contributor branches in DatabaseManager), not a prototype
    "contributor_real": CONTRIBUTOR_TODAY,
}
NEEDS_DB = {
    name
    for name, steps in VARIANTS.items()
    if any(
        s in steps
        for s in ("db_manager", "bold_search", "sets_direct", "sets_direct_both")
    )
}


# ---------------------------------------------------------------- readings


def vm_field(name: str) -> float:
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + ":"):
            return int(line.split()[1]) / 1024
    return 0.0


def take_reading(label: str) -> dict[str, Any]:
    proc = psutil.Process()
    full = proc.memory_full_info()
    return {
        "label": label,
        "rss_mb": round(full.rss / MB, 1),
        "pss_mb": round(getattr(full, "pss", 0) / MB, 1),
        "uss_mb": round(full.uss / MB, 1),
        "hwm_mb": round(vm_field("VmHWM"), 1),
        "swap_mb": round(vm_field("VmSwap"), 1),
        "threads": proc.num_threads(),
    }


def commit_id() -> str:
    """Read the commit from .git directly; the standing rule is no git command."""
    try:
        head = Path(".git/HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return head[:12]
        ref_file = Path(".git") / head[5:]
        if ref_file.is_file():
            return ref_file.read_text(encoding="utf-8").strip()[:12]
        for line in Path(".git/packed-refs").read_text(encoding="utf-8").splitlines():
            if line.endswith(" " + head[5:]):
                return line.split()[0][:12]
    except OSError:
        pass
    return "unknown"


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    if not root.is_dir():
        return result
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            result[str(path)] = (stat.st_mtime_ns, stat.st_size)
    return result


def changed_files(
    before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]
) -> list[str]:
    return sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))


# ------------------------------------------------------------------- stats


def median(values: list[float]) -> float:
    return statistics.median(values)


def spread_flag(values: list[float]) -> bool:
    if len(values) < 2:
        return False
    mid = median(values)
    return mid > 0 and (max(values) - min(values)) > SPREAD_LIMIT * mid


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def step_delta(row: dict[str, Any], label: str) -> float | None:
    """The reading with `label` minus the reading before it."""
    items = row.get("readings", [])
    for index, item in enumerate(items):
        if item["label"] == label:
            before = float(items[index - 1]["rss_mb"]) if index else 0.0
            return float(item["rss_mb"]) - before
    return None


def primary(row: dict[str, Any]) -> float | None:
    """The number that stands for a run: the last step's delta, or the final
    RSS for the whole-build variants."""
    items = row.get("readings", [])
    if not items:
        return None
    if str(row.get("variant", "")).startswith(WHOLE_BUILD):
        return float(items[-1]["rss_mb"])
    return step_delta(row, items[-1]["label"])


# ------------------------------------------------------------------- child


@dataclass
class Ctx:
    db_path: Path | None
    tmp: Path
    meta: dict[str, Any]
    columns_md: Path
    fake_mb: int = 0
    fake_raise: bool = False
    objs: dict[str, Any] = field(default_factory=dict)


def patch_db(db_path: Path) -> None:
    """Point every `get_db_session` at the copy, before any engine is built."""
    import db.db_helpers as db_helpers

    original = db_helpers.get_db_session

    def patched(_path: Path) -> Any:
        return original(db_path)

    for module in list(sys.modules.values()):
        if (
            isinstance(module, ModuleType)
            and vars(module).get("get_db_session") is original
        ):
            setattr(module, "get_db_session", patched)


def check_session(session: Any, c: Ctx) -> None:
    from sqlalchemy import text

    query_only = session.execute(text("PRAGMA query_only")).scalar()
    c.meta["query_only"] = query_only
    if query_only != 1:
        raise RuntimeError(f"PRAGMA query_only is {query_only}, expected 1")
    files = [row[2] for row in session.execute(text("PRAGMA database_list"))]
    if c.db_path is None or str(c.db_path.resolve()) not in files:
        raise RuntimeError("the session does not read the --db copy")


def step_imports(c: Ctx) -> None:
    importlib.import_module("gui2.main")
    if c.db_path:
        patch_db(c.db_path)


def step_db_manager(c: Ctx) -> None:
    import gui2.database_manager as database_manager

    manager = database_manager.DatabaseManager(c.tmp / "checked.csv")
    check_session(manager.db_session, c)
    c.objs["dbm"] = manager


def step_initialize_db(c: Ctx) -> None:
    c.objs["dbm"].initialize_db()


def step_corpus_full(c: Ctx) -> None:
    c.objs["dbm"].load_corpus()


def slim_columns(c: Ctx, drop: tuple[str, ...] = ()) -> list[str]:
    """Column names from the table in columns.md, minus `id` and `drop`."""
    names: list[str] = []
    for line in c.columns_md.read_text(encoding="utf-8").splitlines():
        cells = [x.strip() for x in line.strip("|").split("|")]
        if len(cells) == 3 and cells[1] in ("yes", "no") and cells[0] not in drop:
            names.append(cells[0])
    return names


def load_slim(c: Ctx, drop: tuple[str, ...] = ()) -> None:
    """Load only the needed columns and mark the corpus fresh, as the real
    change would, so later steps use these rows and do not reload."""
    from sqlalchemy.orm import load_only

    from db.models import DpdHeadword

    manager = c.objs["dbm"]
    attrs = [getattr(DpdHeadword, name) for name in slim_columns(c, drop)]
    manager.db = manager.db_session.query(DpdHeadword).options(load_only(*attrs)).all()
    manager._corpus_stale = False
    manager._corpus_gen += 1


def step_corpus_slim(c: Ctx) -> None:
    load_slim(c)


def step_corpus_slim_nofreq(c: Ctx) -> None:
    load_slim(c, drop=("freq_data",))


def step_corpus_slim_split(c: Ctx) -> None:
    """No inflection columns (the sets do not come from the corpus). `freq_data`
    only for headwords with an empty meaning_1: the detector reads it only
    there (tools/synonym_variant.py:351-353). Same rows, same order."""
    from sqlalchemy.orm import load_only

    from db.models import DpdHeadword

    manager = c.objs["dbm"]
    drop = ("inflections", "inflections_api_ca_eva_iti")
    with_freq = slim_columns(c, drop)
    without_freq = slim_columns(c, drop + ("freq_data",))
    session = manager.db_session
    has_meaning = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 != "")
        .options(load_only(*[getattr(DpdHeadword, n) for n in without_freq]))
        .all()
    )
    no_meaning = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .options(load_only(*[getattr(DpdHeadword, n) for n in with_freq]))
        .all()
    )
    manager.db = sorted(has_meaning + no_meaning, key=lambda row: row.id)
    manager._corpus_stale = False
    manager._corpus_gen += 1


class HashedWords:
    """Membership test for a large set of words in 8 bytes per word: a sorted
    array of 64-bit hashes. A wrong "yes" needs a hash collision."""

    MASK = 0xFFFFFFFFFFFFFFFF

    def __init__(self, words: Any) -> None:
        from array import array

        hashes = array("Q", (hash(w) & self.MASK for w in words))
        unique = array("Q")
        last = None
        for value in sorted(hashes):
            if value != last:
                unique.append(value)
                last = value
        self._hashes = unique

    def __contains__(self, word: object) -> bool:
        from bisect import bisect_left

        if not isinstance(word, str):
            return False
        key = hash(word) & self.MASK
        index = bisect_left(self._hashes, key)
        return index < len(self._hashes) and self._hashes[index] == key

    def __len__(self) -> int:
        return len(self._hashes)


def step_corpus_slim_noinfl(c: Ctx) -> None:
    """The slim set without the two inflection columns, for the case where the
    inflection set is answered by the lookup table (L5)."""
    load_slim(c, drop=("inflections", "inflections_api_ca_eva_iti"))


def step_sets_today(c: Ctx) -> None:
    c.objs["dbm"].make_inflections_lists()


def direct_sets(c: Ctx, with_meaning: bool) -> None:
    from db.models import DpdHeadword

    session = c.objs["dbm"].db_session
    all_inflections: set[str] = set()
    missing: set[str] = set()
    columns = [DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti]
    if with_meaning:
        columns.append(DpdHeadword.meaning_1)
    for row in session.query(*columns):
        words = row[0].split(",") + row[1].split(",")
        all_inflections.update(words)
        if with_meaning and not row[2]:
            missing.update(words)
    c.objs["all_inflections"] = all_inflections
    c.objs["missing"] = missing


def step_sets_direct(c: Ctx) -> None:
    direct_sets(c, with_meaning=False)


def step_sets_direct_both(c: Ctx) -> None:
    direct_sets(c, with_meaning=True)


def step_sets_hash(c: Ctx) -> None:
    from db.models import DpdHeadword

    session = c.objs["dbm"].db_session

    def words() -> Any:
        for first, second in session.query(
            DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti
        ):
            yield from first.split(",")
            yield from second.split(",")

    c.objs["all_inflections"] = HashedWords(words())


def step_detector(c: Ctx) -> None:
    c.objs["detector"] = c.objs["dbm"].get_relationship_detector()


def step_wordfinder_today(c: Ctx) -> None:
    from tools.wordfinder_manager import WordFinderManager

    c.objs["wordfinder"] = WordFinderManager()


def step_wordfinder_interned(c: Ctx) -> None:
    """The same data as the real load, with one string per word."""
    from tools.paths import ProjectPaths

    def intern_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        return {sys.intern(key): value for key, value in pairs}

    with open(ProjectPaths().cst_file_freq, encoding="utf-8") as handle:
        c.objs["wordfinder_data"] = json.load(handle, object_pairs_hook=intern_keys)


def step_ai_manager(c: Ctx) -> None:
    folders = os.environ.get("PATH", "").split(os.pathsep)
    kept = [f for f in folders if not (Path(f) / "agy").exists()]
    os.environ["PATH"] = os.pathsep.join(kept)
    from tools.ai_manager import AIManager

    manager = AIManager()
    c.objs["ai"] = manager
    c.meta["providers_built"] = sorted(manager.providers)


def step_bold_search(c: Ctx) -> None:
    from tools.bold_definitions_search import BoldDefinitionsSearchManager

    searcher = BoldDefinitionsSearchManager()
    check_session(searcher.session, c)
    c.objs["bold"] = searcher


def step_spellchecker(c: Ctx) -> None:
    from tools.spelling import CustomSpellChecker

    c.objs["spell"] = CustomSpellChecker(c.tmp / "spell_dictionary.txt")


def step_reload_full(c: Ctx) -> None:
    """What the Pass1Add "refresh DB" button leads to: stale, then a new load."""
    manager = c.objs["dbm"]
    manager.mark_corpus_stale()
    manager.load_corpus()


def step_reload_slim(c: Ctx) -> None:
    c.objs["dbm"].mark_corpus_stale()
    load_slim(c)


def step_fake(c: Ctx) -> None:
    if c.fake_raise:
        raise RuntimeError("fake failure")
    chunks = []
    for _ in range(c.fake_mb // 10):
        chunks.append(b"\x01" * (10 * MB))
        time.sleep(0.05)
    c.objs["fake"] = chunks


STEPS: dict[str, Callable[[Ctx], None]] = {
    "db_manager": step_db_manager,
    "initialize_db": step_initialize_db,
    "corpus_full": step_corpus_full,
    "corpus_slim": step_corpus_slim,
    "corpus_slim_nofreq": step_corpus_slim_nofreq,
    "corpus_slim_noinfl": step_corpus_slim_noinfl,
    "corpus_slim_split": step_corpus_slim_split,
    "sets_hash": step_sets_hash,
    "sets_today": step_sets_today,
    "sets_direct": step_sets_direct,
    "sets_direct_both": step_sets_direct_both,
    "detector": step_detector,
    "wordfinder_today": step_wordfinder_today,
    "wordfinder_interned": step_wordfinder_interned,
    "ai_manager": step_ai_manager,
    "bold_search": step_bold_search,
    "spellchecker": step_spellchecker,
    "reload_full": step_reload_full,
    "reload_slim": step_reload_slim,
}


def build_steps(variant: str) -> list[tuple[str, Callable[[Ctx], None] | None]]:
    """(label, step) pairs; a reading is taken after each one."""
    if variant == "_fake":
        return [("bare", None), ("_fake", step_fake)]
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant}")
    steps: list[tuple[str, Callable[[Ctx], None] | None]] = [
        ("bare", None),
        ("imports", step_imports),
    ]
    return steps + [(name, STEPS[name]) for name in VARIANTS[variant]]


class Recorder:
    def __init__(self, variant: str, out: Path, cap_mb: float, meta: dict[str, Any]):
        self.row: dict[str, Any] = {
            "variant": variant,
            "outcome": "ok",
            "readings": [],
            "meta": meta,
        }
        self.out = out
        self.cap_mb = cap_mb
        self.current = "start"
        self.lock = threading.Lock()
        self.written = False
        self.done = threading.Event()

    def take(self, label: str) -> None:
        self.row["readings"].append(take_reading(label))

    def write(self, outcome: str, **extra: Any) -> None:
        with self.lock:
            if self.written:
                return
            self.written = True
            self.row["outcome"] = outcome
            self.row.update(extra)
            with self.out.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(self.row) + "\n")

    def watch(self) -> None:
        me = psutil.Process()
        while not self.done.is_set():
            if me.memory_info().rss / MB > self.cap_mb:
                last = take_reading("capped")
                self.row["readings"].append(last)
                self.write("capped", reached=self.current, last_reading=last)
                os._exit(3)
            time.sleep(0.1)


def run_child(args: argparse.Namespace) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="leverprobe_"))
    os.environ["DPD_GUI2_ROLE"] = "contributor-server"
    os.environ["DPD_GUI2_USERNAME"] = "memprobe"
    os.environ["DPD_GUI2_DATA_DIR"] = str(tmp)
    db_path = Path(args.db) if args.db else None
    meta: dict[str, Any] = {
        "commit": commit_id(),
        "python": sys.version.split()[0],
        "db_size": db_path.stat().st_size if db_path and db_path.exists() else None,
        "providers_built": [],
        "agy_found": bool(shutil.which("agy")),
        "malloc_arena_max": os.environ.get("MALLOC_ARENA_MAX"),
        "loadavg": os.getloadavg()[0],
    }
    rec = Recorder(args.variant, Path(args.out), args.watchdog_mb, meta)
    if args.variant in NEEDS_DB and (db_path is None or not db_path.is_file()):
        rec.write("error", error_type="UsageError", error="--db copy is required")
        return 1
    if args.guard_dirs:
        fail_dirs = [Path(p) for p in args.guard_dirs.split(",")]
        warn_dirs: list[Path] = []
    else:
        fail_dirs = [Path("gui2/data"), Path("gui2/storage"), tmp]
        warn_dirs = [Path("shared_data")]
    before = {d: snapshot(d) for d in fail_dirs + warn_dirs}

    ctx = Ctx(db_path, tmp, meta, Path(args.columns_md), args.fake_mb, args.fake_raise)
    threading.Thread(target=rec.watch, daemon=True).start()
    try:
        for label, step in build_steps(args.variant):
            rec.current = label
            if step:
                step(ctx)
            rec.take(label)
        gc.collect()
        rec.row["rss_after_gc_mb"] = round(psutil.Process().memory_info().rss / MB, 1)
        ctypes.CDLL("libc.so.6").malloc_trim(0)
        rec.row["rss_after_trim_mb"] = round(psutil.Process().memory_info().rss / MB, 1)
        hit = [n for d in fail_dirs for n in changed_files(before[d], snapshot(d))]
        meta["guard_warnings"] = [
            n for d in warn_dirs for n in changed_files(before[d], snapshot(d))
        ]
        if hit:
            rec.write("error", error_type="GuardViolation", error=", ".join(hit[:10]))
        else:
            rec.write("ok")
    except (Exception, SystemExit) as exc:
        rec.write(
            "error",
            error_type=type(exc).__name__,
            error=str(exc)[:300],
            reached=rec.current,
        )
    finally:
        rec.done.set()
    return 0


# ------------------------------------------------------------------ driver


def say(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def run_one(
    variant: str, args: argparse.Namespace, run_id: str, record: bool = True
) -> dict[str, Any]:
    out = Path(tempfile.mkdtemp(prefix="leverrun_")) / "row.jsonl"
    cmd = [
        "systemd-run", "--user", "--scope", "-q",
        "-p", "MemoryMax=1500M", "-p", "MemorySwapMax=0", "--",
        "env", "MALLOC_ARENA_MAX=2", "PYTHONPATH=.",
        sys.executable, str(Path(__file__)),
        "--variant", variant, "--out", str(out), "--db", args.db,
        "--columns-md", args.columns_md,
    ]  # fmt: skip
    try:
        done = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CHILD_TIMEOUT_S
        )
        rows, code, tail = read_jsonl(out), done.returncode, done.stderr[-200:]
    except subprocess.TimeoutExpired:
        rows, code, tail = read_jsonl(out), None, "timeout"
    row: dict[str, Any]
    if rows:
        row = rows[-1]
    else:
        row = {"variant": variant, "outcome": "killed", "note": "killed (no output)"}
        row["returncode"], row["stderr_tail"] = code, tail
    row["run_id"] = run_id
    if record:
        with Path(args.out).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
    return row


def drive(args: argparse.Namespace) -> int:
    started = time.monotonic()
    warm = run_one("corpus_full", args, "warmup", record=False)
    if warm["outcome"] != "ok":
        say(f"warm-up run {warm['outcome']}: stopping")
        return 1
    count = 1
    names = args.only.split(",") if args.only else list(VARIANTS)
    for variant in names:
        rows: list[dict[str, Any]] = []
        for repeat in range(2):
            for index in range(3):
                if time.monotonic() - started > DRIVER_TIMEOUT_S:
                    say("40 minute limit reached: stopping")
                    return 1
                row = run_one(variant, args, f"{variant}#{repeat * 3 + index + 1}")
                count += 1
                say(f"{count:3d} {variant} {row['outcome']}")
                if row["outcome"] != "ok":
                    say(f"stopping on {row['outcome']}: {row.get('error', '')}")
                    return 1
                rows.append(row)
            values = [v for v in (primary(r) for r in rows) if v is not None]
            if repeat == 0 and spread_flag(values):
                say(f"{variant}: spread above 10 % of the median, 3 more runs")
                continue
            break
    say(f"done: {count} processes")
    return 0


# ------------------------------------------------------------------ report


def final_rss(rows: list[dict[str, Any]]) -> list[float]:
    return [float(r["readings"][-1]["rss_mb"]) for r in rows]


def final_hwm(rows: list[dict[str, Any]]) -> list[float]:
    return [float(r["readings"][-1]["hwm_mb"]) for r in rows]


def report(rows_path: Path, out: Path) -> None:
    rows = [r for r in read_jsonl(rows_path) if r.get("outcome") == "ok"]
    by: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by.setdefault(row["variant"], []).append(row)

    def deltas(variant: str, step: str) -> list[float]:
        found = [step_delta(r, step) for r in by.get(variant, [])]
        return [v for v in found if v is not None]

    def span(values: list[float]) -> str:
        if not values:
            return "n/a"
        mark = " ⚑" if spread_flag(values) else ""
        return f"{median(values):.1f} ({min(values):.1f}–{max(values):.1f}){mark}"

    def saving(a: list[float], b: list[float]) -> str:
        if not a or not b:
            return "n/a"
        return (
            f"{median(a) - median(b):.1f} ({min(a) - max(b):.1f}–{max(a) - min(b):.1f})"
        )

    def med(values: list[float]) -> float | None:
        return median(values) if values else None

    lines = ["# Lever results (MB, laptop, fresh process per run)", ""]
    lines += ["## Step cost per variant (delta of the last step)", ""]
    lines += [
        "| Variant | Last step | Delta, median (min–max) | Runs |",
        "|---|---|---|---|",
    ]
    for variant, steps in VARIANTS.items():
        last = steps[-1]
        lines.append(
            f"| {variant} | {last} | {span(deltas(variant, last))} | {len(by.get(variant, []))} |"
        )

    c = deltas

    def final(name: str) -> list[float]:
        return final_rss(by.get(name, []))

    lever_rows = [
        ("L1 slim corpus (warm build, sets not built)", saving(final("warm_today"), final("warm_slim"))),
        ("L1 slim corpus, with the sets still built (Pass1 used)", saving(final("contributor_today"), final("contributor_slim"))),
        ("L1 slim corpus without the two inflection columns (needs L5)", saving(final("warm_today"), final("warm_slim_noinfl"))),
        ("L7 ceiling: also without freq_data (would change detector results)", saving(final("warm_today"), final("warm_slim_nofreq"))),
        ("L2 direct sets instead of today's sets", saving(final("contributor_today"), final("contributor_sets_direct"))),
        ("L3 missing-meaning set (step cost of the direct build)", saving(c("sets_direct_both", "sets_direct_both"), c("sets_direct", "sets_direct"))),
        ("L4 interned word finder (warm build)", saving(final("warm_today"), final("warm_interned"))),
        ("L5 no inflection set at all (whole build; the lookup table is NOT equivalent, see equivalence.md)", saving(final("contributor_today"), final("warm_today"))),
        ("L7b freq_data only for headwords with no meaning, no inflection columns (warm build)", saving(final("warm_today"), final("warm_slim_split"))),
        ("L8 compact inflection set (whole build)", saving(final("contributor_today"), final("contributor_hash"))),
        ("L1 + L7b + direct sets", saving(final("contributor_today"), final("contributor_split_direct"))),
        ("L1 + L7b + compact set", saving(final("contributor_today"), final("contributor_split_hash"))),
        ("L1 + L5 together (slim without inflection columns, no set)", saving(final("contributor_today"), final("warm_slim_noinfl"))),
        ("L6 lazy managers (AI, bold search, detector never built)", saving(final("contributor_today"), final("contributor_lazy"))),
        ("Refresh DB: extra memory, full corpus", saving(final("reload_full"), final("detector_full"))),
        ("Refresh DB: extra memory, slim corpus", saving(final("reload_slim"), final("detector_slim"))),
    ]  # fmt: skip
    lines += ["", "## Saving per lever (before − after, median; range in brackets)", ""]
    lines += ["A negative number means the lever costs memory.", ""]
    lines += ["| Lever | Saving |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in lever_rows]

    lines += ["", "## Whole contributor build (final RSS and start-up peak)", ""]
    lines += ["| Variant | Final RSS | Peak (VmHWM) |", "|---|---|---|"]
    for variant in VARIANTS:
        if variant.startswith(WHOLE_BUILD):
            rs, hw = final(variant), final_hwm(by.get(variant, []))
            lines.append(f"| {variant} | {span(rs)} | {span(hw)} |")

    def total_saving(after: str) -> float | None:
        before_values, after_values = final("contributor_today"), final(after)
        if not before_values or not after_values:
            return None
        return median(before_values) - median(after_values)

    lines += ["", "## Estimate for the server (saving measured on the laptop)", ""]
    scenarios = [
        ("L1 only", total_saving("contributor_slim")),
        ("L1+L7b+direct sets", total_saving("contributor_split_direct")),
        ("L1+L7b+compact set", total_saving("contributor_split_hash")),
    ]
    if all(v is not None for _, v in scenarios):
        header = "| Contributors | Today |" + "".join(f" {n} |" for n, _ in scenarios)
        lines += [header, "|---|---|" + "---|" * len(scenarios)]
        for n in (3, 8, 16):
            cells = "".join(
                f" {BASELINE_MB + n * (SERVER_ONE_BOOK_MB - (v or 0)):.0f} |"
                for _, v in scenarios
            )
            lines.append(f"| {n} | {BASELINE_MB + n * SERVER_ONE_BOOK_MB:.0f} |{cells}")
        lines += [
            "",
            "Per instance after one book: "
            + ", ".join(
                f"{name} {SERVER_ONE_BOOK_MB - (v or 0):.0f} MB"
                for name, v in scenarios
            )
            + f" (today {SERVER_ONE_BOOK_MB} MB).",
            "Server baseline 1066 MB; today's figures from `contrib_mem_measure/artifacts/server/results.md`. The earlier thread found the laptop and the server agree to 5 MB.",
        ]
    else:
        lines.append("n/a (composite variants missing)")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say(f"wrote {out}")


# ---------------------------------------------------------------- selftest


def child_row(extra: list[str], cap: float) -> tuple[int, dict[str, Any] | None]:
    work = Path(tempfile.mkdtemp(prefix="leverself_"))
    out = work / "row.jsonl"
    cmd = [sys.executable, str(Path(__file__)), "--variant", "_fake", "--out", str(out)]
    cmd += ["--watchdog-mb", str(cap), "--guard-dirs", str(work / "guard")] + extra
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    rows = read_jsonl(out)
    return done.returncode, (rows[-1] if rows else None)


def selftest(cap: float) -> str | None:
    """Return the label of the first failing check, or None."""
    code, row = child_row(["--fake-mb", "60"], cap)
    delta = step_delta(row, "_fake") if row else None
    if not (row and row["outcome"] == "ok" and delta and 45 <= delta <= 75):
        return "(a)"
    code, row = child_row(["--fake-mb", "300"], cap)
    if not (
        code == 3 and row and row["outcome"] == "capped" and row.get("last_reading")
    ):
        return "(b)"
    code, row = child_row(["--fake-raise"], cap)
    if not (row and row["outcome"] == "error" and row["error_type"] == "RuntimeError"):
        return "(c)"
    guard = Path(tempfile.mkdtemp(prefix="leverguard_"))
    (guard / "a.txt").write_text("x", encoding="utf-8")
    first = snapshot(guard)
    if changed_files(first, snapshot(guard)):
        return "(d)"
    time.sleep(0.01)
    (guard / "a.txt").write_text("xy", encoding="utf-8")
    if changed_files(first, snapshot(guard)) != [str(guard / "a.txt")]:
        return "(d)"
    if median([100.0, 104.0, 108.0]) != 104.0:
        return "(e)"
    if spread_flag([100.0, 104.0, 108.0]) or not spread_flag([100.0, 120.0, 100.0]):
        return "(e)"
    sample = {"readings": [{"label": "a", "rss_mb": 10}, {"label": "b", "rss_mb": 35}]}
    if step_delta(sample, "b") != 25 or step_delta(sample, "a") != 10:
        return "(e)"
    return None


# -------------------------------------------------------------------- main


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant")
    parser.add_argument("--db", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--report")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--columns-md", default=DEFAULT_COLUMNS_MD)
    parser.add_argument("--watchdog-mb", type=float, default=1400)
    parser.add_argument("--guard-dirs", default="")
    # self-test hooks only
    parser.add_argument("--fake-mb", type=int, default=0)
    parser.add_argument("--fake-raise", action="store_true")
    parser.add_argument("--selftest-cap", type=float, default=150)
    return parser.parse_args()


def main() -> int:
    args = parse()
    if args.selftest:
        failed = selftest(args.selftest_cap)
        say("SELFTEST_OK" if failed is None else f"SELFTEST_FAIL: {failed}")
        return 0 if failed is None else 1
    if args.report:
        if not args.out:
            say("--report needs --out")
            return 2
        report(Path(args.report), Path(args.out))
        return 0
    if args.all:
        if not (args.db and args.out):
            say("--all needs --db and --out")
            return 2
        return drive(args)
    if args.variant and args.out:
        return run_child(args)
    say("nothing to do: give --variant, --all, --report or --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
