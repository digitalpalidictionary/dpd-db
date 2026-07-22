"""Tests for the incremental re-check cache and TSV queue merge in proofreader."""

import threading
import time

from tools.proofreader import (
    ProofreaderManager,
    apply_checked_item,
    build_corrected_by_id,
    filter_unchecked,
    load_checked_cache,
    load_tsv_queue,
    save_checked_cache,
    save_tsv_queue,
    tsv_lock,
)


def test_load_checked_cache_missing_file(tmp_path) -> None:
    cache_path = tmp_path / "checked.json"
    assert load_checked_cache(cache_path) == {}


def test_checked_cache_round_trip(tmp_path) -> None:
    cache_path = tmp_path / "checked.json"
    cache = {"1": "meaning one", "2": "meaning two"}
    save_checked_cache(cache_path, cache)
    assert load_checked_cache(cache_path) == cache


def test_checked_cache_broken_json(tmp_path) -> None:
    cache_path = tmp_path / "checked.json"
    cache_path.write_text("not json", encoding="utf-8")
    assert load_checked_cache(cache_path) == {}


def test_load_tsv_queue_missing_file(tmp_path) -> None:
    tsv_path = tmp_path / "proofreader.tsv"
    assert load_tsv_queue(tsv_path) == {}


def test_tsv_queue_round_trip(tmp_path) -> None:
    tsv_path = tmp_path / "proofreader.tsv"
    queue = {
        "1": {
            "id": "1",
            "lemma_1": "test1",
            "meaning_1": "old1",
            "meaning_1_corrected": "new1",
        },
        "2": {
            "id": "2",
            "lemma_1": "test2",
            "meaning_1": "old2",
            "meaning_1_corrected": "new2",
        },
    }
    save_tsv_queue(tsv_path, queue)
    assert load_tsv_queue(tsv_path) == queue


def test_filter_unchecked_skips_unchanged() -> None:
    data = [
        {"id": 1, "lemma_1": "a", "meaning_1": "meaning one"},
        {"id": 2, "lemma_1": "b", "meaning_1": "meaning two"},
    ]
    checked_cache = {"1": "meaning one", "2": "meaning two"}
    assert filter_unchecked(data, checked_cache) == []


def test_filter_unchecked_keeps_new_and_edited() -> None:
    data = [
        {"id": 1, "lemma_1": "a", "meaning_1": "meaning one edited"},
        {"id": 2, "lemma_1": "b", "meaning_1": "meaning two"},
        {"id": 3, "lemma_1": "c", "meaning_1": "meaning three (never checked)"},
    ]
    checked_cache = {"1": "meaning one", "2": "meaning two"}
    result = filter_unchecked(data, checked_cache)
    assert [d["id"] for d in result] == [1, 3]


def test_apply_checked_item_merge_preserves_untouched_replaces_stale() -> None:
    """Exercises the real apply_checked_item used by main(): id 1 is
    re-checked (correction found), id 2 is re-checked (now clean, stale
    queued row should be dropped), id 3 is never touched this run and its
    pending row must survive untouched."""
    tsv_queue = {
        "1": {
            "id": "1",
            "lemma_1": "a",
            "meaning_1": "old text",
            "meaning_1_corrected": "old correction",
        },
        "2": {
            "id": "2",
            "lemma_1": "b",
            "meaning_1": "old text",
            "meaning_1_corrected": "old correction",
        },
        "3": {
            "id": "3",
            "lemma_1": "c",
            "meaning_1": "unchanged text",
            "meaning_1_corrected": "still pending",
        },
    }
    checked_cache = {}

    apply_checked_item(
        tsv_queue,
        checked_cache,
        {"id": 1, "lemma_1": "a", "meaning_1": "new text"},
        corrected_meaning="new correction",
    )
    apply_checked_item(
        tsv_queue,
        checked_cache,
        {"id": 2, "lemma_1": "b", "meaning_1": "new clean text"},
        corrected_meaning="",  # re-checked, found clean this time -> no new row
    )

    assert tsv_queue["1"]["meaning_1_corrected"] == "new correction"
    assert "2" not in tsv_queue
    assert tsv_queue["3"]["meaning_1_corrected"] == "still pending"
    assert checked_cache == {"1": "new text", "2": "new clean text"}


