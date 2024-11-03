#par[
  #blue-lemma[{{ i.lemma_1 }}]:  
    {{ i.pos }}.//// if i.plus_case \\\\ ({{ i.plus_case|safe }})//// endif \\\\//// if i.meaning_1 \\\\ {{ i.meaning_1_typst|safe }}//// if i.meaning_lit \\\\; lit. {{ i.meaning_lit}}//// endif \\\\//// else \\\\ {{ i.meaning_2_typst|safe }}//// endif \\\\ //// if i.construction_summary_typst \\\\ #gray[[{{i.construction_summary_typst}}]]//// endif \\\\ #gray[{{ i.degree_of_completion }}]
]

