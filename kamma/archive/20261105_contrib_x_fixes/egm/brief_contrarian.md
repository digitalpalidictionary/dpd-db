# Request: contrib_x_fixes

The Digital Pāḷi Dictionary project has a desktop editing app (folder `gui2/`) and a contributor web server (scripts in `scripts/server_contrib/`). A triage left twelve small fixes. The owner wants one thread to do them.

## Hypothesis

The fixes are small and need no new design. One thread does them in order, one task each, with a test where the fix has behaviour. Two bigger items (audio in the preview on desktop, and a contributor changing their own password) move to separate threads.

## The fixes

1. Pass2 Add screen: wrap both clipboard copy calls so a refused copy never stops the rest of a save.
2. Make the preview folder before the app starts.
3. Skip the decon cache save quietly when the database is read-only.
4. Remove the helper web server start from gui2, with its dead code and tests.
5. Renaming an inflection pattern must mark the word cache stale.
6. Remove an unused additions manager from the Pass1 Add controller.
7. The daily pull sends a desktop notice on every "editor open" skip.
8. The nightly server window deletes the old database copy and the temporary git checkout after a good run only.
9. Make two username checks in gui2 agree when no username is set.
10. Read-only tabs: grey out the Save Changes button instead of showing a message.
11. DB tab: contributor starter preset is one filter, `lemma_1`, and shows columns id, pos, grammar, meaning_1, meaning_2, meaning_lit.
12. Turn the Alt shortcuts off in the web version only. The desktop keeps them.
13. Investigate one flaky test in `tests/scripts/server_contrib/test_maintenance_window.py`.
