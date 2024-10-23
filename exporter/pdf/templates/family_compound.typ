#heading(outlined: true, depth: 2)[{{ i.compound_family }}] <{{ i.compound_family }}>

*{{ i.count }}* compounds which contain *{{ i.compound_family }}*

#table(
  columns: (auto, auto, 4fr, auto),
{% for d in i.data_unpack %}
  [#blue-bold[{{ d[0] }}]], [*{{ d[1] }}*], [{{ d[2].replace("*", "\*")|safe }}], [#text(gray)[{{ d[3].replace("~", "\~") }}]],
{% endfor %}
)
#feedback-link(
  "Correct a mistake",
  "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.compound_family }}&entry.326955045=Compound+Family&entry.1433863141=DPD%20PDF+{{ date }}"
)