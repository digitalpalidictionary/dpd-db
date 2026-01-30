# Mako to Jinja2 Migration: Discovery Report

**Date:** 2026-01-29  
**Project:** Digital Pāḷi Dictionary (DPD)  
**Track:** Mako to Jinja2 Template Refactoring

---

## 1. Executive Summary

### Overview
The Digital Pāḷi Dictionary project currently uses the **Mako** templating engine for HTML generation across multiple exporters. This report documents the complete inventory of Mako usage and provides a roadmap for migrating to **Jinja2**, a more modern and widely-supported templating engine.

### Key Findings
- **9 Python files** use Mako for template rendering
- **36 template files** contain Mako syntax (`.html` files)
- **2 template files** already use Jinja2 syntax (Kobo exporter)
- **Webapp exporter** already uses Jinja2 via FastAPI
- Most templates use simple variable substitution and conditionals
- Some templates contain complex nested logic and loops

### Migration Status
- **Already Migrated:** Webapp templates (Jinja2), Kobo templates (Jinja2)
- **Needs Migration:** 36 Mako templates across 6 exporters
- **Estimated Complexity:** Medium - mostly automated conversion possible

---

## 2. Files Using Mako

### 2.1 Python Files with Mako Imports

| # | File Path | Purpose | Templates Used |
|---|-----------|---------|----------------|
| 1 | [`exporter/deconstructor/deconstructor_exporter.py`](exporter/deconstructor/deconstructor_exporter.py:5) | Exports deconstructor data to GoldenDict/MDict | 2 |
| 2 | [`exporter/kindle/kindle_exporter.py`](exporter/kindle/kindle_exporter.py:16) | Creates EPUB/MOBI ebook versions | 8 |
| 3 | [`exporter/tpr/tpr_exporter.py`](exporter/tpr/tpr_exporter.py:14) | Exports data for Tipitaka Pali Reader | 1 |
| 4 | [`exporter/goldendict/export_epd.py`](exporter/goldendict/export_epd.py:5) | Generates English-to-Pāḷi dictionary HTML | 1 |
| 5 | [`exporter/grammar_dict/grammar_dict.py`](exporter/grammar_dict/grammar_dict.py:5) | Compiles grammar dictionary HTML tables | 1 |
| 6 | [`exporter/goldendict/export_variant_spelling.py`](exporter/goldendict/export_variant_spelling.py:7) | Generates variant readings and spelling corrections | 3 |
| 7 | [`exporter/goldendict/export_dpd.py`](exporter/goldendict/export_dpd.py:10) | Main DPD headword HTML compiler (most complex) | 14 |
| 8 | [`exporter/goldendict/export_help.py`](exporter/goldendict/export_help.py:7) | Compiles help, abbreviations, bibliography | 2 |
| 9 | [`exporter/goldendict/export_roots.py`](exporter/goldendict/export_roots.py:6) | Generates root dictionary HTML | 6 |

**Total: 9 Python files**

### 2.2 Python File Purposes

#### 1. Deconstructor Exporter
- **File:** `exporter/deconstructor/deconstructor_exporter.py`
- **Purpose:** Prepares deconstruction data for GoldenDict and MDict formats
- **Complexity:** Low
- **Key Function:** `make_deconstructor_dict_data()`

#### 2. Kindle Exporter
- **File:** `exporter/kindle/kindle_exporter.py`
- **Purpose:** Creates EPUB and MOBI versions of DPD for Kindle devices
- **Complexity:** Medium
- **Key Functions:** Multiple `render_*_templ()` functions for different entry types

#### 3. TPR Exporter
- **File:** `exporter/tpr/tpr_exporter.py`
- **Purpose:** Exports simplified DPD data for Tipitaka Pali Reader integration
- **Complexity:** Medium
- **Key Function:** `generate_tpr_data()`

#### 4. GoldenDict EPD Exporter
- **File:** `exporter/goldendict/export_epd.py`
- **Purpose:** Generates HTML for English-to-Pāḷi dictionary
- **Complexity:** Low
- **Key Function:** `generate_epd_html()`

