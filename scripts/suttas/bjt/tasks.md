# Jātaka Extraction Tasks

## Current Status
- Script `kn13_jat.py` created and partially working
- Extracting 533 jātakas instead of expected 547
- Missing 14 jātakas
- **PROGRESS UPDATE**: Conditional logic structure identified and partially fixed
- **NEXT STEP**: Fix Mahānipāto variable usage and test clean version

## Critical Issues to Fix

### 1. **Mahānipāto Coding Problem**
**Current Issue**: Mahānipāto jātakas have wrong codes
- Should be: `bjt_sutta_code: "22. 1."`, `bjt_web_code: "kn-jat-22-1"`
- Currently: `bjt_sutta_code: "0. 0. 1."`, `bjt_web_code: "kn-jat-0-0-1"`

**Root Cause**: Mahānipāto logic conflict - both special case AND regular logic processing same entries

### 2. **Missing Jātakas (14 total)**
**Expected**: 547 jātakas total
**Current**: 533 jātakas
**Missing**: 14 jātakas somewhere in extraction logic

### 3. **Field Name Issues**
- `bjt_piṭaka` should be exactly "suttantapiṭake" (no extra characters)

## Required Fixes

### Fix 1: Restructure Conditional Logic ✅ COMPLETED
**Problem**: Mahānipāto jātakas (level 2) are being caught by regular jātaka logic
**Solution**: Reorder conditions to check Mahānipāto FIRST, before regular jātaka patterns
**Status**: Clean version created with proper conditional structure

```python
# Current problematic flow:
elif (level == 1 or level == 2) and re.match(...):
    # Regular jātaka logic
elif level == 2 and "mahānipāto" in current_nipāta.lower():
    # Mahānipāto logic (never reached!)

# Fixed flow:
elif level == 2 and "mahānipāto" in current_nipāta.lower() and re.match(...):
    # Mahānipāto logic (priority)
elif (level == 1 or level == 2) and re.match(...) and "mahānipāto" not in current_nipāta.lower():
    # Regular jātaka logic
```

### Fix 2: Correct Mahānipāto Variable Usage 🔄 IN PROGRESS
**Problem**: Using `nipāta_num` (which is 0) instead of `actual_nipata` (which is 22)
**Solution**: Use consistent variable naming in Mahānipāto block
**Status**: Clean version created but still needs variable fix and testing

```python
# In Mahānipāto block:
actual_nipata = 22  # Use this consistently
sutta_code = f"22. {jātaka_num}."  # Correct format
web_code = f"kn-jat-22-{jātaka_num}"  # Correct format
```

### Fix 3: Add Debug Output ⏳ PENDING
**Problem**: Can't see which jātakas are being missed
**Solution**: Add debug prints to track pattern matching
**Status**: Ready to implement after variable fix

```python
# Add debug output for each jātaka found:
print(f"DEBUG: Found jātaka: {text}, level: {level}, pattern_match: {re.match(...)}")
```

### Fix 4: Investigate Missing Jātakas ⏳ PENDING
**Problem**: Need to identify which specific jātakas are missing
**Solution**: 
1. Add counting per nipāta to identify gaps
2. Check if some jātakas use different patterns
3. Verify all 10 expected Mahānipāto jātakas are captured
**Status**: Ready to implement after variable fix

### Fix 5: Verify Field Values
**Problem**: `bjt_piṭaka` field may have extra characters
**Solution**: Ensure exact string match "suttantapiṭake"

## Implementation Priority
1. **HIGH**: Fix Mahānipāto variable usage - use actual_nipata=22 consistently
2. **MEDIUM**: Add debug output to identify missing jātakas
3. **MEDIUM**: Verify and fix field values
4. **LOW**: Optimize performance and add validation

## Expected Outcome
- All 547 jātakas extracted
- Mahānipāto jātakas coded as `kn-jat-22-1` to `kn-jat-22-10`
- All field names and values correct
- Debug output shows extraction process clearly

## Test Cases
1. Verify Mahānipāto: `1. mūgapakkhajātakaṃ` → `22. 1.` → `kn-jat-22-1`
2. Verify regular jātaka: `1. 1. 1. apaṇṇakajātakaṃ` → `1. 1. 1.` → `kn-jat-1-1-1`
3. Count total jātakas per nipāta matches expected distribution

## Next Steps for New Agent
1. **Deploy clean version**: Replace `kn13_jat.py` with the clean conditional logic version
2. **Fix Mahānipāto variables**: Ensure `actual_nipata=22` is used consistently 
3. **Test and debug**: Run script and verify Mahānipāto codes are correct
4. **Investigate missing jātakas**: Add counting to identify the 14 missing entries
5. **Fix field values**: Ensure `bjt_piṭaka` field is exactly "suttantapiṭake"
## Progress Update - December 10, 2025

### Current Status
- Script `kn13_jat.py` is partially working
- Extracting 533 jātakas instead of expected 547 (missing 14)
- Mahānipāto entries are correctly coded as 22. 1. to 22. 5. (5 entries found, need 10)
- Field value inconsistencies identified:
  - 27 entries have "suttantapiṭake - khuddakanikāye" instead of "suttantapiṭake"
  - 188 entries have "khuddakanikāyo" instead of "khuddakanikāye"

### Missing Jātakas Analysis
Specific missing jātakas identified by user:
1. sabbasaṃhārakapañhajātaka
2. gadrabhapañhajātaka  
3. amarādevīpañhajātaka
4. tittirajātaka
5. siṅgālajātaka

**Investigation needed**: These jātakas may not exist in the current JSON files, or they may use different formatting patterns that don't match the regex `^\d+\.\s*\w+.*jātakaṃ`.

### Issues Found
1. **Field Value Inconsistencies**: Script uses raw text from JSON instead of standardized values
2. **Missing Jātakas**: 14 jātakas not being extracted - need to identify if they exist in source files
3. **Mahānipāto Count**: Only 5 Mahānipāto jātakas found instead of expected 10

### Next Steps
1. **HIGH**: Fix field value inconsistencies by hardcoding standardized values
2. **HIGH**: Search for missing jātakas in all JSON files to determine if they exist
3. **MEDIUM**: Add debug output to track extraction process
4. **MEDIUM**: Verify Mahānipāto jātaka count and investigate missing 5 entries
5. **LOW**: Test script with fixes and verify all 547 jātakas are extracted

### Script Analysis
Current script correctly handles:
- Mahānipāto conditional logic (checks Mahānipāto first)
- Proper nipāta_num assignment (22 for Mahānipāto)
- Correct sutta code generation (22. 1., 22. 2., etc.)

Script needs fixes for:
- Field value standardization
- Missing jātaka detection
- Debug output for troubleshooting
