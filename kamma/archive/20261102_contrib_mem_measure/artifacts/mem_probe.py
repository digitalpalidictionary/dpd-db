"""Measure where one contributor gui2 instance spends its memory.

One measurement per process. See spec.md and plan.md in the parent folder.
Run from the repo root. Child modes write one JSON row to --out.

    --point <name>     run one point in this process (the child)
    --all              the driver: every point, three fresh processes each
    --unit-readings    read the python processes of a systemd unit
    --selftest         check the probe itself
"""

import argparse
import ctypes
import gc
import importlib
import json
import os
import shutil
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
from mem_stats import (
    partial_status,
    point_delta,
    primary,
    read_jsonl,
    spread_flag,
    summarize,
)

MB = 1024 * 1024
ISOLATED = [
    "bare",
    "imports",
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
STAIRCASE = [
    "bare",
    "imports",
    "db_manager",
    "initialize_db",
    "corpus",
    "inflections_lists",
    "wordfinder",
    "ai_manager",
    "bold_search",
    "relationship_detector",
    "spellchecker",
]
PREREQ = {
    "initialize_db": ["db_manager"],
    "corpus": ["db_manager"],
    "inflections_lists": ["db_manager", "corpus"],
    "relationship_detector": ["db_manager", "corpus"],
}
NEEDS_DB = {
    "db_manager",
    "initialize_db",
    "corpus",
    "inflections_lists",
    "relationship_detector",
    "bold_search",
    "staircase",
}
DRIVER_TIMEOUT_S = 40 * 60
CHILD_TIMEOUT_S = 600


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
        ref = head[5:]
        ref_file = Path(".git") / ref
        if ref_file.is_file():
            return ref_file.read_text(encoding="utf-8").strip()[:12]
        for line in Path(".git/packed-refs").read_text(encoding="utf-8").splitlines():
            if line.endswith(" " + ref):
                return line.split()[0][:12]
    except OSError:
        pass
    return "unknown"


# ------------------------------------------------------------------- guard


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
    names = set(before) | set(after)
    return sorted(n for n in names if before.get(n) != after.get(n))


# ------------------------------------------------------------------- child


@dataclass
class Ctx:
    db_path: Path | None
    tmp: Path
    meta: dict[str, Any]
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
    """The loaders must read the copy, and read-only."""
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

    original = database_manager.load_decon_no_headwords_cache

    def spy(session: Any) -> Any:
        result = original(session)
        c.meta["decon_cache"] = "miss" if result is None else "hit"
        return result

    setattr(database_manager, "load_decon_no_headwords_cache", spy)
    manager = database_manager.DatabaseManager(c.tmp / "checked.csv")
    check_session(manager.db_session, c)
    c.objs["dbm"] = manager


def step_initialize_db(c: Ctx) -> None:
    c.objs["dbm"].initialize_db()


def step_corpus(c: Ctx) -> None:
    c.objs["dbm"].load_corpus()


def step_inflections_lists(c: Ctx) -> None:
    c.objs["dbm"].make_inflections_lists()


def step_relationship_detector(c: Ctx) -> None:
    c.objs["detector"] = c.objs["dbm"].get_relationship_detector()


def step_wordfinder(c: Ctx) -> None:
    from tools.wordfinder_manager import WordFinderManager

    c.objs["wordfinder"] = WordFinderManager()


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


def open_book(c: Ctx, name: str) -> None:
    from gui2.books import sutta_central_books
    from tools.cst_sc_text_sets import make_cst_text_list

    book = sutta_central_books[name]
    c.objs[f"seg:{name}"] = book.segment_dict
    c.objs[f"word:{name}"] = book.word_dict
    c.objs[f"cst:{name}"] = make_cst_text_list(book.cst_books, dedupe=True)


def step_fake(c: Ctx) -> None:
    if c.fake_raise:
        raise RuntimeError("fake failure")
    chunks = []
    for _ in range(c.fake_mb // 10):
        chunks.append(b"\x01" * (10 * MB))
        time.sleep(0.05)
    c.objs["fake"] = chunks


STEPS: dict[str, Callable[[Ctx], None]] = {
    "imports": step_imports,
    "db_manager": step_db_manager,
    "initialize_db": step_initialize_db,
    "corpus": step_corpus,
    "inflections_lists": step_inflections_lists,
    "relationship_detector": step_relationship_detector,
    "wordfinder": step_wordfinder,
    "ai_manager": step_ai_manager,
    "bold_search": step_bold_search,
    "spellchecker": step_spellchecker,
    "_fake": step_fake,
}


def build_steps(
    point: str, book: str | None, books: list[str]
) -> list[tuple[str, Callable[[Ctx], None] | None]]:
    """(label, step) pairs; a reading is taken after each one."""
    if point == "staircase":
        return [(name, STEPS.get(name)) for name in STAIRCASE]
    steps: list[tuple[str, Callable[[Ctx], None] | None]] = [("bare", None)]
    if point == "bare":
        return steps
    if point == "_fake":
        return steps + [("_fake", step_fake)]
    steps.append(("imports", step_imports))
    if point == "imports":
        return steps
    if point == "book":
        if not book:
            raise ValueError("--point book needs --book")
        return steps + [(f"book:{book}", lambda c, b=book: open_book(c, b))]
    if point == "books_cumulative":
        if not books:
            raise ValueError("--point books_cumulative needs --books")
        for name in books:
            steps.append((f"book:{name}", lambda c, b=name: open_book(c, b)))
        return steps
    for prereq in PREREQ.get(point, []):
        steps.append((prereq, STEPS[prereq]))
    steps.append((point, STEPS[point]))
    return steps


class Recorder:
    def __init__(self, point: str, out: Path, cap_mb: float, meta: dict[str, Any]):
        self.row: dict[str, Any] = {
            "point": point,
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
            rss = me.memory_info().rss / MB
            if rss > self.cap_mb:
                last = take_reading("capped")
                self.row["readings"].append(last)
                self.write("capped", reached=self.current, last_reading=last)
                os._exit(3)
            time.sleep(0.1)


def run_child(args: argparse.Namespace) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="memprobe_"))
    os.environ["DPD_GUI2_ROLE"] = "contributor-server"
    os.environ["DPD_GUI2_USERNAME"] = "memprobe"
    os.environ["DPD_GUI2_DATA_DIR"] = str(tmp)
    db_path = Path(args.db) if args.db else None
    meta: dict[str, Any] = {
        "commit": commit_id(),
        "python": sys.version.split()[0],
        "db_size": db_path.stat().st_size if db_path and db_path.exists() else None,
        "env_gates": {
            "DPD_GUI2_ROLE": "contributor-server",
            "DPD_GUI2_USERNAME": "memprobe",
            "DPD_GUI2_DATA_DIR": "set",
        },
        "providers_built": [],
        "agy_found": bool(shutil.which("agy")),
        "malloc_arena_max": os.environ.get("MALLOC_ARENA_MAX"),
        "loadavg": os.getloadavg()[0],
        "decon_cache": "not_run",
    }
    rec = Recorder(args.point, Path(args.out), args.watchdog_mb, meta)
    if args.point in NEEDS_DB and (db_path is None or not db_path.is_file()):
        rec.write("error", error_type="UsageError", error="--db copy is required")
        return 1

    if args.guard_dirs:
        fail_dirs = [Path(p) for p in args.guard_dirs.split(",")]
        warn_dirs: list[Path] = []
    else:
        fail_dirs = [Path("gui2/data"), Path("gui2/storage"), tmp]
        warn_dirs = [Path("shared_data")]
    before = {d: snapshot(d) for d in fail_dirs + warn_dirs}

    ctx = Ctx(db_path, tmp, meta, args.fake_mb, args.fake_raise)
    threading.Thread(target=rec.watch, daemon=True).start()
    try:
        steps = build_steps(
            args.point, args.book, args.books.split(",") if args.books else []
        )
        for label, step in steps:
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
    point: str,
    args: argparse.Namespace,
    run_id: str,
    book: str | None = None,
    record: bool = True,
) -> dict[str, Any]:
    out = Path(tempfile.mkdtemp(prefix="memrun_")) / "row.jsonl"
    cmd = [
        "systemd-run", "--user", "--scope", "-q",
        "-p", "MemoryMax=1500M", "-p", "MemorySwapMax=0", "--",
        "env", "MALLOC_ARENA_MAX=2", "PYTHONPATH=.",
        sys.executable, str(Path(__file__)),
        "--point", point, "--out", str(out), "--db", args.db,
    ]  # fmt: skip
    if book:
        cmd += ["--book", book]
    if point == "books_cumulative":
        cmd += ["--books", args.books]
    try:
        done = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CHILD_TIMEOUT_S
        )
        rows = read_jsonl(out)
        code, tail = done.returncode, done.stderr[-200:]
    except subprocess.TimeoutExpired:
        rows, code, tail = read_jsonl(out), None, "timeout"
    row: dict[str, Any]
    if rows:
        row = rows[-1]
    else:
        row = {"point": point, "outcome": "killed", "note": "killed (no output)"}
        row["returncode"], row["stderr_tail"] = code, tail
    row["run_id"] = run_id
    if book:
        row["book"] = book
    if record:
        with Path(args.out).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
    return row


