# Plan: DB Tab Horizontal Scroll and Column Widths

## Phase 1: Fix layout and column sizing

- [x] Remove `width=1350` from `table_container` in `_create_results_section`
  → verify: horizontal scrollbar appears in DB tab when columns exceed viewport

- [x] Replace proportional column width formula with per-column content-based sizing
  → verify: columns are as wide as their content, not compressed

- [x] Set minimum column width to 120px
  → verify: short-content columns like "origin" and "pattern" are not squeezed
