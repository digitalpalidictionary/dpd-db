# -*- coding: utf-8 -*-
"""Jinja2 environment setup utility for DPD exporters.

This module provides a centralized way to create and configure Jinja2
environments with consistent settings across all exporters.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_jinja2_env(
    templates_dir: Path | str,
    autoescape: bool = True,
    trim_blocks: bool = True,
    lstrip_blocks: bool = True,
    **env_options: Any,
) -> Environment:
    """Create a configured Jinja2 environment.

    Args:
        templates_dir: Path to the directory containing templates.
        autoescape: Whether to enable auto-escaping for HTML/XML. Defaults to True.
        trim_blocks: Whether to trim first newline after a block. Defaults to True.
        lstrip_blocks: Whether to strip leading whitespace before blocks. Defaults to True.
        **env_options: Additional options to pass to Jinja2 Environment.

    Returns:
        A configured Jinja2 Environment instance.
    """
    templates_path = Path(templates_dir)

    loader = FileSystemLoader(str(templates_path))

    env_kwargs: dict[str, Any] = {
        "loader": loader,
        "trim_blocks": trim_blocks,
        "lstrip_blocks": lstrip_blocks,
    }

    if autoescape:
        env_kwargs["autoescape"] = select_autoescape(["html", "xml"])

    env_kwargs.update(env_options)

    env = Environment(**env_kwargs)

    return env


def get_webapp_jinja2_env() -> Environment:
    """Create a Jinja2 environment configured for the webapp exporter.

    Returns:
        A Jinja2 Environment configured with webapp templates directory.
    """
    from tools.paths import ProjectPaths

    pth = ProjectPaths()
    return create_jinja2_env(pth.webapp_templates_dir)