#### 5. Grammar Dictionary
- **File:** `exporter/grammar_dict/grammar_dict.py`
- **Purpose:** Compiles HTML tables of grammatical possibilities
- **Complexity:** Medium
- **Key Function:** `generate_html_from_lookup()`

#### 6. Variant/Spelling Exporter
- **File:** `exporter/goldendict/export_variant_spelling.py`
- **Purpose:** Generates HTML for variant readings and spelling mistakes
- **Complexity:** Low
- **Key Functions:** `generate_variant_data_list()`, `generate_spelling_data_list()`

#### 7. Main DPD Exporter (Most Complex)
- **File:** `exporter/goldendict/export_dpd.py`
- **Purpose:** Main DPD headword HTML compiler with multiprocessing
- **Complexity:** High
- **Key Features:**
  - Uses multiprocessing for performance
  - 14 different template types
  - Complex template class `DpdHeadwordTemplates`
  - Multiple render functions for different sections

#### 8. Help Exporter
- **File:** `exporter/goldendict/export_help.py`
- **Purpose:** Compiles help files, abbreviations, bibliography, and thanks
- **Complexity:** Low
- **Key Functions:** `add_abbrev_html()`, `add_help_html()`, `add_bibliography()`, `add_thanks()`

#### 9. Roots Exporter
- **File:** `exporter/goldendict/export_roots.py`
- **Purpose:** Generates HTML for Pāḷi roots dictionary
- **Complexity:** Medium
- **Key Functions:** Multiple `render_root_*_templ()` functions

---

## 3. Template Inventory

### 3.1 Templates by Directory

#### Deconstructor (2 templates)
| File | Path | Syntax |
|------|------|--------|
| [`deconstructor_header.html`](exporter/deconstructor/deconstructor_header.html) | `exporter/deconstructor/` | Static HTML (no Mako) |
| [`deconstructor.html`](exporter/deconstructor/deconstructor.html) | `exporter/deconstructor/` | Mako |

