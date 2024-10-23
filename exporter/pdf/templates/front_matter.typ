#show link: underline
#set table(stroke: 0.1pt + silver)

#set page(
  paper: "a4",
  numbering: "1 / 1",
)

#let feedback-link(comment, url) = {
  v(-10pt)
  text(
    size: 6pt,
    link(url)[#comment]
  )
}

#let blue(content) = text(rgb("#00A4CC"))[#content]
#let blue-bold(content) = text(rgb("#00A4CC"), weight: "bold")[#content]

// title page 

#align(left, text(18pt)[
  *Digital Pāḷi Dictionary*
])

#align(left, text(14pt)[
  Created by Bodhirasa Bhikkhu
])

#align(left, text(10pt)[
  Updated on #text(rgb("#00A4CC"))[#datetime.today().display()]
])

#pagebreak()

// copyright page

Digital Pāḷi Dictionary is a work in progress, made available for feedback and suggestions.
#pagebreak()

#outline(depth: 1)
#pagebreak()

// abbreviations page

= List of Abbreviations
#pagebreak()

// dpd

= Pāḷi to English Dictionary

