// layout

#show link: underline
#set table(stroke: 0.1pt + silver)

// formulas

#let feedback-link(comment, url) = {
  // v(-10pt)
  text(
    size: 6pt,
    link(url)[#comment]
  )
}

#let blue(content) = text(rgb("#00A4CC"))[#content]

#let blue-bold(content) = text(rgb("#00A4CC"), weight: "bold")[#content]

#let blue-lemma(content) = text(
  rgb("#00A4CC"), 
  weight: "bold", 
  size: 1.1em
)[#content]

#let gray(content) = text(
  rgb("#909090"),
  weight: "light",
  size: 0.8em
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

#align(left, text(18pt)[
  *Digital Pāḷi Dictionary*
])

#align(left, text(14pt)[
  Created by Bodhirasa Bhikkhu
])

#align(left, text(10pt)[
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
#pagebreak()

// dpd

= Pāḷi to English Dictionary
#text(" ")
