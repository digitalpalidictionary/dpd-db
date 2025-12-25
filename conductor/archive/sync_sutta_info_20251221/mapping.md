# Template Mapping: Webapp (Jinja2) to GoldenDict (Mako)

| Webapp (Jinja2) | GoldenDict (Mako) |
| --- | --- |
| `{{ d.su.field }}` | `${ su.field }` |
| `{% if d.su.field %}` | `% if su.field:` |
| `{% endif %}` | `% endif` |
| `{{ d.su.field.replace('x', 'y') }}` | `${ su.field.replace('x', 'y') }` |
| `{{ d.i.id }}` | `${ i.id }` |
| `{{ d.i.lemma_link }}` | `${ i.lemma_link }` |
| `{{ d.app_name }}` | (Not available in GoldenDict, use "GoldenDict") |
| `{{ d.date }}` | `${ today }` (Note: GoldenDict template uses `${ today }`) |

## Specific Section: BJT
All `d.su.` fields in the BJT section must be converted to `su.`.

## Specific Section: SC Express
- Change label from "SC Voice" to "SC Express".
- Change condition from `% if su.sc_code:` to `% if su.sc_express_link:`.
- Update link to `${ su.sc_express_link }`.
