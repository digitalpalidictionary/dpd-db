# Handoff — 20261122_variants_show_all (2026-11-22)

## State
- Every task in `plan.md` is `[x]`, including Phase 6 (the link look the owner chose after review). `review.md` says PASSED.
- **Nothing is committed.** The shared tree is checked out on the PR branch `webapp-variants-show-more` (fork `kirill-morozov-n/dpd-db`; `pushremote` = the fork URL; HEAD = the author's commit `430b5938`), with all of this thread's work uncommitted on top.
- Do not switch this tree back to `main` while the work is uncommitted. Several files differ between the two branches, so the checkout would refuse or carry the work across. Do not run another thread in this checkout until this one is committed.
- The owner's GoldenDict folder (`<GoldenDict dir>/dpd-variants`) holds the latest link-look build. The variants exporter's `copy_dir` always replaces it.

## Next steps
1. Optional: the owner looks at "ca" in DPD Variants in GoldenDict once (restart GoldenDict first) to confirm the link look.
2. Run `/kamma:4-finalize` on this thread. Skip the GitHub issue step (project rule). Record lessons, for example: the variants exporter writes into the GoldenDict folder even from a scratch run; and happy-dom gives `import.meta.url` a non-file scheme.
3. Only on the owner's go-ahead, follow "After finalize" in `plan.md`. Commit by explicit path, including the four untracked files: `exporter/goldendict/javascript/variants.js`, `exporter/wxt_extension/utils/variants.ts`, `exporter/wxt_extension/tests/utils/variants.test.ts` and `exporter/wxt_extension/tests/fixtures/variants_folded.html`, plus this thread folder. Then `git pull --ff-only`, the dry-run push gate to the fork, the push, and `gh pr merge 299 --merge --subject "#99 webapp: fold long variant lists behind a show all button (#299)"`. Then `git checkout main && git pull --ff-only`.
4. After the merge, the owner deploys dpdict.net and releases the extension (`just wxt-bump`), in either order.

## Known, not this thread's
- `tests/tools/test_docs_update_abbreviations.py::test_make_abbreviations_md_golden_master` fails on its frozen fixture ("three gender" against the data's "three genders").
- The lookup key `ootnote` (828 variant rows) is probably "footnote" with its first letter lost in the variant extraction. It is a candidate for its own thread.
