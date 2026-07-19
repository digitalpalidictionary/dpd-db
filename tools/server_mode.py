"""Detect a headless gui2 server session (a web contributor instance) so that
desktop-only shell-outs (browser pop-ups, GoldenDict, the local webapp helper)
can be suppressed. Desktop behaviour is unchanged: neither the env var nor the
config option is set there, so every helper returns False / None."""

import os

from tools.configger import config_read


def resolve_role() -> str | None:
    """Active gui2 role: DPD_GUI2_ROLE env override → config.ini [gui2] role.

    Single source of truth so button-hiding (gui2.user.is_server_contributor)
    and shell-out gating (is_headless_server) can never disagree. Returns None
    when neither is set — the legacy desktop role. Mirrors resolve_username."""
    return os.environ.get("DPD_GUI2_ROLE") or config_read("gui2", "role")


def is_headless_server() -> bool:
    """True when this process is a contributor-server gui2 web instance.

    Uses resolve_role() so it honours the config.ini fallback too — a server
    whose role is set in config (not the env var) still suppresses shell-outs.
    Desktop / primary sessions resolve to None, so this is False and shell-outs
    behave exactly as before."""
    return resolve_role() == "contributor-server"
