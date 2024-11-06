
#heading(outlined: false, depth: 3)[{{ i.lookup_key|safe }}]
#v(0.35em, weak: true)

//// for d in i.epd_unpack \\\\
#par[
  #blue-bold[{{ d[0]|safe }}]: {{ d[1] }}. {{ d[2].replace("*", "\*")|safe }}
]
//// endfor \\\\

#par[
  #line(length: 100%, stroke: 0.1pt + rgb("00A4CC"))
  #feedback-link(
    "Correct a mistake",
    "https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{ i.lookup_key }}&entry.326955045=Meaning&entry.1433863141=DPD%20PDF+{{ date }}"
  )
]