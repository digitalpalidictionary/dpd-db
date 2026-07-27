"""Tests for the repo-wide pyrefly type-check gate (`just typecheck`).

Guards two things that break silently:
1. The pyrefly config drifting out of alignment with the pyright config.
2. The gate losing its teeth — passing code that has a real type error.
"""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
JUSTFILE = PROJECT_ROOT / "justfile"


def _tool_config(tool: str) -> dict[str, Any]:
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)["tool"][tool]


def _normalise_exclude(pattern: str) -> str:
    """Reduce a glob exclude to its bare path so pyright and pyrefly compare equal.

    pyright writes `gui2`, pyrefly writes `gui2/**` or `**/archive/**`.
    """
    return pattern.removeprefix("**/").removesuffix("/**").removesuffix("/*")


def _pyrefly_binary() -> str:
    found = shutil.which("pyrefly")
    if found:
        return found
    return str(Path(sys.prefix) / "bin" / "pyrefly")


def _run_pyrefly(target: Path, config: str | None) -> subprocess.CompletedProcess[str]:
    # PYTHONPATH pointing at another checkout makes pyrefly resolve the wrong
    # modules, so the subprocess gets a clean environment.
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    cmd = [_pyrefly_binary(), "check", "--output-format", "min-text"]
    if config is not None:
        cmd += ["--config", config]
    cmd.append(str(target))
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env
    )


def test_pyrefly_config_present() -> None:
    assert "pyrefly" in tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]


def test_pyrefly_python_version_matches_pyright() -> None:
    assert (
        _tool_config("pyrefly")["python-version"]
        == _tool_config("pyright")["pythonVersion"]
    )


def _sub_config_for(tree: str) -> dict[str, Any] | None:
    for sub in _tool_config("pyrefly").get("sub-config", []):
        if _normalise_exclude(sub["matches"]) == tree:
            return sub
    return None


def _effective_errors(tree: str) -> dict[str, bool]:
    """The error toggles that actually apply to ``tree``.

    A sub-config overlays the root ``[errors]`` table rather than replacing it, so
    reading the sub-config alone would miss a root-level toggle. Checking only the
    sub-config would let someone disable an import code repo-wide while the test
    guarding that code still passed.
    """
    merged: dict[str, bool] = dict(_tool_config("pyrefly").get("errors", {}))
    sub = _sub_config_for(tree)
    if sub is not None:
        merged.update(sub.get("errors", {}))
    return merged


def test_pyrefly_excludes_cover_every_pyright_exclude() -> None:
    """A tree pyright skips must be skipped by pyrefly too — or checked under a
    sub-config that turns the type-shape codes off, as tests/** is."""
    pyrefly_excludes = {
        _normalise_exclude(p) for p in _tool_config("pyrefly")["project-excludes"]
    }
    pyright_excludes = {
        _normalise_exclude(p) for p in _tool_config("pyright")["exclude"]
    }
    for tree in pyright_excludes - pyrefly_excludes:
        assert _sub_config_for(tree) is not None, (
            f"{tree} is checked by pyrefly with no sub-config"
        )
        silenced = [code for code, on in _effective_errors(tree).items() if on is False]
        assert silenced, f"{tree} is checked by pyrefly but silences nothing"


def test_tests_tree_is_still_checked_for_imports() -> None:
    """tests/** trades type-shape checking for import checking — losing the import
    half would re-open the hole that broke CI on 2026-07-27.
    """
    assert _sub_config_for("tests") is not None
    effective = _effective_errors("tests")
    for code in ("missing-module-attribute", "missing-import", "unbound-name"):
        assert effective.get(code, True) is True, f"{code} must stay on in tests/"


def test_typecheck_recipe_invokes_pyrefly() -> None:
    recipes = JUSTFILE.read_text(encoding="utf-8")
    assert "\ntypecheck:\n" in recipes
    body = recipes.split("\ntypecheck:\n", 1)[1].split("\n\n", 1)[0]
    assert "pyrefly check" in body


def test_gate_rejects_a_real_type_error(tmp_path: Path) -> None:
    """The whole point of the gate: bad code must fail it."""
    bad = tmp_path / "bad_sample.py"
    bad.write_text("def f(x: int) -> str:\n    return x\n", encoding="utf-8")

    result = _run_pyrefly(bad, config="pyproject.toml")

    assert result.returncode != 0
    assert "bad-return" in result.stdout


def test_gate_accepts_clean_code(tmp_path: Path) -> None:
    """Guards against the gate becoming so noisy it blocks correct code."""
    good = tmp_path / "good_sample.py"
    good.write_text("def f(x: int) -> str:\n    return str(x)\n", encoding="utf-8")

    result = _run_pyrefly(good, config="pyproject.toml")

    assert result.returncode == 0, result.stdout


def test_project_config_is_stricter_than_the_default_preset(tmp_path: Path) -> None:
    """The teeth come from [tool.pyrefly], not from pyrefly's own defaults.

    Run with no config, pyrefly falls back to preset `basic` and lets this error
    through. If someone weakens [tool.pyrefly] to match, the gate goes quiet
    without any test failing — this is what notices.
    """
    bad = tmp_path / "bad_sample.py"
    bad.write_text("def f(x: int) -> str:\n    return x\n", encoding="utf-8")

    assert _run_pyrefly(bad, config=None).returncode == 0
    assert _run_pyrefly(bad, config="pyproject.toml").returncode != 0