#### GoldenDict Templates (26 templates)
| # | File | Path | Syntax | Complexity |
|---|------|------|--------|------------|
| 1 | [`dpd_header.html`](exporter/goldendict/templates/dpd_header.html) | `exporter/goldendict/templates/` | Mako | High |
| 2 | [`dpd_header_plain.html`](exporter/goldendict/templates/dpd_header_plain.html) | `exporter/goldendict/templates/` | Static HTML | Low |
| 3 | [`dpd_definition.html`](exporter/goldendict/templates/dpd_definition.html) | `exporter/goldendict/templates/` | Mako | Low |
| 4 | [`dpd_button_box.html`](exporter/goldendict/templates/dpd_button_box.html) | `exporter/goldendict/templates/` | Mako | Medium |
| 5 | [`dpd_example.html`](exporter/goldendict/templates/dpd_example.html) | `exporter/goldendict/templates/` | Mako | Medium |
| 6 | [`dpd_grammar.html`](exporter/goldendict/templates/dpd_grammar.html) | `exporter/goldendict/templates/` | Mako | High |
| 7 | [`dpd_inflection.html`](exporter/goldendict/templates/dpd_inflection.html) | `exporter/goldendict/templates/` | Mako | Medium |
| 8 | [`dpd_family_root.html`](exporter/goldendict/templates/dpd_family_root.html) | `exporter/goldendict/templates/` | Mako | Low |
| 9 | [`dpd_family_word.html`](exporter/goldendict/templates/dpd_family_word.html) | `exporter/goldendict/templates/` | Mako | Low |
| 10 | [`dpd_family_compound.html`](exporter/goldendict/templates/dpd_family_compound.html) | `exporter/goldendict/templates/` | Mako | Low |
| 11 | [`dpd_family_idiom.html`](exporter/goldendict/templates/dpd_family_idiom.html) | `exporter/goldendict/templates/` | Mako | Low |
| 12 | [`dpd_family_set.html`](exporter/goldendict/templates/dpd_family_set.html) | `exporter/goldendict/templates/` | Mako | Low |
| 13 | [`dpd_frequency.html`](exporter/goldendict/templates/dpd_frequency.html) | `exporter/goldendict/templates/` | Mako | Low |
| 14 | [`dpd_feedback.html`](exporter/goldendict/templates/dpd_feedback.html) | `exporter/goldendict/templates/` | Mako | Low |
| 15 | [`dpd_sutta_info.html`](exporter/goldendict/templates/dpd_sutta_info.html) | `exporter/goldendict/templates/` | Mako | Very High |
| 16 | [`dpd_variant_reading.html`](exporter/goldendict/templates/dpd_variant_reading.html) | `exporter/goldendict/templates/` | Mako | Low |
| 17 | [`dpd_spelling_mistake.html`](exporter/goldendict/templates/dpd_spelling_mistake.html) | `exporter/goldendict/templates/` | Mako | Low |
| 18 | [`help_abbrev.html`](exporter/goldendict/templates/help_abbrev.html) | `exporter/goldendict/templates/` | Mako | Low |
| 19 | [`help_help.html`](exporter/goldendict/templates/help_help.html) | `exporter/goldendict/templates/` | Mako | Low |
| 20 | [`root_header.html`](exporter/goldendict/templates/root_header.html) | `exporter/goldendict/templates/` | Mako | Medium |
| 21 | [`root_definition.html`](exporter/goldendict/templates/root_definition.html) | `exporter/goldendict/templates/` | Mako | Low |
| 22 | [`root_buttons.html`](exporter/goldendict/templates/root_buttons.html) | `exporter/goldendict/templates/` | Mako | Low |
| 23 | [`root_info.html`](exporter/goldendict/templates/root_info.html) | `exporter/goldendict/templates/` | Mako | Low |
| 24 | [`root_matrix.html`](exporter/goldendict/templates/root_matrix.html) | `exporter/goldendict/templates/` | Mako | Low |
| 25 | [`root_families.html`](exporter/goldendict/templates/root_families.html) | `exporter/goldendict/templates/` | Mako | Low |
| 26 | [`epd.html`](exporter/goldendict/templates/epd.html) | `exporter/goldendict/templates/` | Mako | Low |

#### Kindle Templates (8 templates)
| # | File | Path | Syntax | Complexity |
|---|------|------|--------|------------|
| 1 | [`ebook_abbreviation_entry.html`](exporter/kindle/templates/ebook_abbreviation_entry.html) | `exporter/kindle/templates/` | Mako | Medium |
| 2 | [`ebook_content_opf.html`](exporter/kindle/templates/ebook_content_opf.html) | `exporter/kindle/templates/` | Mako | Low |
| 3 | [`ebook_deconstructor_entry.html`](exporter/kindle/templates/ebook_deconstructor_entry.html) | `exporter/kindle/templates/` | Mako | Low |
| 4 | [`ebook_entry.html`](exporter/kindle/templates/ebook_entry.html) | `exporter/kindle/templates/` | Mako | Medium |
| 5 | [`ebook_example.html`](exporter/kindle/templates/ebook_example.html) | `exporter/kindle/templates/` | Mako | Medium |
| 6 | [`ebook_grammar.html`](exporter/kindle/templates/ebook_grammar.html) | `exporter/kindle/templates/` | Mako | High |
| 7 | [`ebook_letter.html`](exporter/kindle/templates/ebook_letter.html) | `exporter/kindle/templates/` | Mako | Low |
| 8 | [`ebook_titlepage.html`](exporter/kindle/templates/ebook_titlepage.html) | `exporter/kindle/templates/` | Mako | Low |

#### Grammar Dictionary (1 template)
| File | Path | Syntax |
|------|------|--------|
| [`grammar_dict_header.html`](exporter/grammar_dict/grammar_dict_header.html) | `exporter/grammar_dict/` | Static HTML |

