# Spec: audio in the preview (placeholder)

**Thread:** 20261105_contrib_audio_preview
**Date:** 2026-11-05
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Status:** PLACEHOLDER. Basics only, to be filled in by `/kamma:1-plan` later.
Nothing here is decided or scheduled.

## Problem (from the 20261030 triage, item 8; owner decision: desktop only)

The saved preview page (`gui2/assets/preview/`) has a play-audio request
(`/audio/<word>`, `exporter/webapp/main.py:348`), but nothing serves it: the
preview is a static file, not the webapp. On the desktop the button does
nothing. The audio database behind the endpoint is about 1.2 GB.

## Wanted (rough, owner to confirm at planning)

- Desktop only: the button works in the saved preview on the laptop.
- Hide the button on the contributor server, and for words with no audio.
- A new word has no audio until the next build.
- Owner wants to hear what problems come up before a design is chosen
  (how gui2 serves or embeds the audio for a static page).

## Constraints carried over from the triage

- Needs a design decision before code.
- Separate from the contributor server: never loads the audio db there.

## What's not included

- The contributor password change (`20261105_contrib_password_change`).
- Anything about the audio build pipeline or mp3 generation.
