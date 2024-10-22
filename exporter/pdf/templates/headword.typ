// lemma
#heading(outlined: false, depth: 2)[{{ i.lemma_1 }}]
// summary
{{ i.pos }}.{% if i.plus_case %} ({{ i.plus_case }}){% endif %}{% if i.meaning_1 %} *{{ i.meaning_1_typst|safe }}*{% if i.meaning_lit %}; lit. {{ i.meaning_lit}}.{% endif %}{% else %} {{ i.meaning_2_typst|safe }}.{% endif %}{% if i.construction_summary_typst %} [{{i.construction_summary_typst}}]{% endif %} #text(gray)[{{i.degree_of_completion}}]

// grammar table
{% if i.meaning_1 %}
#table(
  columns: (2fr, 6fr),
  // table.cell(colspan: 2)[*Grammar*],
  [#text(rgb("#00A4CC"))[Pāḷi]], [{{ i.lemma_clean }}],
  [#text(rgb("#00A4CC"))[IPA]], [/{{ i.lemma_ipa }}/],
  [#text(rgb("#00A4CC"))[Grammar]], [{{ i.grammar|safe }}],
{% if i.family_root %}
  [#text(rgb("#00A4CC"))[Root Family]], [#link(<{{ i.root_family_key_typst }}>)[{{ i.family_root }}]],
{% endif %}
{% if i.root_key %}
  [#text(rgb("#00A4CC"))[Root]], [{{ i.root_clean }}#super[{{ i.rt.root_has_verb }}]{{ i.rt.root_group }} {{i.root_sign_typst}} ({{ i.rt.root_meaning }})],
{% endif %}
{% if i.rt.root_in_comps %}
  [#text(rgb("#00A4CC"))[√ In Sandhi]], [{{ i.rt.root_in_comps }}],
{% endif %}
{% if i.root_base_typst %}
  [#text(rgb("#00A4CC"))[Base]], [{{ i.root_base_typst|safe }}],
{% endif %}
{% if i.construction %}
  [#text(rgb("#00A4CC"))[Construction]], [{{ i.construction_typst|safe }}],
{% endif %}
{% if i.derivative %}
  [#text(rgb("#00A4CC"))[Derivative]], [{{ i.derivative }} ({{ i.suffix_typst }})],
{% endif %}
{% if i.phonetic %}
  [#text(rgb("#00A4CC"))[Phonetic Change]], [{{ i.phonetic_typst|safe }}],
{% endif %}
{% if i.compound_type and "?" not in i.compound_type %}
  [#text(rgb("#00A4CC"))[Compound]], [{{ i.compound_type|safe }} ({{ i.compound_construction_typst|safe }})],
{% endif %}
{% if i.family_compound and (i.needs_compound_family_button or i.needs_compound_families_button)%}
  [#text(rgb("#00A4CC"))[Compound Family]], [
{% for fc in i.family_compound.split(" ")%}
  #link(<{{ fc }}>)[{{ fc }}] 
{% endfor %}
  ],
{% endif %}
{% if i.antonym %}
  [#text(rgb("#00A4CC"))[Antonym]], [{{ i.antonym }}],
{% endif %}
{% if i.synonym %}
  [#text(rgb("#00A4CC"))[Synonym]], [{{ i.synonym }}],
{% endif %}
{% if i.variant %}
  [#text(rgb("#00A4CC"))[Variant]], [{{ i.variant }}],
{% endif %}
{% if i.commentary and i.commentary !="-" %}
  [#text(rgb("#00A4CC"))[Commentary]], [{{ i.commentary_typst|safe }}],
{% endif %}
{% if i.notes %}
  [#text(rgb("#00A4CC"))[Notes]], [{{ i.notes_typst|safe }}],
{% endif %}
{% if i.cognate %}
  [#text(rgb("#00A4CC"))[English Cognate]], [{{ i.cognate_typst|safe }}],
{% endif %}
{% if i.link %}
  [#text(rgb("#00A4CC"))[Web Link]], [{{ i.link_typst|safe }}],
{% endif %}
{% if i.non_ia %}
  [#text(rgb("#00A4CC"))[Non IA]], [{{ i.non_ia|safe }}],
{% endif %}
{% if i.sanskrit %}
  [#text(rgb("#00A4CC"))[Sanskrit]], [{{ i.sanskrit_typst|safe }}],
{% endif %}
{% if i.rt.sanskrit_root %}
  [#text(rgb("#00A4CC"))[Sanskrit Root]], [{{ i.rt.sanskrit_root }} {{ i.rt.sanskrit_root_class }} ({{ i.rt.sanskrit_root_meaning }})],
{% endif %}
)
#feedback-link(
  "Correct a mistake",
  "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lemma_link }}&entry.326955045=Grammar&entry.1433863141=DPD%20PDF+{{ date }}"
)
{% endif %}

// example(s)
{% if i.meaning_1 and i.example_1 %}
#table(
  columns: (1fr),
// {% if i.needs_example_button %}
//   [*Example*],
// {% elif i.needs_examples_button %}
//   [*Examples*],
// {% endif %}
  [
    {{ i.example_1_typst|safe }}\ 
    #text(rgb("#00A4CC"))[_{{ i.source_1 }} {{ i.sutta_1_typst|safe }}_]
  ],
{% if i.meaning_1 and i.example_2 %}
  [
    {{ i.example_2_typst|safe }}\
    #text(rgb("#00A4CC"))[_{{ i.source_2 }} {{ i.sutta_2_typst|safe }}_]
  ],
{% endif %}
)
#feedback-link(
  "Add a better example",
  "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lemma_link }}&entry.326955045=Examples&entry.1433863141=DPD%20PDF+{{ date }}"
)
{% endif %}