#### Variants (1 template)
| File | Path | Syntax |
|------|------|--------|
| [`variants_header.html`](exporter/variants/variants_header.html) | `exporter/variants/` | Static HTML |

#### Kobo Templates (2 templates) - ALREADY JINJA2
| File | Path | Syntax |
|------|------|--------|
| [`dpd_headword.html`](exporter/kobo/templates/dpd_headword.html) | `exporter/kobo/templates/` | **Jinja2** |
| [`lookup.html`](exporter/kobo/templates/lookup.html) | `exporter/kobo/templates/` | **Jinja2** |

#### Webapp Templates (17 templates) - ALREADY JINJA2
| # | File | Path | Syntax |
|---|------|------|--------|
| 1 | `abbreviations.html` | `exporter/webapp/templates/` | Jinja2 |
| 2 | `abbreviations_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 3 | `bold_definitions.html` | `exporter/webapp/templates/` | Jinja2 |
| 4 | `deconstructor.html` | `exporter/webapp/templates/` | Jinja2 |
| 5 | `deconstructor_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 6 | `dpd_headword.html` | `exporter/webapp/templates/` | Jinja2 |
| 7 | `dpd_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 8 | `epd.html` | `exporter/webapp/templates/` | Jinja2 |
| 9 | `epd_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 10 | `grammar.html` | `exporter/webapp/templates/` | Jinja2 |
| 11 | `grammar_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 12 | `header.html` | `exporter/webapp/templates/` | Jinja2 |
| 13 | `help.html` | `exporter/webapp/templates/` | Jinja2 |
| 14 | `help_summary.html` | `exporter/webapp/templates/` | Jinja2 |
| 15 | `home.html` | `exporter/webapp/templates/` | Jinja2 |
| 16 | `home_simple.html` | `exporter/webapp/templates/` | Jinja2 |
| 17+ | (others) | `exporter/webapp/templates/` | Jinja2 |

**Total Template Count:**
- Mako templates needing migration: **36**
- Already Jinja2: **19** (17 webapp + 2 kobo)
- Static HTML headers: **4**

---

## 4. Python-to-Template Mapping

### 4.1 Deconstructor Exporter
```python
# exporter/deconstructor/deconstructor_exporter.py
Template(filename=str(g.pth.deconstructor_header_templ_path))  # deconstructor_header.html
Template(filename=str(g.pth.deconstructor_templ_path))         # deconstructor.html
```

### 4.2 Kindle Exporter
```python
# exporter/kindle/kindle_exporter.py
Template(filename=str(pth.ebook_entry_templ_path))             # ebook_entry.html
Template(filename=str(pth.ebook_grammar_templ_path))           # ebook_grammar.html
Template(filename=str(pth.ebook_example_templ_path))           # ebook_example.html
Template(filename=str(pth.ebook_deconstructor_templ_path))     # ebook_deconstructor_entry.html
Template(filename=str(pth.ebook_letter_templ_path))            # ebook_letter.html
Template(filename=str(pth.ebook_abbrev_entry_templ_path))      # ebook_abbreviation_entry.html
Template(filename=str(pth.ebook_title_page_templ_path))        # ebook_titlepage.html
Template(filename=str(pth.ebook_content_opf_templ_path))       # ebook_content_opf.html
```

### 4.3 TPR Exporter
```python
# exporter/tpr/tpr_exporter.py
Template(filename=str(g.pth.dpd_definition_templ_path))        # dpd_definition.html
```

### 4.4 GoldenDict EPD Exporter
```python
# exporter/goldendict/export_epd.py
Template(filename=str(pth.dpd_header_plain_templ_path))        # dpd_header_plain.html
```

### 4.5 Grammar Dictionary
```python
# exporter/grammar_dict/grammar_dict.py
Template(filename=str(g.pth.grammar_dict_header_templ_path))   # grammar_dict_header.html
```

### 4.6 Variant/Spelling Exporter
```python
# exporter/goldendict/export_variant_spelling.py
Template(filename=str(pth.dpd_header_plain_templ_path))        # dpd_header_plain.html
Template(filename=str(pth.variant_templ_path))                 # dpd_variant_reading.html
Template(filename=str(pth.spelling_templ_path))                # dpd_spelling_mistake.html
```

### 4.7 Main DPD Exporter (export_dpd.py)
```python
# exporter/goldendict/export_dpd.py - DpdHeadwordTemplates class
self.header_templ = Template(filename=str(paths.dpd_header_templ_path))              # dpd_header.html
self.dpd_definition_templ = Template(filename=str(paths.dpd_definition_templ_path))  # dpd_definition.html
self.button_box_templ = Template(filename=str(paths.button_box_templ_path))          # dpd_button_box.html
self.sutta_info_templ = Template(filename=str(paths.sutta_info_templ_path))          # dpd_sutta_info.html
self.grammar_templ = Template(filename=str(paths.grammar_templ_path))                # dpd_grammar.html
self.example_templ = Template(filename=str(paths.example_templ_path))                # dpd_example.html
self.inflection_templ = Template(filename=str(paths.inflection_templ_path))          # dpd_inflection.html
self.family_root_templ = Template(filename=str(paths.family_root_templ_path))        # dpd_family_root.html
self.family_word_templ = Template(filename=str(paths.family_word_templ_path))        # dpd_family_word.html
self.family_compound_templ = Template(filename=str(paths.family_compound_templ_path)) # dpd_family_compound.html
self.family_idiom_templ = Template(filename=str(paths.family_idiom_templ_path))      # dpd_family_idiom.html
self.family_set_templ = Template(filename=str(paths.family_set_templ_path))          # dpd_family_set.html
self.frequency_templ = Template(filename=str(paths.frequency_templ_path))            # dpd_frequency.html
self.feedback_templ = Template(filename=str(paths.feedback_templ_path))              # dpd_feedback.html
```

### 4.8 Help Exporter
```python
# exporter/goldendict/export_help.py
Template(filename=str(pth.dpd_header_plain_templ_path))        # dpd_header_plain.html
Template(filename=str(pth.abbrev_templ_path))                  # help_abbrev.html
Template(filename=str(pth.help_templ_path))                    # help_help.html
```

### 4.9 Roots Exporter
```python
# exporter/goldendict/export_roots.py
Template(filename=str(pth.root_header_templ_path))             # root_header.html
Template(filename=str(pth.root_definition_templ_path))         # root_definition.html
Template(filename=str(pth.root_button_templ_path))             # root_buttons.html
Template(filename=str(pth.root_info_templ_path))               # root_info.html
Template(filename=str(pth.root_matrix_templ_path))             # root_matrix.html
Template(filename=str(pth.root_families_templ_path))           # root_families.html
```

---

## 5. Mako Syntax Catalog

### 5.1 Variable Substitution

| Mako Syntax | Jinja2 Equivalent | Example |
|-------------|-------------------|---------|
| `${variable}` | `{{ variable }}` | `${i.lemma_1}` → `{{ i.lemma_1 }}` |
| `${obj.attr}` | `{{ obj.attr }}` | `${i.pos}` → `{{ i.pos }}` |
| `${dict['key']}` | `{{ dict['key'] }}` | `${i['meaning']}` → `{{ i['meaning'] }}` |

### 5.2 Control Structures

| Mako Syntax | Jinja2 Equivalent | Example |
|-------------|-------------------|---------|
| `% if condition:` | `{% if condition %}` | `% if i.plus_case:` → `{% if i.plus_case %}` |
| `% endif` | `{% endif %}` | Same closing tag |
| `% for item in items:` | `{% for item in items %}` | `% for d in deconstructions:` → `{% for d in deconstructions %}` |
| `% endfor` | `{% endfor %}` | Same closing tag |
| `% else` | `{% else %}` | Same else tag |
| `% elif` | `{% elif %}` | Same elif tag |

### 5.3 Comments

| Mako Syntax | Jinja2 Equivalent | Example |
|-------------|-------------------|---------|
| `## comment` | `{# comment #}` | `## TODO` → `{# TODO #}` |
| `<%doc> ... </%doc>` | `{# ... #}` | Multi-line comments |

