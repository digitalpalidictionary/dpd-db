

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
#hide[
  #heading(level: 1)[Title Page]
]

#align(left, text(20pt)[
  *Digital Pāḷi Dictionary*
])

#align(left, text(15pt)[
  Created by Bodhirasa
])

#pagebreak()

// copyright page

#hide[
  #heading(level: 1)[Front Matter]
]

#align(center + top)[
  Digital Pāḷi Dictionary is a work in progress, made available for testing and feedback purposes.

  Last updated on *#datetime.today().display()*
]

#align(center + horizon)[ 
  DPD Online
  #link("https://www.dpdict.net")[#blue("https://www.dpdict.net")]

  DPD Docs Website
  #link("https://digitalpalidictionary.github.io/")[#blue("https://digitalpalidictionary.github.io/")]

  Github Repository
  #link("https://github.com/digitalpalidictionary/dpd-db")[#blue("https://github.com/digitalpalidictionary/dpd-db")]

  Get the latest version
  #link("https://github.com/digitalpalidictionary/dpd-db/releases/latest")[#blue("https://github.com/digitalpalidictionary/dpd-db/releases/latest")]

]

#align(center + bottom)[

  Digital Pāḷi Dictionary is made available under a

  *Creative Commons \
  Attribution-NonCommercial-ShareAlike 4.0 \
  International License* \

  #image(
    "images/by-nc-sa.png",
    format: "png",
    width: auto,
    height: auto,
    alt: "CC BY-NC-SA",
  )

  #link("https://creativecommons.org/licenses/by-nc-sa/4.0/")[CC BY-NC-SA 4.0 \
  license details]
]

#pagebreak()

// quote

#hide[
  #heading(level: 1)[Epigraph]
]

#align(center + horizon)[
  tasmātiha, bhikkhave, evaṃ sikkhitabbaṃ – \
  attharasassa dhammarasassa vimuttirasassa lābhino bhavissāmāti. \
  evañhi vo, bhikkhave, sikkhitabbanti. \
  #text(size: 0.8em)[#blue[Aṅguttara Nikaya 1.335]]
]

#pagebreak()

// outline

#hide[
  #heading(level: 1)[Contents]
]

#outline(depth: 1)
#pagebreak()

#set page(numbering: "1 / 1")

