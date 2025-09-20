// layout

#set text(font: "Libertinus Serif")
// #set text(font: "Crimson Pro")

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

#let blue(content) = text(rgb("#1a8bdb"))[#content]

#let blue-bold(content) = text(
  rgb("#1a8bdb"), 
  weight: "bold", 
)[#content]

#let gray(content) = text(
    rgb("#404040"),
    weight: "light",
  )[#content]

#let gray-small(content) = text(
    rgb("#808080"),
    weight: "light",
    size: 0.75em
  )[#content]

#let google-form(url) = {
  text(
    rgb("#808080"),
    size: 0.75em,
    link(url)[🖉]
  )
}

#let thin-line() = line(length: 100%, stroke: 0.1pt + rgb("1a8bdb"))

