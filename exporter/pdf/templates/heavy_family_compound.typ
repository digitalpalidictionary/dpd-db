
#heading(outlined: false, depth: 3)[{{ i.compound_family }}] <{{ i.compound_family }}>

*{{ i.count }}* compounds which contain *{{ i.compound_family }}*

#block(
  stroke: 1pt + rgb("#00A4CC"),
  radius: 5pt,
  table(
    columns: (auto, auto, 4fr, auto),
    stroke: (x: none, y: none),
  
  //// for d in i.data_unpack \\\\
    [#blue-bold[{{ d[0] }}]], [*{{ d[1] }}*], [{{ d[2].replace("*", "\*")|safe }}], [#gray[{{ d[3] }}]],
  //// endfor \\\\

    table.hline(stroke: 0.1pt + rgb("#00A4CC")),
    table.cell(colspan: 4)[
      #feedback-link(
        "Correct a mistake",
        "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.compound_family }}&entry.326955045=Compound+Family&entry.1433863141=DPD%20PDF+{{ date }}"
      )                           
    ]
  )    
)             