### 5.4 Common Patterns Found

#### Pattern 1: Simple Variable Output
```mako
<!-- Mako -->
<p>${i.pos}. ${i.meaning_combo_html}</p>
```
```jinja2
<!-- Jinja2 -->
<p>{{ i.pos }}. {{ i.meaning_combo_html }}</p>
```

#### Pattern 2: Conditional Rendering
```mako
<!-- Mako -->
% if i.plus_case:
(${i.plus_case})
% endif
```
```jinja2
<!-- Jinja2 -->
{% if i.plus_case %}
({{ i.plus_case }})
{% endif %}
```

#### Pattern 3: Loop with Index
```mako
<!-- Mako -->
% for counter, i in enumerate(dpd_db):
    ${counter}: ${i.lemma_1}
% endfor
```
```jinja2
<!-- Jinja2 -->
{% for i in dpd_db %}
    {{ loop.index0 }}: {{ i.lemma_1 }}
{% endfor %}
```

#### Pattern 4: Nested Conditionals
```mako
<!-- Mako -->
% if i.example_1 and i.example_2:
<div id="examples_${i.lemma_1_}" class="dpd content hidden">
% elif i.example_1 and not i.example_2:
<div id="example_${i.lemma_1_}" class="dpd content hidden">
% endif
```
```jinja2
<!-- Jinja2 -->
{% if i.example_1 and i.example_2 %}
<div id="examples_{{ i.lemma_1_ }}" class="dpd content hidden">
{% elif i.example_1 and not i.example_2 %}
<div id="example_{{ i.lemma_1_ }}" class="dpd content hidden">
{% endif %}
```

