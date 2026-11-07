# Independent review prompt — thread 20261107_pass1auto_unknown_first

You are an independent reviewer with zero memory of the implementation session.
Review the kamma thread at:

kamma/threads/20261107_pass1auto_unknown_first/

Follow kamma-3-review sections 4.0–6.0. Load and read:
- kamma/threads/20261107_pass1auto_unknown_first/spec.md
- kamma/threads/20261107_pass1auto_unknown_first/plan.md
- kamma/workflow.md
- kamma/project.md
- kamma/tech.md

The implementation is UNCOMMITTED in the working tree. Files changed BY THIS
THREAD ONLY:
- gui2/pass1_auto_controller.py
- tests/gui2/test_pass1_auto_controller.py
- kamma/threads/20261107_pass1auto_unknown_first/plan.md (checkboxes)

IMPORTANT: gui2/books.py and tests/gui2/test_books.py are also modified in the
tree by ANOTHER concurrent session — they are NOT part of this thread. Exclude
them from the diff review entirely. Use `git diff gui2/pass1_auto_controller.py
tests/gui2/test_pass1_auto_controller.py` as the thread's diff.

Review each changed file across: correctness (vs spec.md), readability,
architecture, security, performance. Check the check, not just its result:
verify the test run covers the behaviours the spec's "How we'll know it's done"
section names (unknown first, group order kept, text run unchanged). Run:
- uv run pytest tests/gui2/test_pass1_auto_controller.py -q
- uv run ruff check gui2/pass1_auto_controller.py tests/gui2/test_pass1_auto_controller.py
- uv run pyright --project /dev/null gui2/pass1_auto_controller.py tests/gui2/test_pass1_auto_controller.py

Report findings back (do NOT write review.md yourself): severity blocking /
major / minor / nit, file:line, what, why, recommended fix. Also state
coverage and residual risk explicitly. If no findings, say so explicitly.
