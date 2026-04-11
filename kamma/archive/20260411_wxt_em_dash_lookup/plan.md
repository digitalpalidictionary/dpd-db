# plan.md

## Phase 1: Confirm and implement the normalization fix
- [x] Inspect `exporter/wxt_extension/utils/utils.ts` and confirm the current `PUNCTUATION_REGEX` does not remove the em dash used in failing selections like `jīvitindriyaṁ—`.
- [x] Update the word-cleaning logic in `exporter/wxt_extension/utils/utils.ts` so the em dash is removed during lookup normalization.
- [x] Re-read `exporter/wxt_extension/entrypoints/content.ts` to confirm the cleaned value is still the value sent to `/search_json?q=`.
- [x] Verify Phase 1 automatically by checking the changed code paths and ensuring the fix is limited to lookup normalization.

## Phase 2: Validate the extension build surface
- [x] Run the existing TypeScript verification command for the extension from `exporter/wxt_extension`: `npm run compile`.
- [x] If compilation reports issues caused by the change, fix them and rerun verification.
- [x] Verify Phase 2 automatically by confirming the compile command completes successfully.

## Phase 3: Prepare thread records and handoff
- [x] Write the approved `spec.md` and `plan.md` into `kamma/threads/<thread_id>/`.
- [x] Keep `plan.md` updated in-place as tasks move from `[ ]` to `[~]` to `[x]`.
- [x] After implementation, provide exact manual test steps for selecting a word ending with `—` in the browser extension and confirming results appear.
- [x] Verify Phase 3 automatically by re-reading the thread files and ensuring they match the completed work.
