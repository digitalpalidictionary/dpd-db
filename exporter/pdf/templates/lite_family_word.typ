
#heading3[{{ i.word_family }}]

//// if i.count > 1 \\\\
{{ i.count }} words belong to the #blue-bold[{{ i.word_family }}] family
//// else \\\\
{{ i.count }} word belongs to the #blue-bold[{{ i.word_family }}] family
//// endif \\\\
#v(0.35em, weak: true)
#table(
  columns: (auto, auto, 4fr, auto),
  stroke: (x: none, y: none),
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
      "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.word_family }}&entry.326955045=Word+Family&entry.1433863141=DPD%20PDF+{{ date }}"
    )                           
  ]
)
