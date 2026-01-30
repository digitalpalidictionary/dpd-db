# Mako to Jinja2 Syntax Conversion Guide

**Date:** 2026-01-29  
**Project:** Digital Pāḷi Dictionary (DPD)  
**Track:** Mako to Jinja2 Template Refactoring

---

## Overview

This guide documents the syntax conversions required when migrating Mako templates to Jinja2 for the DPD project. It covers all patterns found in the project's 36 Mako templates across 9 Python files.

---

## 1. Basic Syntax Translations

### 1.1 Variable Expressions

| Mako | Jinja2 | Description |
|------|--------|-------------|
| `${variable}` | `{{ variable }}` | Simple variable output |
| `${obj.attr}` | `{{ obj.attr }}` | Object attribute access |
| `${dict['key']}` | `{{ dict['key'] }}` | Dictionary key access |
| `${obj.method()}` | `{{ obj.method() }}` | Method calls |
| `${obj.method(arg)}` | `{{ obj.method(arg) }}` | Method calls with arguments |

**Examples:**

```mako
<!-- Mako -->
<p>${i.lemma_1}</p>
<p>${i.pos}. ${i.meaning_combo_html}</p>
```

```jinja2
<!-- Jinja2 -->
<p>{{ i.lemma_1 }}</p>
<p>{{ i.pos }}. {{ i.meaning_combo_html }}</p>
```

### 1.2 Control Structures

| Mako | Jinja2 | Description |
|------|--------|-------------|
| `% if condition:` | `{% if condition %}` | If statement opening |
| `% elif condition:` | `{% elif condition %}` | Else-if statement |
| `% else:` | `{% else %}` | Else statement |
| `% endif` | `{% endif %}` | If statement closing |
| `% for item in items:` | `{% for item in items %}` | For loop opening |
| `% endfor` | `{% endfor %}` | For loop closing |
| `% while condition:` | `{% while condition %}` | While loop opening |
| `% endwhile` | `{% endwhile %}` | While loop closing |

**Examples:**

```mako
<!-- Mako -->
% if i.plus_case:
    <span>(${i.plus_case})</span>
% endif
```

```jinja2
<!-- Jinja2 -->
{% if i.plus_case %}
    <span>({{ i.plus_case }})</span>
{% endif %}
```

### 1.3 Comments

| Mako | Jinja2 | Description |
|------|--------|-------------|
| `## comment` | `{# comment #}` | Single-line comment |
| `<%doc> ... </%doc>` | `{# ... #}` | Multi-line comment block |

**Examples:**

```mako
<!-- Mako -->
## This is a comment
<%doc>
This is a
multi-line comment
</%doc>
```

```jinja2
<!-- Jinja2 -->
{# This is a comment #}
{#
This is a
multi-line comment
#}
```

---

## 2. Control Structure Translations

### 2.1 If/Elif/Else Statements

**Mako:**
```mako
% if i.example_1 and i.example_2:
    <div id="examples_${i.lemma_1_}" class="dpd content hidden">
% elif i.example_1 and not i.example_2:
    <div id="example_${i.lemma_1_}" class="dpd content hidden">
% else:
    <div class="dpd content">
% endif
```

**Jinja2:**
```jinja2
{% if i.example_1 and i.example_2 %}
    <div id="examples_{{ i.lemma_1_ }}" class="dpd content hidden">
{% elif i.example_1 and not i.example_2 %}
    <div id="example_{{ i.lemma_1_ }}" class="dpd content hidden">
{% else %}
    <div class="dpd content">
{% endif %}
```

### 2.2 For Loops

**Mako:**
```mako
% for d in deconstructions:
    <p>${d}</p>
% endfor
```

**Jinja2:**
```jinja2
{% for d in deconstructions %}
    <p>{{ d }}</p>
{% endfor %}
```

### 2.3 For Loops with Index

**Mako (using enumerate):**
```mako
% for counter, i in enumerate(dpd_db):
    <tr id="${counter}">
        <td>${i.lemma_1}</td>
    </tr>
% endfor
```

**Jinja2 (using loop.index0):**
```jinja2
{% for i in dpd_db %}
    <tr id="{{ loop.index0 }}">
        <td>{{ i.lemma_1 }}</td>
    </tr>
{% endfor %}
```

