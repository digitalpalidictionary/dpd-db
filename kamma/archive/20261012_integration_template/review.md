# Review: "Add Your App" integration template page

Date: 2026-10-12. Reviewer: independent subagent (read-only). CodeRabbit skipped at user's request.

## Findings (all fixed)
1. Minor: Easy Way prompt did not say where to write the answers. Added "write into add_your_app.md, keeping every heading" and a fallback for agents without web access.
2. Minor: "How to Send It" step 1 did not fit developers who used the AI. Added "If you used the easy way, skip to step 3."
3. Nit: bare example URLs read like answers. Now "For example: `...`".
4. Nit: "Tick all that apply" on a plain bullet list. Now "Keep the ones that apply".

## Coverage
- Checked: spec coverage of every listed item, markdown vs enabled extensions, in-page anchor slugs, nav YAML placement, spelling consistency, URL shape.
- After fixes: `mkdocs build` exit 0, only the pre-existing README.md/index.md warning.
- Not checked: rendered page in a real browser on the live site; the Easy Way URL works only after deploy.

Verdict: pass.
