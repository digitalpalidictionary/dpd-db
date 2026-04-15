# Spec: DB Tab Horizontal Scroll and Column Widths

## Overview
Fix the DB tab DataTable in gui2 to support horizontal scrolling and display columns at natural widths.

## What it should do
- Enable horizontal overflow so columns beyond the visible viewport can be scrolled to
- Size each column by its own content length, not by proportional distribution of a fixed total
- Cap column width at 500px (content wraps beyond that)
- Enforce a 120px minimum so short-content columns are not squeezed

## Assumptions & uncertainties
- The `ft.Row` with `scroll=ft.ScrollMode.AUTO` wrapping the table container was already present — only the fixed `width=1350` needed removing to activate it
- Character-to-pixel ratio of 8px per character is a reasonable approximation for size-12 monospace text

## Constraints
- Only `gui2/filter_component.py` touched

## How we'll know it's done
- Horizontal scrollbar appears when columns exceed viewport
- Short-content columns (e.g. "origin", "pattern") are at least 120px wide
- Long-content columns wrap at 500px

## What's not included
- No changes to vertical scrolling (already worked)
- No changes to data or filter logic
