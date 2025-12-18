"""
A general lookup system using dpd-db

The starting point is an inflected *word* in a Pāḷi text.

- A *word* is all characters up until the next space, comma, semicolon, fullstop or exclamation mark, with all hyphens, single and double quote characters removed.
- e.g. if a text contains `visattika"nti.` the word is `visattikanti`


lookup the word in inflection_to_headwords table (!1)
if result
    render html of each headword using the `generate_dpd_html` in `/exporter/goldendict/export_dpd.py`
    if headword contains "√":
        render html using the `generate_root_html` funcbtion in `exporter/export_roots.py`
    furthermore lookup word in sandhi table: (!2)
    if result:
        render html of deconstructor data
else:
    lookup word in sandhi table: (!2)
    if result:
        render html of deconstructor data
    else:
        sorry, word not in dpd-db

display compiled html

!1 this data is currently generated here `db/inflections/inflections_to_headwords.py` but yet added to the db model or db tables
!2 this will probably be renamed at some point

"""
