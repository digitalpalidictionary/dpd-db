{% if i.root_family.startswith("√") %}
#heading(outlined: true, depth: 2)[{{ i.root_family }}] <{{ i.root_family_key_typst }}>
{% else %}
#heading(outlined: false, depth: 2)[{{ i.root_family }}] <{{ i.root_family_key_typst }}>
{%  endif %}

{{ i.count }} words belong to the root family *{{ i.root_family }}* ({{ i.root_meaning }})

#table(
  columns: (3fr, 1fr, 8fr, 0.5fr),
{% for d in i.data_unpack %}
  [#blue-bold[{{ d[0] }}]], [*{{ d[1] }}*], [{{ d[2] }}], [#text(gray)[{{ d[3].replace("~", "\~") }}]],
{% endfor %}
)
#feedback-link(
  "Correct a mistake",
  "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.root_family_key }}&entry.326955045=Root+Family&entry.1433863141=DPD%20PDF+{{ date }}"
)
