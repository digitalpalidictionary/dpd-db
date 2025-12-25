# Specification: Sync Sutta Info to GoldenDict

## 1. Overview
The `dpd_sutta_info.html` template used for GoldenDict export needs to be fully synchronized with the Webapp's `dpd_headword.html`.
The Webapp template is the source of truth. This involves porting the BJT data, fixing the SC Express label, and verifying/updating all other fields in the Sutta Info section.

## 2. Goals
- Ensure GoldenDict users have access to the exact same Sutta data as Webapp users.
- Fix the labeling error for the SC Express link.
- Maintain template consistency between the two platforms, accounting for syntax differences (Jinja2 vs Mako).

## 3. Functional Requirements
### 3.1 BJT Data Port
- **Source:** `exporter/webapp/templates/dpd_headword.html` (Jinja2)
- **Target:** `exporter/goldendict/templates/dpd_sutta_info.html` (Mako)
- **Action:** Copy the BJT section.
- **Transformation:** Convert Jinja2 syntax to Mako.
    - Variables: `{{ d.su.field }}` -> `${ su.field }` (Note: `d.su` in Jinja maps to `su` in this Mako context).
    - Conditionals: `{% if condition %}` -> `% if condition:`
    - End blocks: `{% endif %}` -> `% endif`
    - String manipulation: Verify python string methods (e.g., `.replace()`) work directly in Mako expressions.

### 3.2 Full Sutta Info Sync
- **Comparison:** Systematically compare the "Sutta Info" section of both templates.
- **Action:** Update `dpd_sutta_info.html` to include any other missing fields or structure found in `dpd_headword.html`.
- **Constraint:** Maintain the Mako syntax and GoldenDict specific context variables.

### 3.3 SC Express Fix
- Locate the table row for `sc_express_link` in `dpd_sutta_info.html`.
- Update the table header (`<th>`) from "SC Voice" to "SC Express".
- Ensure the table data (`<td>`) displays the correct link/text.

## 4. Non-Functional Requirements
- The generated HTML structure must remain valid.
- The Mako template must render without syntax errors during the export process.

## 5. Acceptance Criteria
- [ ] The `dpd_sutta_info.html` file contains the full BJT section matching `dpd_headword.html`.
- [ ] All other fields in the Sutta Info section match the Webapp template.
- [ ] All Jinja2 syntax in the new/updated sections is correctly converted to Mako.
- [ ] The row for `sc_express_link` has the header "SC Express".
