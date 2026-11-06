# Spec: a contributor changes their own password (placeholder)

**Thread:** 20261105_contrib_password_change
**Date:** 2026-11-05
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Status:** PLACEHOLDER. Basics only, to be filled in by `/kamma:1-plan` later.
Nothing here is decided or scheduled.

## Problem (from the 20261030 triage, item 15; owner decision: wants it)

Contributor login is nginx basic auth today. Passwords are set by the
maintainer through `scripts/server_contrib/add_contributor.sh`; a contributor
who wants a new password must ask. The owner wants contributors to change
their own password.

## Wanted (rough, owner to confirm at planning)

- A feature, not a fix: it needs its own design and spec.
- Open questions for planning: where the password lives (htpasswd files vs
  something else), which page offers the change, how nginx is reloaded, and
  whether the maintainer keeps an override.

## What's not included

- Audio in the preview (`20261105_contrib_audio_preview`).
- Any change to the maintainer's own credentials or to ssh access.