def drive(args: argparse.Namespace) -> int:
    started = time.monotonic()
    books = args.books.split(",")
    jobs: list[tuple[str, str | None]] = [(p, None) for p in ISOLATED]
    jobs += [("book", b) for b in books]
    jobs += [("books_cumulative", None), ("staircase", None)]
    warm = run_one("bare", args, "warmup", record=False)
    if warm["outcome"] != "ok":
        say(f"warm-up run {warm['outcome']}: stopping")
        return 1
    count = 1
    for point, book in jobs:
        rows: list[dict[str, Any]] = []
        for repeat in range(2):
            for index in range(3):
                if time.monotonic() - started > DRIVER_TIMEOUT_S:
                    say("40 minute limit reached: stopping")
                    return 1
                name = f"{point}:{book}" if book else point
                row = run_one(point, args, f"{name}#{repeat * 3 + index + 1}", book)
                count += 1
                say(f"{count:3d} {name} {row['outcome']}")
                if row["outcome"] != "ok":
                    say(f"stopping on {row['outcome']}: {row.get('error', '')}")
                    return 1
                rows.append(row)
            values = [v for v in (primary(r) for r in rows) if v is not None]
            if repeat == 0 and spread_flag(values):
                say(f"{name}: spread above 10 % of the median, 3 more runs")
                continue
            break
    say(f"done: {count} processes")
    return 0