**Jinja2 Loop Variables:**
- `loop.index` - 1-based index
- `loop.index0` - 0-based index
- `loop.first` - True if first iteration
- `loop.last` - True if last iteration
- `loop.length` - Total number of items

### 2.4 Nested Control Structures

**Mako:**
```mako
% if i.family_set:
    <div class="family_set">
    % for f in i.family_set_list:
        % if f:
            <p>${f}</p>
        % endif
    % endfor
    </div>
% endif
```

**Jinja2:**
```jinja2
{% if i.family_set %}
    <div class="family_set">
    {% for f in i.family_set_list %}
        {% if f %}
            <p>{{ f }}</p>
        {% endif %}
    {% endfor %}
    </div>
{% endif %}
```

---

## 3. Special Cases and Edge Cases

### 3.1 String Interpolation in HTML Attributes

**Mako:**
```mako
<div id="examples_${i.lemma_1_}" class="dpd content hidden">
<a href="#freq_${i.lemma_1_}">Frequency</a>
```

**Jinja2:**
```jinja2
<div id="examples_{{ i.lemma_1_ }}" class="dpd content hidden">
<a href="#freq_{{ i.lemma_1_ }}">Frequency</a>
```

### 3.2 Dictionary Access

**Mako:**
```mako
${i['abbrev']}
${i.freq_data_unpack["FreqHeading"]}
${data['key_with_underscore']}
```

**Jinja2:**
```jinja2
{{ i['abbrev'] }}
{{ i.freq_data_unpack["FreqHeading"] }}
{{ data['key_with_underscore'] }}
```

### 3.3 Nested Attribute Access

**Mako:**
```mako
${i.rt.root_has_verb}
${i.si.sutta_code}
${i.grammar_row.pos}
```

**Jinja2:**
```jinja2
{{ i.rt.root_has_verb }}
{{ i.si.sutta_code }}
{{ i.grammar_row.pos }}
```

### 3.4 Method Calls

**Mako:**
```mako
${i.freq_data_unpack["FreqHeading"]}
${su.bjt_open_tipitaka_lk_link.replace('latn', 'deva')}
${text.strip().upper()}
```

**Jinja2:**
```jinja2
{{ i.freq_data_unpack["FreqHeading"] }}
{{ su.bjt_open_tipitaka_lk_link.replace('latn', 'deva') }}
{{ text.strip().upper() }}
```

### 3.5 URL Parameters with Variables

**Mako:**
```mako
<a href="https://docs.google.com/forms/d/e/.../viewform?entry=${i.id}%20${i.lemma_link}">
<a href="${website}" target="_blank">${website}</a>
```

**Jinja2:**
```jinja2
<a href="https://docs.google.com/forms/d/e/.../viewform?entry={{ i.id }}%20{{ i.lemma_link }}">
<a href="{{ website }}" target="_blank">{{ website }}</a>
```

### 3.6 Inline JavaScript with Variables

**Mako:**
```mako
<script>
var data_${i.lemma_1_} = {
    "id": ${i.id},
    "lemma": "${i.lemma_1}",
    "pos": "${i.pos}"
};
</script>
```

**Jinja2:**
```jinja2
<script>
var data_{{ i.lemma_1_ }} = {
    "id": {{ i.id }},
    "lemma": "{{ i.lemma_1 }}",
    "pos": "{{ i.pos }}"
};
</script>
```

### 3.7 Conditional Opening Tags

**Mako:**
```mako
% if i.example_1 and i.example_2:
    <div id="examples_${i.lemma_1_}" class="content hidden">
% elif i.example_1 and not i.example_2:
    <div id="example_${i.lemma_1_}" class="content hidden">
% else:
    <div class="content">
% endif
    <!-- content here -->
    </div>
```

**Jinja2:**
```jinja2
{% if i.example_1 and i.example_2 %}
    <div id="examples_{{ i.lemma_1_ }}" class="content hidden">
{% elif i.example_1 and not i.example_2 %}
    <div id="example_{{ i.lemma_1_ }}" class="content hidden">
{% else %}
    <div class="content">
{% endif %}
    <!-- content here -->
    </div>
```

