"""Update the mkdocs How to Cite page.

Generated so that the example version is always the current release, the same
way abbreviations, bibliography and thanks are kept fresh."""

from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.version import (
    AUTHOR,
    EXAMPLE_ID,
    EXAMPLE_LEMMA,
    WEBSITE,
    get_doi,
    make_citation,
    release_date,
)


def make_how_to_cite_md(version: str, doi: str | None = None) -> str:
    permalink = f"{WEBSITE}?tab=dpd&q={EXAMPLE_ID}"
    citation = make_citation(version, doi)
    entry = (
        f'{AUTHOR}. "{EXAMPLE_LEMMA}." *Digital Pāḷi Dictionary*, '
        f"version {version}. <{permalink}>"
    )
    bare = permalink.replace("https://", "")
    year = release_date(version)[:4]

    doi_note = (
        f"\nThe DOI <https://doi.org/{doi}> always resolves to the newest release.\n"
        if doi
        else ""
    )

    return f"""# How to Cite DPD

DPD is revised every month. Always cite the version you used.

## The dictionary

> {citation}
{doi_note}
## A single entry

> {entry}

**Chicago (note)**

> {AUTHOR}, "{EXAMPLE_LEMMA}," *Digital Pāḷi Dictionary*, version {version},
> {permalink}.

**MLA**

> {AUTHOR}. "{EXAMPLE_LEMMA}." *Digital Pāḷi Dictionary*, version {version},
> {bare}.

**APA**

> {AUTHOR}. ({year}). {EXAMPLE_LEMMA}. In *Digital Pāḷi Dictionary*
> (version {version}). {permalink}

## Finding the version

**Online** — go to [dpdict.net]({WEBSITE}). The version is in the footer line at the
bottom of the page, right after the *how to cite* link.

**GoldenDict, MDict, DictTango** — look up **`cite`**. The entry gives you the whole
citation, with the version of the copy you have installed already filled in.

**DPD app** — the info menu, under **How to Cite**, with a copy button.

**PDF** — on the second page, under *How to cite this dictionary*.

**Database** — the `db_info` table has a `dpd_release_version` row, and a `citation` row
holding the finished citation.

## Finding the permalink

```
{WEBSITE}?tab=dpd&q=<id>
```

Look the word up on [dpdict.net]({WEBSITE}), click the **feedback** button in the row of
buttons under the entry, and the id is the first line — `ID {EXAMPLE_ID}`. Ids are
permanent and are never reused, so the link will always reach that same entry.

To cite a word rather than one particular entry of it, use the word itself:
`{WEBSITE}?tab=dpd&q=gacchati`

## From the repository

The [GitHub project page]({{github}}) has a **Cite this repository** button that
generates APA or BibTeX.

## Licence

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — see the
[licence page](license.md).
""".replace("{github}", "https://github.com/digitalpalidictionary/dpd-db")


def main() -> None:
    pr.tic()
    pr.yellow_title("updating mkdocs how to cite")
    pth = ProjectPaths()
    version = config_read("version", "version") or "unknown"
    pth.docs_how_to_cite_md_path.write_text(
        make_how_to_cite_md(version, get_doi()), encoding="utf-8"
    )
    pr.summary("how_to_cite.md", "ok")
    pr.toc()


if __name__ == "__main__":
    main()
