
#heading(outlined: false, depth: 2)[{{ i.compound_family }}]
// <{{ i.compound_family }}>

//// if i.count == 1 \\\\
{{ i.count }} compound which contains *{{ i.compound_family }}*
//// else \\\\
{{ i.count }} compounds which contain *{{ i.compound_family }}*
//// endif \\\\

#table(
  columns: (auto, auto, 4fr, auto),
  stroke: (x: none, y: none),
  inset: (x: 0em, y: 0.35em),
  column-gutter: 1em, 

//// for d in i.data_unpack \\\\
  [#blue-lemma[{{ d[0] }}]], [{{ d[1] }}], [{{ d[2].replace("*", "\*")|safe }}], [#gray[{{ d[3] }}]],
//// endfor \\\\

  table.cell(colspan: 4)[
    #line(length: 100%, stroke: 0.1pt + rgb("00A4CC"))
    #feedback-link(
      "Correct a mistake",
      "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.compound_family }}&entry.326955045=Compound+Family&entry.1433863141=DPD%20PDF+{{ date }}"
    )                           
  ]
)
