# Review: trial replacement of kindlegen with kindling

Method: two independent fresh-context reviewers run in parallel —
(a) an adversarial line-by-line code review of the diff, with an instruction to
probe removed behaviour, subprocess handling, path correctness, template
consumers, test quality and project conventions; (b) a claims auditor whose job
was to re-derive every number in `research.md`, `spec.md`, `plan.md` and
`test_protocol.md` from the repo and the real tools, and to verify that every
Pāḷi word in the user-facing protocol actually resolves.

CodeRabbit was **not** run: it uploads the diff to an external service, and the
user has not been asked yet. Coverage below is from the two agent passes plus my
own re-verification. Every finding was re-checked against the code or the data
before being accepted — two were accepted only after I reproduced them myself.

## Findings acted on

1. **`--fold-accents` rationale in `research.md` §4 was wrong** (claims auditor;
   independently reproduced). The original text claimed the flag "loses real
   headwords", citing `thāna` and `ṭhana`. I re-parsed the rendered index:
   **neither word exists in the dictionary** — zero occurrences as headword or
   inflected form. What the "exact" column recorded as a success was a fuzzy
   fallback onto `thana` (breast), a different word. I then built a
   `--fold-accents` variant from the current render and compared: every real
   Pāḷi word resolves at the **identical text position** in both modes
   (`ṭhāna`, `dhammā`, `dhammassa`, `buddhaṃ`, `ariyasaccaṃ`, `okārassa`,
   `okkamati`, `bhikkhūti`, `evaṃvipāko`, `suffering`, `thana`).
   **Fixed:** §4 rewritten with the correction and the re-measured evidence.
   The recommendation (do not pass the flag) stands on different grounds —
   smaller output, better misspelled-query fallback — and the false claim is
   explicitly retracted in place so a later reader cannot act on it.
   `plan.md` had spotted the smoking gun ("resolves *via* `thana`") and filed
   it as a curiosity; that is now the refutation it always was.

2. **`.exists()` was the wrong guard on the binary** (code reviewer). A release
   asset fetched with a browser or `curl -O` lands mode 0644, which passes an
   existence check and then dies inside `Popen` with a bare `PermissionError` —
   defeating the friendly error the guard exists to give. This is the single
   most likely first-run state, since installing the binary requires a manual
   `chmod +x`. **Fixed:** one-line change to `os.access(path, os.X_OK)`.
   A longer error message naming the pinned release URL was written and then
   removed — the user asked for the simplest working proof of concept, and a
   download URL in a red line is not what makes this trial work.

3. **The new tests would stay green through several real breakages** (code
   reviewer, two separate defects). (a) `cast(ProjectPaths, SimpleNamespace(...))`
   is a runtime no-op, so the suite proved only that `make_mobi` reads the
   attribute names the test author chose — deleting or renaming
   `ProjectPaths.kindling_path` left every test passing while the real exporter
   died with `AttributeError`. Especially sharp here because this is a shared
   working tree where a concurrent session can revert a single line. (b) The
   fake `Popen` swallowed `**kwargs` unexamined, so dropping `text=True` (every
   build then fails on `escape(bytes)`) or dropping `stderr=STDOUT` was
   undetectable. **Fixed:** added a test that asserts the *real* `ProjectPaths`
   exposes `kindling_path`; the fake now captures kwargs and asserts
   `text`/`stdout`/`stderr`; a new test asserts the child's lines actually reach
   `pr.white`; and the unusable-binary test is parametrized over missing and
   mode-0644. 4 tests → 6.

4. **Stale research-era numbers presented as current fact** (claims auditor;
   re-derived myself). The July render's figures had leaked forward into
   documents describing the September build: `spec.md` said kindling indexes
   422,191 forms (it is **423,001**), and `test_protocol.md` — the one document
   the user reads — told them 88,500 of our forms are ambiguous (it is
   **88,775**; duplicate headwords are **10,046**, not 10,020).
   **Fixed:** all three corrected at every site, and `research.md` now opens
   with a snapshot warning stating its counts are superseded by `plan.md`.

5. **Two unit systems inside one document** (claims auditor). `plan.md`
   described the same two files as "71.7 MB / 38.2 MB" (MiB) in its comparison
   table and "75.2 MB / 40.1 MB" (MB) eleven lines later; `spec.md` promised
   ~71/~38 while the protocol said 75.2/40.1 — a phantom 4 MB gap for anyone
   cross-checking. **Fixed:** MB (10^6) everywhere, stated explicitly in
   `spec.md`.

6. **Undisclosed scope creep** (claims auditor). The spec authorised
   `epub:type="dictionary"` on `ebook_letter.jinja`; the diff also edited
   `ebook_epd_letter.jinja`. `OPF_078` needs only one such document, so it was
   not required. **Fixed:** the edit is kept — both templates emit real
   `<idx:entry>` content and marking only one would have been the inconsistent
   choice — but `spec.md` now records it as drift rather than leaving the spec
   silently contradicted by the diff.

7. **`exporter/kindle/README.md` documented kindlegen** (both reviewers). Now
   false on every platform. **Fixed**, including a pointer to where the pinned
   binary comes from.

8. **`test_protocol.md` misclassified `evaṃvipāko`** (claims auditor). Listed
   as a headword in the control group that exists to prove the dictionary works
   before the user trusts a failure elsewhere; it is an inflected form only
   (`orth=0, iform=1`). **Fixed:** moved to group 1. Also added the 3-section
   split to the protocol as something to test deliberately rather than by
   accident.

