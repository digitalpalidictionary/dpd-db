# Plan — PR #279 review and TPR handover

PR: https://github.com/digitalpalidictionary/dpd-db/pull/279. Spec: `spec.md`.

## Architecture Decisions

- No DPD code changes in this thread. The PR is answered, not merged or closed.
- The removal of TPR from DPD is a separate, later thread. It starts only when the author confirms his build works.

## Phase 1 — Reply

- [x] Post the final reply on PR #279 as `bdhrs`, no signature, PR stays open. Body: the posted file `pr279_reply.md` (scratchpad), approved by the owner on 2026-11-03.
  → verify: `gh pr view 279 -R digitalpalidictionary/dpd-db --json state,comments` shows state `OPEN` and the last comment by `bdhrs`, starting "Thanks Bhante."
  → done 2026-11-03: https://github.com/digitalpalidictionary/dpd-db/pull/279#issuecomment-6601345237, state `OPEN`, author `bdhrs`.

> Finalized 2026-11-03 after phase 1. Phases 2 and 3 are deferred: they wait on the author, and the removal is its own new thread. The memory note `project_tpr_handover` records the handover for future sessions.

## Phase 2 — Wait (owner)

- [ ] Owner tells the agent when the author reports that his build is up and working.
  → verify: owner message.

## Phase 3 — Follow-up thread

- [ ] Open a new kamma thread to take TPR out of DPD, using the removal scope in `spec.md`.
  → verify: the new thread directory exists with its own spec.md.
