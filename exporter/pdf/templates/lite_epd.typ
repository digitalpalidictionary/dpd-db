
#heading3[{{ i.lookup_key|safe }}]
#v(0.35em, weak: true)
#table(
  columns: (auto, auto, 4fr),
  stroke: (x: none, y: none),
  inset: (x: 0em, y: 0.35em),
  column-gutter: 1em,

  table.cell(colspan: 3)[
  #thin-line()
  ],

//// for d in i.epd_unpack \\\\
  [#blue-bold[{{ d[0]|safe }}]],
  [{{ d[1] }}],
  [{{ d[2].replace("*", "\*")|safe }}],
//// endfor \\\\

  table.cell(colspan: 3)[
    #thin-line()
    #feedback-link(
      "Correct a mistake",
      "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lookup_key }}&entry.326955045=Meaning&entry.1433863141=DPD%20PDF+{{ date }}"
    )                           
  ]
)