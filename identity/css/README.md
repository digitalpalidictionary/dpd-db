# Single Source of Truth

This folder contains the Single Source of Truth for all CSS used across the project.

# CSSManager

`tools/css_manager.py` handles syncing all CSS across the project.

The two main files are

## dpd.css
Contains all CSS classes used everywhere

## dpd-fonts.css
Imports the fonts from disk / res folder

## dpd-css-and-fonts.css
This is an automatically generated combo of the above two files. Don't adjust manually.

## dpd-variables.css

This is automatically added to header files:

- GoldenDict — DPD Header: [exporter/goldendict/templates/dpd_header.html](../../exporter/goldendict/templates/dpd_header.html)

- GoldenDict - Root Header [exporter/goldendict/templates/root_header.html](../../exporter/goldendict/templates/root_header.html)

- GoldenDict — Deconstructor Header: [exporter/deconstructor/deconstructor_header.html](../../exporter/deconstructor/deconstructor_header.html)

- GoldenDict — DPD Header plain:[exporter/goldendict/templates/dpd_header_plain.html](../../exporter/goldendict/templates/dpd_header_plain.html)

- GoldenDict — GrammarDict Header: [exporter/grammar_dict/grammar_dict_header.html](../../exporter/grammar_dict/grammar_dict_header.html)

- GoldenDict — Variants Header: [exporter/variants/variants_header.html](../../exporter/variants/variants_header.html)

The file is copied to:

- WebApp: [exporter/webapp/static/dpd.css](../../exporter/webapp/static/dpd.css)

- Docs: [docs/stylesheets/dpd-variables.css](../../docs/stylesheets/dpd-variables.css)

---













<!-- This should definitely be simplified into one  -->