#### Pattern 5: Method Calls
```mako
<!-- Mako -->
${ su.bjt_open_tipitaka_lk_link.replace('latn', 'deva') }
```
```jinja2
<!-- Jinja2 -->
{{ su.bjt_open_tipitaka_lk_link.replace('latn', 'deva') }}
```

#### Pattern 6: Dictionary Access
```mako
<!-- Mako -->
${ i.freq_data_unpack["FreqHeading"] }
```
```jinja2
<!-- Jinja2 -->
{{ i.freq_data_unpack["FreqHeading"] }}
```

#### Pattern 7: List Iteration
```mako
<!-- Mako -->
% for website in i.link_list:
    <a href="${website}" target="_blank">${website}</a>
% endfor
```
```jinja2
<!-- Jinja2 -->
{% for website in i.link_list %}
    <a href="{{ website }}" target="_blank">{{ website }}</a>
{% endfor %}
```

### 5.5 Special Cases

#### Inline JavaScript with Variables
```mako
<!-- Mako -->
<script>
var data_${ i.lemma_1_ } = {
    "id": ${ i.id },
    "lemma": "${i.lemma_1}",
};
</script>
```
```jinja2
<!-- Jinja2 -->
<script>
var data_{{ i.lemma_1_ }} = {
    "id": {{ i.id }},
    "lemma": "{{ i.lemma_1 }}",
};
</script>
```

#### URL Parameters
```mako
<!-- Mako -->
<a href="https://example.com/form?entry=${i.id}%20${i.lemma_link}">Link</a>
```
```jinja2
<!-- Jinja2 -->
<a href="https://example.com/form?entry={{ i.id }}%20{{ i.lemma_link }}">Link</a>
```

---

## 6. Complexity Analysis

### 6.1 Exporter Complexity Ratings

