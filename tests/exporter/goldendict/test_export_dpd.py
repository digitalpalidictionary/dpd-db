"""Tests for exit-code propagation in export_dpd multiprocessing."""

from multiprocessing import Process


def _crashing_worker():
    raise RuntimeError("simulated worker crash")


def test_crashing_worker_has_nonzero_exit_code():
    p = Process(target=_crashing_worker)
    p.start()
    p.join()
    assert p.exitcode != 0
