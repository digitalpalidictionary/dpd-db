
//// for d in data \\\\
  //// if d.category \\\\
  #heading(level: 2, outlined: true)[
    {{ d.category|safe }}
  ]
  #line(length: 100%)
  //// endif \\\\
  //// if d.surname \\\\ - #blue-bold[{{ d.surname|safe }}]//// endif \\\\//// if d.firstname \\\\, {{ d.firstname|safe }}//// endif \\\\//// if d.year \\\\, {{ d.year|safe }}//// endif \\\\//// if d.title \\\\. _{{ d.title|safe }}_//// endif \\\\//// if d.city and d.publisher \\\\, {{ d.city|safe }}: {{ d.publisher|safe }}//// elif not d.city and d.publisher \\\\, {{ d.publisher|safe }}//// endif \\\\//// if d.site \\\\, accessed through #link("{{ d.site|safe }}")[{{ d.site }}]//// endif \\\\
  
//// endfor \\\\
