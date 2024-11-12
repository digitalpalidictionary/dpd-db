#par[
  #blue-bold[{{ i.lemma_1 }}]    
    {{ i.pos }}.//// if i.plus_case \\\\ ({{ i.plus_case|safe }})//// endif \\\\//// if i.meaning_1 \\\\ {{ i.meaning_1_typst|safe }}//// if i.meaning_lit \\\\; lit. {{ i.meaning_lit}}//// endif \\\\//// else \\\\ {{ i.meaning_2_typst|safe }}//// endif \\\\ //// if i.construction_summary_typst \\\\ #gray[[{{i.construction_summary_typst}}]]//// endif \\\\ #gray-small[{{ i.degree_of_completion }}]
  // #google-form("https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lemma_link }}&entry.326955045=Meaning&entry.1433863141=DPD%20PDF+{{ date }}")
]

