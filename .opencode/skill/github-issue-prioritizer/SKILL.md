---
name: github-issue-prioritizer
description: Fetch all open GitHub issues and determine the most important one to work on next based on priority signals
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: github-issues
---

## What I do

I fetch all open GitHub issues from the specified repository and determine which issue should be worked on next by analyzing priority signals.

## Priority Ranking Criteria

Issues are ranked by the following weighted factors (highest priority first):

1. **Critical Labels** - Issues with "bug", "critical", "urgent", "high-priority", "p0", "severity/critical" labels get highest priority
2. **Reactions** - Issues with more "+1" or emoji reactions indicate community interest
3. **Comments** - More discussion suggests active interest or complexity
4. **Age** - Older unaddressed issues may be more important to resolve
5. **Assignee Status** - Unassigned issues may need attention; assigned issues with no recent activity may be blocked
6. **Milestone Proximity** - Issues close to current milestone deadline

## How to use me

1. Fetch the repository issues using the GitHub CLI or API
2. Call this skill with the repository context
3. I'll analyze and rank all open issues
4. Return the top-priority issue with reasoning

## Input Format

When calling this skill, provide:
- Repository (owner/repo format)
- Optional: Number of top issues to return (default: 1)
- Optional: Specific labels to filter by
- Optional: Milestone context

## Output Format

I return:
1. The single most important issue to work on next
2. Top 3-5 alternative issues with brief justification
3. Detailed ranking rationale with priority score breakdown

## Required Tools

To use this skill effectively, the agent needs:
- `git` - to get repository URL (`git remote get-url origin`)
- `curl` - to call GitHub REST API for fetching issues
- File read/write permissions for logging/scoring cache
- Repository context awareness

## Notes

- Unlabeled issues are ranked lower than labeled ones
- Closed issues are excluded from analysis
- Draft PRs linked to issues may affect priority
- The skill weights can be adjusted based on team preferences
