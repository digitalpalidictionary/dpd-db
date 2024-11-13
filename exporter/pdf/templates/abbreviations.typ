
#table(
  columns: (auto, auto),
  stroke: (x: none, y: none),
  inset: (x: 0em, y: 0.35em),
  column-gutter: 1em,
//// for d in data \\\\
  [#blue[{{ d.abbrev.replace("*", "\*")|safe }}]],
  [{{ d.meaning|safe }}],
//// endfor \\\\
)