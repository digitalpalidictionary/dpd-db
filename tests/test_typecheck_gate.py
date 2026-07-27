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

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
JUSTFILE = PROJECT_ROOT / "justfile"


def _tool_config(tool: str) -> dict:
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


def test_pyrefly_excludes_cover_every_pyright_exclude() -> None:
    """A tree pyright is told to skip must not be type-checked by pyrefly either."""
    pyrefly_excludes = {
        _normalise_exclude(p) for p in _tool_config("pyrefly")["project-excludes"]
    }
    pyright_excludes = {
        _normalise_exclude(p) for p in _tool_config("pyright")["exclude"]
    }
    assert pyright_excludes <= pyrefly_excludes


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