| Exporter | Complexity | Templates | Risk Level | Notes |
|----------|------------|-----------|------------|-------|
| **Deconstructor** | Low | 2 | Low | Simple loop over deconstructions |
| **Kindle** | Medium | 8 | Medium | Multiple entry types, EPUB structure |
| **TPR** | Medium | 1 | Low | Uses shared dpd_definition template |
| **GoldenDict EPD** | Low | 1 | Low | Simple header template |
| **Grammar Dict** | Medium | 1 | Medium | Custom grammar row generation |
| **Variant/Spelling** | Low | 3 | Low | Simple variant/spelling templates |
| **GoldenDict DPD** | **High** | 14 | **High** | Multiprocessing, most complex |
| **Help** | Low | 2 | Low | Abbreviations and help entries |
| **Roots** | Medium | 6 | Medium | Root dictionary with families |

### 6.2 Template Complexity Ratings

| Template | Complexity | Lines | Key Features |
|----------|------------|-------|--------------|
| `dpd_sutta_info.html` | Very High | 902 | 100+ conditionals, multiple tables |
| `dpd_header.html` | High | 104 | JavaScript data injection, conditionals |
| `dpd_grammar.html` | High | 201 | 30+ conditional rows, nested logic |
| `ebook_grammar.html` | High | 134 | Similar to dpd_grammar |
| `root_header.html` | Medium | 48 | JavaScript data injection |
| `dpd_button_box.html` | Medium | 42 | 13 conditional buttons |
| `dpd_example.html` | Medium | 26 | Nested conditionals |
| `ebook_entry.html` | Medium | 21 | Kindle-specific tags |
| `dpd_inflection.html` | Medium | 29 | Conditional div IDs |
| Others | Low | <20 | Simple variable substitution |

### 6.3 Risk Assessment by Component

#### Low Risk (Simple Migration)
- `dpd_definition.html` - Simple variable substitution
- `dpd_family_*.html` - Placeholder templates
- `dpd_spelling_mistake.html` - Single variable
- `dpd_variant_reading.html` - Single variable
- `help_abbrev.html` - Simple conditionals
- `help_help.html` - Simple structure
- `root_definition.html` - Simple variables
- `root_info.html` - Simple variables
- `root_matrix.html` - Simple conditionals

#### Medium Risk (Moderate Complexity)
- `dpd_button_box.html` - Multiple conditionals
- `dpd_example.html` - Nested conditionals
- `dpd_inflection.html` - Conditional structure
- `root_buttons.html` - Loop with conditionals
- `root_families.html` - Simple loop
- `root_header.html` - JavaScript integration
- `ebook_*.html` - EPUB-specific structure
- `deconstructor.html` - Simple loop

#### High Risk (Complex Migration)
- `dpd_header.html` - Complex JavaScript data structures
- `dpd_grammar.html` - 30+ conditional table rows
- `dpd_sutta_info.html` - 900+ lines, 100+ conditionals
- `ebook_grammar.html` - Parallel to dpd_grammar

---

## 7. Migration Strategy Recommendations

### 7.1 Recommended Migration Order

Based on complexity analysis, migrate in this order:

#### Phase 1: Simple Templates (Low Risk)
1. `dpd_definition.html`
2. `dpd_family_root.html`
3. `dpd_family_word.html`
4. `dpd_family_compound.html`
5. `dpd_family_idiom.html`
6. `dpd_family_set.html`
7. `dpd_frequency.html`
8. `dpd_feedback.html`
9. `dpd_spelling_mistake.html`
10. `dpd_variant_reading.html`
11. `help_abbrev.html`
12. `help_help.html`
13. `root_definition.html`
14. `root_info.html`
15. `root_matrix.html`
16. `root_families.html`

#### Phase 2: Medium Complexity
17. `dpd_button_box.html`
18. `dpd_example.html`
19. `dpd_inflection.html`
20. `root_buttons.html`
21. `root_header.html`
22. `deconstructor.html`
23. `ebook_deconstructor_entry.html`
24. `ebook_titlepage.html`
25. `ebook_content_opf.html`
26. `ebook_letter.html`

