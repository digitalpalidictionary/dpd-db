## Phase 1: root_base filtering by root_sign

- [x] 1.1 In `database_manager.py`: modify `get_root_bases()` to accept `root_sign` param and filter results
- [x] 1.2 Update `get_next_root_base()` signature to accept `root_sign`, pass it to `get_root_bases()`
- [x] 1.3 In `dpd_fields.py`: update `root_base_submit()` to pass current `root_sign` value
- [x] 1.4 Verify with sample data

## Phase 2: family_root derivation from construction

- [x] 2.1 In `database_manager.py`: add `_derive_family_root()` helper
- [x] 2.2 Update `get_next_family_root()` to accept optional `construction` param
- [x] 2.3 In `dpd_fields.py`: update `family_root_submit()` to pass current `construction` value
- [x] 2.4 Verify with sample data
