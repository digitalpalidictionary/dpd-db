# Review — pass1 removals sync

**Verdict: PASSED** (owner asked to finalize after the reviews below, 2026-11-12)

## Files Changed
- gui2/pass1_auto_controller.py, gui2/pass1_file_manager.py
- scripts/server_contrib/contrib_pull.py, scripts/server_contrib/README.md
- kamma/tech.md, AGENTS.md (CLAUDE.md link target)
- tests/gui2/test_pass1_auto_controller.py, tests/gui2/test_pass1_file_manager.py
- tests/scripts/server_contrib/test_contrib_pull.py, tests/scripts/server_contrib/test_contrib_reconcile.py

## Findings
- CodeRabbit (free CLI, 1 finding): book-file rewrite is not atomic. Spec accepts the risk; owner judged it minimal. Not changed.
- pi deepseek-flash (thinking off): the push-file-set test was vacuous (real, fixed); non-object book file raises an uncaught AttributeError (unlikely, not changed); gui2 and the pull differ on odd words (not changed); pasted-text book claim rejected (laptop-only untracked file, covered by the re-draft guard); two doc/test nits not changed.

## Fixes Applied
- Push test now asserts PULL_ONLY_KINDS is disjoint from DELIVERED_KINDS and that delivered_files ignores a list. Reverted-check: adding the kind to DELIVERED_KINDS fails it.

## Test Evidence
- `uv run pytest tests/scripts/server_contrib tests/gui2 tests/tools -q`: 2010 passed, 7 deselected.
- `just typecheck`: 0 errors. ruff and pyright clean on every touched file.
- Delete step switched off: 2 pull tests fail. Server view reverted to own-list only: 1 test fails.
