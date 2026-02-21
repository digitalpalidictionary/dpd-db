# Specification: SN Peyyala Numbering Fix

## Overview

The `sn_peyyalas` list in `tools/cst_source_sutta_example.py` contains errors that cause incorrect sutta numbering in Samyutta Nikaya. This affects SN24 (Diṭṭhisaṃyutta), SN30 (Supaṇṇasaṃyutta), and SN33 (Vacchagottasaṃyutta).

## Problem Statement

### Issue 1: SN30 Numbering Off by +3

**Root Cause**: Lines 37-39 have wrong `samyutta_counter` (20 instead of 30) and one incorrect range.

```python
# Current (WRONG):
(20, "4-6. Dutiyādidvayakārīsuttattikaṃ", 4, 6),
(20, "7-16. Aṇḍajadānūpakārasuttadasakaṃ", 11, 20),  # range also wrong
(20, "17-46. Jalābujādidānūpakārasuttatiṃsakaṃ", 17, 46),
```

These never match because `g.samyutta_counter` is 30 for Supaṇṇasaṃyutta, not 20.

### Issue 2: SN33.51-55 Off by +1 After That

**Root Cause**: Line 54 has wrong end number.

```python
# Current (WRONG):
(33, "51-54. Rūpaappaccakkhakammādisuttacatukkaṃ", 51, 55),
```

The subhead text says "51-54" (4 suttas), XML shows `n="657-660"`. A separate sutta 55 follows.

### Issue 3: SN24 Numbering Off by ~30

**Root Cause**: SN24 has NO entries in `sn_peyyalas`. SN24 uses "bookend notation" where vaggas 2-4 show only the first and last sutta numbers, with middle suttas abbreviated in the bodytext `n` attribute.

- Vagga 1: 18 suttas (normal)
- Vagga 2: 26 suttas (bookend: "1. Vātasuttaṃ" and "18. Nevahotinanahotisuttaṃ" with `n="225-240"` in between)
- Vagga 3: 26 suttas (bookend pattern)
- Vagga 4: 26 suttas (bookend pattern)
- **Total**: 96 suttas (current code counts ~32)

The peyyala logic at line 751 only triggers when `"-" in x.text`, but SN24 subheads don't contain hyphens.

## Solution Design

### Keep Existing 4-Element Tuple Structure

No need to extend the tuple. The existing `p_start` value already disambiguates
entries with the same text, because `sutta_counter` is cumulative within a
samyutta (never reset between vaggas). For example, SN24 vaggas 3 and 4 both
have `"1. Navātasuttaṃ"`, but vagga 3 needs `sutta_counter==44` and vagga 4
needs `sutta_counter==70` — no collision possible.

### Fix Existing Wrong Entries

| Line | Current | Fixed |
|------|---------|-------|
| 37 | `(20, "4-6...", 4, 6)` | `(30, "4-6...", 4, 6)` |
| 38 | `(20, "7-16...", 11, 20)` | `(30, "7-16...", 7, 16)` |
| 39 | `(20, "17-46...", 17, 46)` | `(30, "17-46...", 17, 46)` |
| 54 | `(33, "51-54...", 51, 55)` | `(33, "51-54...", 51, 54)` |

### Add SN24 Entries

```python
# SN24 Diṭṭhisaṃyutta - vaggas 2-4 bookend notation
(24, "1. Vātasuttaṃ", 19, 44),
(24, "1. Navātasuttaṃ", 45, 70),
(24, "1. Navātasuttaṃ", 71, 96),
```

### Restructure Branch Logic

The current code has two mutually exclusive branches:

- Branch 1 (line 739): `subhead + starts_with_digit + NO hyphen` — normal single sutta
- Branch 2 (line 749): `subhead + HAS hyphen` — check peyyala list

SN24's subheads (e.g. `"1. Vātasuttaṃ"`) have no hyphen, so they always enter
Branch 1 and never reach the peyyala loop. **This is the root cause of Issue 3.**

Fix: merge into a single branch that checks peyyalas first for ALL subheads,
then falls through to normal counting for unmatched non-hyphenated entries:

```python
elif x["rend"] == "subhead" and re.findall(r"^\d", x.text):
    sutta_counter_special = ""
    peyyala_matched = False

    for peyyala in sn_peyyalas:
        p_samyutta_counter, p_sutta_name, p_start, p_end = peyyala
        if (
            p_samyutta_counter == g.samyutta_counter
            and x.text == p_sutta_name
            and g.sutta_counter == p_start - 1
        ):
            sutta_name = re.sub(r"^\d.*\. ", "", x.text)
            sutta_counter_special = f"{p_start}-{p_end}"
            g.sutta_counter = p_end
            peyyala_matched = True
            break

    if not peyyala_matched and "-" not in x.text:
        sutta_name, sutta_no = get_text_and_number(x.text)
        g.sutta_counter += 1
```

No false positives: matching requires exact samyutta + exact text + exact
sutta counter position.

## Functional Requirements

1. **FR-1**: SN30 suttas must be numbered correctly (1-46 for Supaṇṇasaṃyutta)
2. **FR-2**: SN33 suttas 51-55 must have correct numbering (51-54 for peyyala, then 55 individually)
3. **FR-3**: SN24 must count 96 suttas total across 4 vaggas
4. **FR-4**: All existing samyutta numbering must remain unchanged

## Acceptance Criteria

1. SN30 sutta numbering matches CST paragraph numbers in XML
2. SN33 suttas 51-55 produce correct source strings (SN33.51-54, SN33.55)
3. SN24 produces source strings from SN24.1 through SN24.96
4. All other samyutta numbering is unchanged
5. All existing tests pass

## Out of Scope

- Changes to other nikayas (DN, MN, AN, KN)
- Changes to sutta content extraction logic
- UI or exporter changes
