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
  rgb("#4c4c4c"),
  weight: "light",
)[#content]

#let thin-line() = line(length: 100%, stroke: 0.1pt + rgb("00A4CC"))

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

#align(left, text(15pt)[
  Created by Bodhirasa
])

#pagebreak()

// copyright page

#align(center + top)[
  Digital Pāḷi Dictionary is a work in progress, made available for testing and feedback purposes.

  Last updated on *#datetime.today().display()*
]

#align(center + horizon)[ 
  DPD Online
  #link("https://www.dpdict.net")[#blue("https://www.dpdict.net")]

  User Manual
  #link("https://digitalpalidictionary.github.io/")[#blue("https://digitalpalidictionary.github.io/")]

  Github Repository
  #link("https://github.com/digitalpalidictionary/dpd-db")[#blue("https://github.com/digitalpalidictionary/dpd-db")]
]

#align(center + bottom)[

  Digital Pāḷi Dictionary is made available under a

  *Creative Commons \
  Attribution-NonCommercial-ShareAlike \
  4.0 International License* \

  #image(
    "images/by-nc-sa.png",
    format: "png",
    width: auto,
    height: auto,
    alt: "CC-BY-NC-SA",
  )

  #link("https://creativecommons.org/licenses/by-nc-sa/4.0/")[license details here]
]

#pagebreak()

// quote

#align(center + horizon)[
  tasmātiha, bhikkhave, evaṃ sikkhitabbaṃ – \
  attharasassa dhammarasassa vimuttirasassa lābhino bhavissāmāti. \
  evañhi vo, bhikkhave, sikkhitabbanti. \
  #text(size: 0.8em)[#blue[Aṅguttara Nikaya 1.335]]
]

#pagebreak()

// outline

#outline(depth: 1)
#pagebreak()

#set page(
  numbering: "1 / 1"
)

#counter(page).update(1)

