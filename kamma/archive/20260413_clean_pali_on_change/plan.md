# Plan: Clean Pāḷi fields on change

## Phase 1: Wire on_change cleaning

- [x] Create `variant_field_change` method (clean + synonym_variant_check)
  → verify: method exists, follows same pattern as `synonym_field_change`
- [x] Update `variant` FieldConfig to use `on_change=self.variant_field_change`
  → verify: read the FieldConfig, confirm on_change is set
- [x] Update `var_phonetic` FieldConfig to add `on_change=self.clean_pali_field`
  → verify: read the FieldConfig, confirm on_change is set
- [x] Update `var_text` FieldConfig to add `on_change=self.clean_pali_field`
  → verify: read the FieldConfig, confirm on_change is set