#### Phase 3: High Complexity
27. `ebook_abbreviation_entry.html`
28. `ebook_entry.html`
29. `ebook_example.html`
30. `ebook_grammar.html`

#### Phase 4: Most Complex
31. `dpd_header.html`
32. `dpd_grammar.html`
33. `dpd_sutta_info.html`

### 7.2 Automation vs Manual Conversion

#### Fully Automatable (Simple regex replacement)
- Variable substitution: `${var}` → `{{ var }}`
- Simple conditionals: `% if` → `{% if %}`
- Simple loops: `% for` → `{% for %}`
- Comments: `##` → `{# #}`

#### Requires Manual Review
- Complex nested conditionals
- JavaScript data injection in templates
- Templates with inline logic
- Multiline statements

#### Recommended Approach
1. Create an automated conversion script for 80% of patterns
2. Manual review and fix for edge cases
3. Comprehensive testing for each exporter

### 7.3 Edge Cases Requiring Special Attention

#### 1. Multiprocessing in export_dpd.py
```python
# Templates are created in child processes
# Jinja2 Environment must be picklable or recreated in each process
```

#### 2. JavaScript Data Injection
```html
<!-- dpd_header.html and root_header.html -->
<script>
var data_${ i.lemma_1_ } = { ... };
</script>
```

#### 3. Conditional Opening Tags
```html
<!-- dpd_example.html and dpd_inflection.html -->
% if condition:
<div id="...">
% elif other_condition:
<div id="...">
% endif
```

#### 4. URL Encoding in Links
```html
<a href="...&entry=${i.id}%20${i.lemma_link}&...">
```

#### 5. Method Chaining
```html
${ su.bjt_open_tipitaka_lk_link.replace('latn', 'deva') }
```

#### 6. Enumerate in Loops
```mako
% for counter, i in enumerate(dpd_db):
```
Jinja2 uses `loop.index` or `loop.index0` instead.

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Output mismatch between Mako and Jinja2 | Medium | High | Comprehensive testing suite |
| Multiprocessing issues with Jinja2 | Low | High | Test with full dataset |
| Template syntax errors after conversion | Medium | Medium | Automated validation |
| Performance degradation | Low | Medium | Benchmark before/after |
| JavaScript injection issues | Medium | High | Test all interactive features |

### 8.2 Mitigation Strategies

#### 1. Comprehensive Testing
- Create output comparison tests for each exporter
- Compare Mako vs Jinja2 output byte-by-byte
- Test with full production dataset

#### 2. Gradual Migration
- Migrate one exporter at a time
- Keep Mako as fallback during transition
- Validate each exporter before proceeding

#### 3. Automated Validation
- Create script to validate all templates
- Check for syntax errors
- Verify all variables are accessible

#### 4. Manual Testing Checklist
- [ ] GoldenDict export renders correctly
- [ ] MDict export renders correctly
- [ ] Kindle EPUB validates
- [ ] Webapp functions normally
- [ ] All buttons and interactions work
- [ ] Audio playback works
- [ ] Feedback forms link correctly

### 8.3 Rollback Plan

1. Keep Mako templates in version control
2. Maintain dual template systems during transition
3. Feature flags to switch between Mako/Jinja2
4. Quick rollback capability if issues arise

---

## 9. Summary

### Key Metrics
- **Python files to update:** 9
- **Mako templates to migrate:** 36
- **Already Jinja2:** 19 templates (webapp + kobo)
- **Estimated effort:** 2-3 weeks with testing
- **Risk level:** Medium (well-understood scope)

### Next Steps
1. Create automated conversion script
2. Set up Jinja2 environment utilities
3. Begin Phase 1 migration (simple templates)
4. Implement comprehensive testing
5. Proceed through phases sequentially

### Success Criteria
- All 36 Mako templates converted to Jinja2
- All 9 Python files updated to use Jinja2
- Output identical to original Mako version
- All tests passing
- No performance regression
- Documentation updated

---

*Report generated: 2026-01-29*  
*Discovery Phase: Complete*