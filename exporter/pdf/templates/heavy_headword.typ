// lemma
#heading(outlined: false, depth: 3)[{{ i.lemma_1 }}]
// summary
{{ i.pos }}.//// if i.plus_case \\\\ ({{ i.plus_case|safe }})//// endif \\\\//// if i.meaning_1 \\\\ *{{ i.meaning_1_typst|safe }}*//// if i.meaning_lit \\\\; lit. {{ i.meaning_lit}}.//// endif \\\\//// else \\\\ {{ i.meaning_2_typst|safe }}.//// endif \\\\//// if i.construction_summary_typst \\\\ [{{i.construction_summary_typst}}]//// endif \\\\ #text(gray)[{{i.degree_of_completion}}]

// grammar table
//// if i.meaning_1 \\\\
#block(
  stroke: 1pt + rgb("#00A4CC"),
  radius: 5pt,
  table(
    columns: (1fr, 3fr),
    stroke: (x: none, y: none),
    [#blue[Pāḷi]], [{{ i.lemma_clean }}],
    [#blue[IPA]], [/{{ i.lemma_ipa }}/],
    [#blue[Grammar]], [{{ i.grammar|safe }}],
  //// if i.family_root \\\\
    [#blue[Root Family]], [#link(<{{ i.root_family_key_typst }}>)[{{ i.family_root }}]],
  //// endif \\\\

  //// if i.root_key \\\\
    [#blue[Root]], [{{ i.root_clean }}#super[{{ i.rt.root_has_verb }}]{{ i.rt.root_group }} {{i.root_sign_typst}} ({{ i.rt.root_meaning }})],
  //// endif \\\\

  //// if i.rt.root_in_comps \\\\
    [#blue[√ In Sandhi]], [{{ i.rt.root_in_comps }}],
  //// endif \\\\

  //// if i.root_base_typst \\\\
    [#blue[Base]], [{{ i.root_base_typst|safe }}],
  //// endif \\\\

  //// if i.construction \\\\
    [#blue[Construction]], [{{ i.construction_typst|safe }}],
  //// endif \\\\

  //// if i.derivative \\\\
    [#blue[Derivative]], [{{ i.derivative }} ({{ i.suffix_typst }})],
  //// endif \\\\

  //// if i.phonetic \\\\
    [#blue[Phonetic Change]], [{{ i.phonetic_typst|safe }}],
  //// endif \\\\

  //// if i.compound_type and "?" not in i.compound_type \\\\
    [#blue[Compound]], [{{ i.compound_type|safe }} ({{ i.compound_construction_typst|safe }})],
  //// endif \\\\

  //// if i.family_compound and (i.needs_compound_family_button or i.needs_compound_families_button)\\\\
    [#blue[Compound Family]], [//// for fc in i.family_compound.split(" ")\\\\ #link(<{{ fc }}>)[{{ fc }}] //// endfor \\\\ ],
  //// endif \\\\

  //// if i.antonym \\\\
    [#blue[Antonym]], [{{ i.antonym }}],
  //// endif \\\\

  //// if i.synonym \\\\
    [#blue[Synonym]], [{{ i.synonym }}],
  //// endif \\\\

  //// if i.variant \\\\
    [#blue[Variant]], [{{ i.variant }}],
  //// endif \\\\

  //// if i.commentary and i.commentary !="-" \\\\
    [#blue[Commentary]], [{{ i.commentary_typst|safe }}],
  //// endif \\\\

  //// if i.notes \\\\
    [#blue[Notes]], [{{ i.notes_typst|safe }}],
  //// endif \\\\

  //// if i.cognate \\\\
    [#blue[English Cognate]], [{{ i.cognate_typst|safe }}],
  //// endif \\\\

  //// if i.link \\\\
    [#blue[Web Link]], [{{ i.link_typst|safe }}],
  //// endif \\\\

  //// if i.non_ia \\\\
    [#blue[Non IA]], [{{ i.non_ia|safe }}],
  //// endif \\\\

  //// if i.sanskrit \\\\
    [#blue[Sanskrit]], [{{ i.sanskrit_typst|safe }}],
  //// endif \\\\

  //// if i.rt.sanskrit_root \\\\
    [#blue[Sanskrit Root]], [{{ i.rt.sanskrit_root }} {{ i.rt.sanskrit_root_class }} ({{ i.rt.sanskrit_root_meaning }})],
  //// endif \\\\

    table.hline(stroke: 0.1pt + rgb("#00A4CC")),
    table.cell(colspan: 2)[
      #feedback-link(
        "Correct a mistake",
        "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lemma_link }}&entry.326955045=Grammar&entry.1433863141=DPD%20PDF+{{ date }}"
      )
    ],
  )
)
//// endif \\\\

// example(s)
//// if i.meaning_1 and i.example_1 \\\\
#block(
  stroke: 1pt + rgb("#00A4CC"),
  radius: 5pt,
  table(
    columns: (1fr),
    stroke: (x: none, y: none),
    [
      {{ i.example_1_typst|safe }}\ 
      #blue[_{{ i.source_1 }} {{ i.sutta_1_typst|safe }}_]
    ],
  //// if i.meaning_1 and i.example_2 \\\\
    [
      {{ i.example_2_typst|safe }}\
      #blue[_{{ i.source_2 }} {{ i.sutta_2_typst|safe }}_]
    ],
  //// endif \\\\

    table.hline(stroke: 0.1pt + rgb("#00A4CC")),
    table.cell(colspan: 1)[
      #feedback-link(
        "Add a better example",
        "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lemma_link }}&entry.326955045=Examples&entry.1433863141=DPD%20PDF+{{ date }}"
      )
    ]
  )
)
//// endif \\\\