# ----------------------------------------------------------- unit readings


def proc_status(pid: int) -> dict[str, float]:
    fields: dict[str, float] = {}
    for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
        key, _, rest = line.partition(":")
        if key in ("VmRSS", "VmHWM", "VmSwap", "Threads"):
            fields[key] = float(rest.split()[0])
    return fields


def unit_readings(unit: str, label: str) -> int:
    shown = subprocess.run(
        ["systemctl", "show", "-p", "ControlGroup", "--value", unit],
        capture_output=True,
        text=True,
    )
    group = shown.stdout.strip()
    procs_file = Path("/sys/fs/cgroup" + group) / "cgroup.procs"
    if not group or not procs_file.is_file():
        say(json.dumps({"error": f"no cgroup for unit {unit}", "label": label}))
        return 0
    uptime = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
    ticks = os.sysconf("SC_CLK_TCK")
    for pid_text in procs_file.read_text(encoding="utf-8").split():
        pid = int(pid_text)
        try:
            if (
                not Path(f"/proc/{pid}/comm")
                .read_text(encoding="utf-8")
                .startswith("python")
            ):
                continue
            status = proc_status(pid)
            stat = (
                Path(f"/proc/{pid}/stat")
                .read_text(encoding="utf-8")
                .rsplit(")", 1)[1]
                .split()
            )
            rollup: dict[str, float] = {}
            for line in (
                Path(f"/proc/{pid}/smaps_rollup")
                .read_text(encoding="utf-8")
                .splitlines()
            ):
                key, _, rest = line.partition(":")
                if key in ("Rss", "Pss", "Private_Clean", "Private_Dirty"):
                    rollup[key] = float(rest.split()[0])
        except OSError as exc:
            say(json.dumps({"error": f"pid {pid}: {exc}", "label": label}))
            continue
        say(
            json.dumps(
                {
                    "label": label,
                    "pid": pid,
                    "vm_rss_mb": round(status.get("VmRSS", 0) / 1024, 1),
                    "vm_hwm_mb": round(status.get("VmHWM", 0) / 1024, 1),
                    "vm_swap_mb": round(status.get("VmSwap", 0) / 1024, 1),
                    "threads": int(status.get("Threads", 0)),
                    "smaps_rss_mb": round(rollup.get("Rss", 0) / 1024, 1),
                    "smaps_pss_mb": round(rollup.get("Pss", 0) / 1024, 1),
                    "smaps_private_mb": round(
                        (
                            rollup.get("Private_Clean", 0)
                            + rollup.get("Private_Dirty", 0)
                        )
                        / 1024,
                        1,
                    ),
                    "elapsed_s": round(uptime - int(stat[19]) / ticks),
                }
            )
        )
    return 0