## Findings recorded, deliberately not fixed here

9. **The gitignored binary breaks the release pipeline — RESOLVED after review**
   (both reviewers, convergent; verified myself). `tools/configger.py:147` sets
   `make_ebook = yes` in the `github_release` profile, which
   `draft_release.yml` applies, so CI runs this exporter on every release. With
   `kindling-cli` gitignored and nothing fetching it, `make_mobi` now raises and
   aborts the whole exporter job — Kobo, TXT, tarball and every upload step
   included. The old `kindlegen` was git-tracked, so CI always had a compiler.
   Not fixed because the spec explicitly excludes binary acquisition and the CI
   workflow, and because the fix depends on a decision the user has not made
   (vendor vs fetch-with-checksum). **`spec.md` now states this deferral blocks
   merge rather than merely postponing tidiness.**

   **Resolved.** Benchmarked on a real runner (run 34754250894): downloading the
   pinned release asset takes 0.607 s against 200.8 s to `cargo install` it.
   `draft_release.yml` now fetches and checksum-verifies the binary before the
   Kindle export, and a smoke job proved the downloaded binary builds a
   dictionary on the runner. The blocker is gone; the full release workflow has
   still not been run end to end, which is noted in the plan.

10. **A missing binary is now fatal to the whole 17-step build chain** (code
    reviewer). `tools/script_runner.py` uses `check=True` + `sys.exit`, and the
    Kindle exporter is command 8 of 17, so a `make_mobi` failure now also skips
    the PDF/TXT/tarball/docs steps **and `config_uposatha_reset.py`**, leaving
    the config in its build profile. Honouring the exit code is what the spec
    asked for and is right; whether a Kindle failure should be fatal to the
    *chain* is a product decision, not a review fix. Flagged for the user.

11. **macOS is untested and now hard-fails** (code reviewer). Cross-platform
    parity is a headline benefit in the research, but nothing in this thread ran
    on macOS, and the binary installed is linux-x86_64. Finding 2's error
    message mitigates the confusion; it does not make the claim tested.

12. **The lookup check is structurally one-sided** (claims auditor). kindling
    cannot decode kindlegen's index (`"dhammassa" does not resolve` against the
    old artefact, with garbage first labels), so the "first automated
    correctness check" can only ever compare the new tool against itself. True,
    worth knowing, and not fixable — but it does undercut the "testable in CI"
    framing, so it is on record.

13. **No partial-retreat path is written down** (claims auditor). Four of the
    five changes — the validator fixes, honouring the exit code, the tests, and
    deleting the silent macOS no-op — are independently good and worth keeping
    even if kindling loses on the device. Nobody had recorded that. Raised with
    the user rather than resolved unilaterally.

14. **Minor, left alone:** `spell="yes"` is still emitted into all 189,505
    entries though kindling documents no spellchecker index (dead markup,
    harmless, but nobody decided to stop emitting it); `pth.kindlegen_path` now
    has no caller (intentional — the old artefact must stay buildable — but it
    will read as orphaned); the subprocess is not context-managed, so the pipe
    is left to the GC on the error path (pre-existing style, no deadlock or
    zombie hazard: single pipe, drained to EOF before `wait()`).

## Categories checked and found clean

- **Path correctness.** `ProjectPaths` absolutises `base_dir`, so all three argv
  entries are absolute and the command is cwd-independent; OPF manifest hrefs
  resolve relative to the OPF's own directory, which is where it sits.
- **Template consumers.** `xmlns:epub` was already declared in both templates
  (and `ebook_titlepage.jinja` has carried `epub:type` through years of
  kindlegen builds); the abbreviations page reusing `ebook_letter.jinja` is
  genuinely dictionary content; `Text/0_a.xhtml` is stable as the `<guide>`
  index target; no other code in the repo reads these files.
- **Removed behaviour.** Every caller of `make_mobi` and every reference to
  `kindlegen_path` swept repo-wide. Only `main()` calls it, correctly skipped
  for `--script`. The output path is byte-identical to the old one, so the
  release asset name is preserved.
- **Subprocess mechanics.** No deadlock, no zombie, no unflushed pipe.
- **Project conventions.** Modern type hints, `Path` over `os` for filepaths,
  no `sys.path` hacks, printer timers paired correctly, no ORM mutation, and
  both comments in `make_mobi` explain WHY.
- **Arithmetic.** The auditor could not find a single arithmetic error in
  `plan.md`; I re-derived 189,505 / 174,381 / 315,297 / 423,001 / 88,775 /
  10,046 independently and they match the tool's own output.

## Post-review verification

- `uv run ruff check --fix` / `ruff format` / `pyright` clean on every touched
  Python file.
- `just typecheck` (pyrefly, whole repo): **0 errors**.
- `uv run pytest tests/`: **1856 passed, 12 deselected**, 0 failures (up from
  1853 — three new tests).
- Every word in `test_protocol.md` re-verified to resolve in the shipped build.
- `--fold-accents` variant rebuilt from the current render solely to check
  finding 1; it is scratch only and is not a deliverable.

## Verdict

Pass. Everything the reviewers found inside the trial's remit is fixed and
re-verified. Finding 9 (binary acquisition) was the one blocker and is now
resolved: CI downloads and checksums the pinned release. The remaining merge
condition is the device test (open question 1), which the user has since run.