### 3.8 Complex Boolean Expressions

**Mako:**
```mako
% if i.meaning_1 and i.meaning_1 != "_":
    <p>${i.meaning_1}</p>
% endif

% if i.example_1 or i.example_2:
    <div class="examples">
% endif
```

**Jinja2:**
```jinja2
{% if i.meaning_1 and i.meaning_1 != "_" %}
    <p>{{ i.meaning_1 }}</p>
{% endif %}

{% if i.example_1 or i.example_2 %}
    <div class="examples">
{% endif %}
```

---

## 4. Patterns NOT Used in This Project

The following Mako features are **not used** in the DPD project but are documented here for reference when working with other Mako codebases.

### 4.1 Template Inheritance

**Mako:**
```mako
<%inherit file="base.html"/>
<%block name="content">
    <!-- content here -->
</%block>
```

**Jinja2:**
```jinja2
{% extends "base.html" %}
{% block content %}
    <!-- content here -->
{% endblock %}
```

### 4.2 Defs (Template Functions)

**Mako:**
```mako
<%def name="greeting(name)">
    Hello, ${name}!
</%def>

${greeting('World')}
```

**Jinja2:**
```jinja2
{% macro greeting(name) %}
    Hello, {{ name }}!
{% endmacro %}

{{ greeting('World') }}
```

### 4.3 Python Code Blocks

**Mako:**
```mako
<%
    import datetime
    now = datetime.datetime.now()
%>
<p>Current time: ${now}</p>
```

**Jinja2:**
```jinja2
{# Jinja2 does not support arbitrary Python code blocks #}
{# Use template context or custom filters instead #}
```

### 4.4 Filters

**Mako:**
```mako
${variable | h}      <!-- HTML escape -->
${variable | n}      <!-- Disable escaping -->
${variable | trim}   <!-- Trim whitespace -->
```

**Jinja2:**
```jinja2
{{ variable | e }}       <!-- HTML escape -->
{{ variable | safe }}    <!-- Mark as safe HTML -->
{{ variable | trim }}    <!-- Trim whitespace -->
{{ variable | upper }}   <!-- Uppercase -->
{{ variable | lower }}   <!-- Lowercase -->
```

### 4.5 Namespaces and Includes

**Mako:**
```mako
<%namespace file="helpers.html" import="*"/>
<%include file="header.html"/>
```

**Jinja2:**
```jinja2
{% from "helpers.html" import * %}
{% include "header.html" %}
```

---

## 5. Common Pitfalls

### 5.1 Whitespace Handling

**Issue:** Jinja2 and Mako handle whitespace differently in control structures.

**Mako:**
```mako
% if condition:
    content
% endif
```

**Jinja2 (with whitespace control):**
```jinja2
{% if condition -%}
    content
{%- endif %}
```

**Note:** Use `-` to trim whitespace:
- `{%- ... %}` - Trim before
- `{% ... -%}` - Trim after
- `{%- ... -%}` - Trim both sides

### 5.2 Auto-Escaping Behavior

**Issue:** Both engines auto-escape by default, but behavior differs.

**Mako:**
```mako
${html_content}        <!-- Auto-escaped by default -->
${html_content | n}    <!-- Disable escaping (not recommended) -->
```

**Jinja2:**
```jinja2
{{ html_content }}           <!-- Auto-escaped by default -->
{{ html_content | safe }}    <!-- Mark as safe (use with caution) -->
```

**Best Practice:** Pass pre-escaped HTML from Python code rather than using `| safe` or `| n`.

### 5.3 Undefined Variable Handling

**Issue:** Mako and Jinja2 handle undefined variables differently.

**Mako:**
- Undefined variables render as empty strings by default
- Can be configured to raise errors

**Jinja2:**
- Undefined variables render as empty strings in production
- In debug mode, raises `UndefinedError`
- Use `default` filter for fallback values

```jinja2
{{ undefined_var | default('fallback') }}
{{ undefined_var | default('', true) }}  {# Use default if undefined or empty #}
```

### 5.4 Boolean Comparisons

**Issue:** Truthiness checks can differ.

**Mako:**
```mako
% if i.meaning_1:
    <!-- True if meaning_1 is truthy -->
% endif
```

