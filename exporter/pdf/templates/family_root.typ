
#heading(outlined: false, depth: 3)[{{ i.root_family }}] <{{ i.root_family_key_typst }}>

{{ i.count }} words belong to the root family *{{ i.root_family }}* ({{ i.root_meaning }})

#block(
  stroke: 1pt + rgb("#00A4CC"),
  radius: 5pt,
  table(
    columns: (3fr, 1fr, 8fr, 0.5fr),
    stroke: (x: none, y: none),
  //// for d in i.data_unpack \\\\
    [#blue-bold[{{ d[0] }}]], [*{{ d[1] }}*], [{{ d[2]|safe }}], [#gray[{{ d[3].replace("~", "\~") }}]],
  //// endfor \\\\

    table.hline(stroke: 0.1pt + rgb("#00A4CC")),
    table.cell(colspan: 4)[
      #feedback-link(
        "Correct a mistake",
        "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.root_family_key }}&entry.326955045=Root+Family&entry.1433863141=DPD%20PDF+{{ date }}"
      )
    ]
  )
)
