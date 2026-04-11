# spec.md

## Overview
Fix a lookup bug in `exporter/wxt_extension` where selected words that end with an em dash are not found by the extension search flow. A concrete failing example is `jīvitindriyaṁ—`, which should be normalized to `jīvitindriyaṁ` before the extension sends the lookup request.

## What it should do
- Strip trailing and embedded dash punctuation used as surrounding punctuation from selected text before lookup.
- Ensure the existing word-cleaning path in the WXT content script handles an em dash (`—`) the same way it already handles ASCII hyphen-like punctuation.
- Preserve the current behavior for other punctuation removal and lowercasing.
- Keep the lookup request path unchanged apart from receiving the corrected cleaned query.

## Constraints
- Work only within the existing WXT extension code under `exporter/wxt_extension/`.
- Keep the change minimal and localized if possible.
- Do not change unrelated extension behavior such as panel rendering, theme handling, or request routing.
- Use the existing TypeScript build verification already defined in `exporter/wxt_extension/package.json` (`npm run compile`) rather than introducing new tooling.
- The repo is an existing multi-target exporter project, so the fix should not affect other exporters.

## How we'll know it's done
- `cleanWord()` removes an em dash from input like `jīvitindriyaṁ—`.
- The content script continues to pass cleaned text into `/search_json?q=...`.
- TypeScript compilation for `exporter/wxt_extension` succeeds.
- The implementation is documented in the Kamma thread files and ready for manual extension testing.

## What's not included
- No redesign of selection expansion behavior.
- No broader Unicode normalization pass beyond the punctuation needed for this bug.
- No changes to server-side search behavior or database content.

## Relevant repo context
- The extension content script entrypoint is `exporter/wxt_extension/entrypoints/content.ts`.
- The current normalization logic is in `exporter/wxt_extension/utils/utils.ts`, where `cleanWord()` uses `PUNCTUATION_REGEX` before lookups are sent.
- `content.ts` calls `cleanWord(word)` and then requests `/search_json?q=` with the cleaned value.
- The extension is a TypeScript WXT project with a `compile` script defined in `exporter/wxt_extension/package.json`.
- Current regex already removes ASCII hyphen `-` and several quotes/punctuation characters, but it does not currently include the em dash character shown in the failing example.