**Jinja2:**
```jinja2
{% if i.meaning_1 %}
    <!-- True if meaning_1 is truthy -->
{% endif %}

{# Explicit None check #}
{% if i.meaning_1 is not none %}
```

### 5.5 String Concatenation

**Issue:** Building strings in templates.

**Mako:**
```mako
${"prefix_" + i.lemma_1}
```

**Jinja2:**
```jinja2
{{ "prefix_" ~ i.lemma_1 }}
{# Or use format #}
{{ "prefix_%s" | format(i.lemma_1) }}
```

### 5.6 Dictionary Default Values

**Issue:** Accessing dictionary keys that may not exist.

**Mako:**
```mako
${i.freq_data_unpack.get("FreqHeading", "N/A")}
```

**Jinja2:**
```jinja2
{{ i.freq_data_unpack.get("FreqHeading", "N/A") }}
{# Or use default filter #}
{{ i.freq_data_unpack["FreqHeading"] | default("N/A") }}
```

---

## 6. Quick Reference Table

### 6.1 Syntax Comparison Summary

| Feature | Mako | Jinja2 |
|---------|------|--------|
| **Variables** | `${var}` | `{{ var }}` |
| **If statement** | `% if cond:` | `{% if cond %}` |
| **Elif** | `% elif cond:` | `{% elif cond %}` |
| **Else** | `% else:` | `{% else %}` |
| **Endif** | `% endif` | `{% endif %}` |
| **For loop** | `% for x in y:` | `{% for x in y %}` |
| **Endfor** | `% endfor` | `{% endfor %}` |
| **Comments** | `## comment` | `{# comment #}` |
| **Multi-line comments** | `<%doc>...</%doc>` | `{# ... #}` |
| **Loop index (0-based)** | `enumerate()` | `loop.index0` |
| **Loop index (1-based)** | - | `loop.index` |
| **First iteration** | - | `loop.first` |
| **Last iteration** | - | `loop.last` |
| **HTML escape** | `${var \| h}` | `{{ var \| e }}` |
| **Mark safe** | `${var \| n}` | `{{ var \| safe }}` |
| **Default value** | - | `{{ var \| default('') }}` |

### 6.2 Common Pattern Conversions

| Pattern | Mako | Jinja2 |
|---------|------|--------|
| **Simple output** | `${i.lemma_1}` | `{{ i.lemma_1 }}` |
| **Attribute access** | `${i.rt.root}` | `{{ i.rt.root }}` |
| **Dictionary access** | `${i['abbrev']}` | `{{ i['abbrev'] }}` |
| **Method call** | `${text.strip()}` | `{{ text.strip() }}` |
| **Conditional** | `% if i.pos:` | `{% if i.pos %}` |
| **Loop** | `% for x in list:` | `{% for x in list %}` |
| **String in attribute** | `id="_${i.id}"` | `id="_{{ i.id }}"` |
| **URL parameter** | `?id=${i.id}` | `?id={{ i.id }}` |

### 6.3 File Extensions

| Engine | Template Extension |
|--------|-------------------|
| Mako | `.html`, `.mako` |
| Jinja2 | `.html`, `.j2`, `.jinja2` |

**Note:** This project uses `.html` for both Mako and Jinja2 templates. The engine is determined by the Python code that loads the template.

---

## 7. Testing Checklist

After converting a template, verify:

- [ ] All `${}` expressions converted to `{{ }}`
- [ ] All `% if` converted to `{% if %}`
- [ ] All `% for` converted to `{% for %}`
- [ ] All `% endif` converted to `{% endif %}`
- [ ] All `% endfor` converted to `{% endfor %}`
- [ ] All `##` comments converted to `{# #}`
- [ ] Enumerate loops use `loop.index0`
- [ ] No Mako-specific syntax remains
- [ ] Template renders without errors
- [ ] Output matches original Mako output

---

## 8. Related Documents

- [Discovery Report](discovery_report.md) - Complete inventory of Mako usage
- [Plan](plan.md) - Migration plan and phases
- [exporter/jinja2_env.py](../../../exporter/jinja2_env.py) - Jinja2 environment setup

---

*Guide created: 2026-01-29*  
*Phase 2: Setup and Configuration*