# ---------------------------------------------------------------- selftest


def child_row(extra: list[str], cap: float) -> tuple[int, dict[str, Any] | None]:
    work = Path(tempfile.mkdtemp(prefix="memself_"))
    out = work / "row.jsonl"
    cmd = [sys.executable, str(Path(__file__)), "--point", "_fake", "--out", str(out)]
    cmd += ["--watchdog-mb", str(cap), "--guard-dirs", str(work / "guard")] + extra
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    rows = read_jsonl(out)
    return done.returncode, (rows[-1] if rows else None)


def selftest(cap: float) -> str | None:
    """Return the label of the first failing check, or None."""
    code, row = child_row(["--fake-mb", "60"], cap)
    delta = point_delta(row, "_fake") if row else None
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
    guard = Path(tempfile.mkdtemp(prefix="memguard_"))
    (guard / "a.txt").write_text("x")
    first = snapshot(guard)
    if changed_files(first, snapshot(guard)):
        return "(d)"
    time.sleep(0.01)
    (guard / "a.txt").write_text("xy")
    if changed_files(first, snapshot(guard)) != [str(guard / "a.txt")]:
        return "(d)"
    stats = summarize([100.0, 104.0, 108.0])
    flagged = spread_flag([100.0, 120.0, 100.0])
    if not (
        stats["median"] == 104.0 and stats["min"] == 100.0 and stats["max"] == 108.0
    ):
        return "(e)"
    if stats["flag"] or not flagged or spread_flag([100.0, 110.0, 105.0]):
        return "(e)"
    if partial_status(["ok", "capped", "ok"]) != "partial":
        return "(e)"
    if partial_status(["ok", "ok"]) != "ok" or partial_status(["capped"]) != "failed":
        return "(e)"
    done = subprocess.run(
        [sys.executable, str(Path(__file__)), "--unit-readings", "no-such-unit-xyz",
         "--label", "t"],
        capture_output=True,
        text=True,
    )  # fmt: skip
    first_line = done.stdout.splitlines()[0] if done.stdout else ""
    if "Traceback" in done.stderr or '"error"' not in first_line:
        return "(f)"
    return None


# -------------------------------------------------------------------- main


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--point")
    parser.add_argument("--book")
    parser.add_argument("--books", default="")
    parser.add_argument("--db", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--unit-readings")
    parser.add_argument("--label", default="")
    parser.add_argument("--selftest", action="store_true")
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
    if args.unit_readings:
        return unit_readings(args.unit_readings, args.label)
    if args.all:
        if not (args.db and args.out and args.books):
            say("--all needs --db, --out and --books")
            return 2
        return drive(args)
    if args.point and args.out:
        return run_child(args)
    say("nothing to do: give --point, --all, --unit-readings or --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
