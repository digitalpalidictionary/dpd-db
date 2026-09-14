"""Tests for make_mobi: it must invoke kindling with the OPF (never the epub,
whose size trips the PalmDB record limit), keep Kindle Publishing Guidelines
validation on, never pass the Pali-breaking --fold-accents, and surface a
failing build instead of reporting success."""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from exporter.kindle import kindle_exporter
from tools.paths import ProjectPaths


class _FakeProcess:
    def __init__(self, returncode: int) -> None:
        self.stdout = iter(["building\n", "done\n"])
        self._returncode = returncode

    def wait(self) -> int:
        return self._returncode


def _paths(tmp_path: Path, mode: int | None = 0o755) -> ProjectPaths:
    binary = tmp_path / "kindling-cli"
    if mode is not None:
        binary.write_text("")
        binary.chmod(mode)
    return cast(
        ProjectPaths,
        SimpleNamespace(
            kindling_path=binary,
            epub_content_opf_path=tmp_path / "content.opf",
            dpd_mobi_path=tmp_path / "dpd-kindle.mobi",
        ),
    )


def _capture(
    monkeypatch: pytest.MonkeyPatch, returncode: int = 0
) -> list[tuple[list[str], dict[str, Any]]]:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_popen(command: list[str], **kwargs: Any) -> _FakeProcess:
        calls.append((command, kwargs))
        return _FakeProcess(returncode)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    return calls


def test_project_paths_really_exposes_kindling_path() -> None:
    """The other tests fake ProjectPaths, so without this one a rename or a
    revert of the real attribute would leave the whole file green."""
    assert ProjectPaths().kindling_path.name == "kindling-cli"


def test_make_mobi_builds_from_the_opf_into_the_mobi_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pth = _paths(tmp_path)
    calls = _capture(monkeypatch)

    kindle_exporter.make_mobi(pth)

    assert len(calls) == 1
    command, _ = calls[0]
    assert command[0] == str(pth.kindling_path)
    assert command[1] == "build"
    assert command[2] == str(pth.epub_content_opf_path)
    assert command[3:] == ["-o", str(pth.dpd_mobi_path)]
    assert not any(arg.endswith(".epub") for arg in command)


def test_make_mobi_keeps_validation_on_and_accent_folding_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _capture(monkeypatch)

    kindle_exporter.make_mobi(_paths(tmp_path))

    command, _ = calls[0]
    assert "--no-validate" not in command
    assert "--fold-accents" not in command


def test_make_mobi_decodes_and_merges_the_child_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without text=True the stream yields bytes and rich's escape() raises on
    the first line; without the stderr merge the diagnostics bypass pr.white."""
    calls = _capture(monkeypatch)
    printed: list[str] = []
    monkeypatch.setattr(kindle_exporter.pr, "white", lambda line: printed.append(line))

    kindle_exporter.make_mobi(_paths(tmp_path))

    _, kwargs = calls[0]
    assert kwargs["text"] is True
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.STDOUT
    assert printed == ["building", "done"]


@pytest.mark.parametrize("mode", [None, 0o644], ids=["missing", "not-executable"])
def test_make_mobi_raises_on_an_unusable_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: int | None
) -> None:
    """0o644 is how a downloaded release asset arrives before chmod +x."""
    calls = _capture(monkeypatch)

    with pytest.raises(FileNotFoundError):
        kindle_exporter.make_mobi(_paths(tmp_path, mode=mode))

    assert calls == []


def test_make_mobi_raises_on_a_non_zero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture(monkeypatch, returncode=1)

    with pytest.raises(RuntimeError):
        kindle_exporter.make_mobi(_paths(tmp_path))
