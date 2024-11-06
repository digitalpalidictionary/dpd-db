// layout

#show link: underline
#set table(stroke: 0.1pt + silver)

// formulas

#let feedback-link(comment, url) = {
  v(-3pt)
  text(
    size: 6pt,
    link(url)[#comment]
  )
}

#let heading3(content) = {
  heading(level: 2, outlined: false)[#content]
}

#let blue(content) = text(rgb("#00A4CC"))[#content]

#let blue-bold(content) = text(
  rgb("#00A4CC"), 
  weight: "bold", 
)[#content]

#let gray(content) = text(
  rgb("#909090"),
  weight: "light",
)[#content]

// title page

#set page(
  paper: "a4",
  numbering: none,
)

#set document(
  title: "Digital Pāḷi Dictionary",
  author: "Bodhirasa Bhikkhu",
  date: auto
  )

#align(left, text(20pt)[
  *Digital Pāḷi Dictionary*
])

#align(left, text(12pt)[
  Created by Bodhirasa Bhikkhu
])

#align(left, text(8pt)[
  Updated on #text(rgb("#00A4CC"))[*#datetime.today().display()*]
])

#pagebreak()

// copyright page

Digital Pāḷi Dictionary is a work in progress, made available for testing and feedback.

Copyright information goes here...
#pagebreak()

// outline

#outline(depth: 1)
#pagebreak()

// abbreviations page

#set page(
  numbering: "1 / 1"
)
#counter(page).update(1)

= List of Abbreviations
Abbreviations go here...
// #pagebreak()

