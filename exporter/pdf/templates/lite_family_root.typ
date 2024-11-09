
#heading3[{{ i.root_family }}]

{{ i.count }} words belong to the root family #blue-bold[{{ i.root_family }}] ({{ i.root_meaning }})
#v(0.35em, weak: true)

#table(
  columns: (3fr, 1fr, 8fr, 0.5fr),
  stroke: none,
  inset: (x: 0em, y: 0.35em),
  column-gutter: 1em,

  table.cell(colspan: 4)[
    #thin-line()
  ],

//// for d in i.data_unpack \\\\
  [#blue-bold[{{ d[0] }}]], [{{ d[1] }}], [{{ d[2]|safe }}], [#gray-small[{{ d[3] }}]],
//// endfor \\\\
  
  table.cell(colspan: 4)[
    #thin-line()
    #feedback-link(
      "Correct a mistake",
      "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.root_family_key }}&entry.326955045=Root+Family&entry.1433863141=DPD%20PDF+{{ date }}"
    )
  ]
)