def test_apply_checked_item_no_row_when_echoed_same_meaning() -> None:
    """A model that just echoes the input back (no real fix) must not create
    a no-op queue row."""
    tsv_queue = {}
    checked_cache = {}
    item = {"id": 5, "lemma_1": "x", "meaning_1": "already correct"}

    apply_checked_item(
        tsv_queue, checked_cache, item, corrected_meaning="already correct"
    )

    assert tsv_queue == {}
    assert checked_cache == {"5": "already correct"}


def test_build_corrected_by_id_normalizes_int_and_str_ids() -> None:
    """The model may echo id back as either an int or a string — both must
    key into the same normalized-to-str dict."""
    corrected_batch = [
        {"id": 1, "meaning_1_corrected": "fix one"},
        {"id": "2", "meaning_1_corrected": "fix two"},
    ]
    result = build_corrected_by_id(corrected_batch)
    assert result == {"1": "fix one", "2": "fix two"}


def test_tsv_queue_sorted_by_id(tmp_path) -> None:
    tsv_path = tmp_path / "proofreader.tsv"
    queue = {
        "10": {
            "id": "10",
            "lemma_1": "b",
            "meaning_1": "old",
            "meaning_1_corrected": "new",
        },
        "2": {
            "id": "2",
            "lemma_1": "a",
            "meaning_1": "old",
            "meaning_1_corrected": "new",
        },
    }
    save_tsv_queue(tsv_path, queue)
    text = tsv_path.read_text(encoding="utf-8")
    assert text.index("\n2\t") < text.index("\n10\t")


def test_tsv_lock_serializes_concurrent_access(tmp_path) -> None:
    """Two threads racing to reload-mutate-save the same queue under the lock
    must not lose either update — the classic bug this lock exists to prevent."""
    tsv_path = tmp_path / "proofreader.tsv"
    save_tsv_queue(
        tsv_path,
        {
            "1": {
                "id": "1",
                "lemma_1": "a",
                "meaning_1": "m1",
                "meaning_1_corrected": "c1",
            },
            "2": {
                "id": "2",
                "lemma_1": "b",
                "meaning_1": "m2",
                "meaning_1_corrected": "c2",
            },
        },
    )

    def pop_one(id_to_pop):
        with tsv_lock(tsv_path):
            queue = load_tsv_queue(tsv_path)
            time.sleep(0.05)  # widen the race window
            queue.pop(id_to_pop, None)
            save_tsv_queue(tsv_path, queue)

    t1 = threading.Thread(target=pop_one, args=("1",))
    t2 = threading.Thread(target=pop_one, args=("2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    remaining = load_tsv_queue(tsv_path)
    assert remaining == {}


def test_proofreader_manager_get_next_correction_locked_against_external_writer(
    tmp_path,
) -> None:
    """A concurrent writer holding the lock must block get_next_correction
    until it releases — proving PRead and the CLI run can't clobber each other."""
    tsv_path = tmp_path / "proofreader.tsv"
    save_tsv_queue(
        tsv_path,
        {
            "1": {
                "id": "1",
                "lemma_1": "a",
                "meaning_1": "m1",
                "meaning_1_corrected": "c1",
            },
            "2": {
                "id": "2",
                "lemma_1": "b",
                "meaning_1": "m2",
                "meaning_1_corrected": "c2",
            },
        },
    )

    lock_held = threading.Event()
    release_lock = threading.Event()

    def hold_lock():
        with tsv_lock(tsv_path):
            lock_held.set()
            release_lock.wait(timeout=5)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert lock_held.wait(timeout=5)

    manager = ProofreaderManager(tsv_path)
    result = {}

    def try_get_next():
        result["correction"], result["remaining"] = manager.get_next_correction()

    getter = threading.Thread(target=try_get_next)
    getter.start()
    time.sleep(0.1)
    assert getter.is_alive()  # still blocked on the lock

    release_lock.set()
    holder.join()
    getter.join(timeout=5)

    assert result["correction"]["id"] == "1"
    assert result["remaining"] == 1
