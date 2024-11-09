
#heading3[{{ i.idiom }}]

//// if i.count > 1 \\\\
{{ i.count }} idiomatic expressions which contain #blue-bold[{{ i.idiom }}]
//// else \\\\
{{ i.count }} idiomatic expression which contains #blue-bold[{{ i.idiom }}]
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
  [#blue-bold[{{ d[0] }}]], [{{ d[1] }}], [{{ d[2].replace("*", "\*")|safe }}], [#gray-small[{{ d[3] }}]],
//// endfor \\\\

  table.cell(colspan: 4)[
    #thin-line()
    #feedback-link(
      "Add more idioms",
      "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.idiom }}&entry.326955045=Idioms&entry.1433863141=DPD%20PDF+{{ date }}"
    )                           
  ]
)
