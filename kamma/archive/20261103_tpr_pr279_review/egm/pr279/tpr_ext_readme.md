# Extension packages

An extension package is a SQLite file that carries its own install steps. The
app runs it with `lib/services/extensions/extension_packages.dart`. Use a
package instead of a `.sql` extension: it installs whole or not at all, it is
kept on the device, and it is applied again after an app update replaces the
databases.

## Layout (format 1)

```sql
meta (key TEXT PRIMARY KEY, value TEXT)
  -- id        letters, digits, _; the file is kept as packages/<id>.db
  -- version   integer; a higher one is applied over a lower one
  -- title, description
  -- format    1; an app that knows only older formats refuses the package

commands (
  seq    INTEGER PRIMARY KEY,                 -- run in this order
  phase  TEXT NOT NULL DEFAULT 'install',     -- install / remove
  op     TEXT NOT NULL,                       -- sql / copy / reindex
  target TEXT,
  arg    TEXT
)

-- plus any tables the steps copy from
```

| op | target | arg | does |
| --- | --- | --- | --- |
| `sql` | | a statement | runs it. The package is attached as `pkg`, the main database is `main`, the sentence extension `ext`, ePitaka `epi` |
| `copy` | `main.<table>` or `ext.<table>` | a table in the package | `INSERT OR REPLACE` every row, by the columns the two tables share |
| `reindex` | | ePitaka book ids, comma separated | brings the search index up to date for those books afterwards |

All `sql` and `copy` steps of a phase run in one transaction. An unknown step,
or a copy into anything other than `main` or `ext`, is refused before anything
runs.

Steps must be safe to run again. Tables without a key (`page_break`,
`page_mark`, `paragraphs`) get no help from `INSERT OR REPLACE`, so start the
install with `sql` steps that delete the rows the package owns. A `remove`
phase is usually those same deletes plus the `reindex`.

## Delivering one

Zip the file with a name ending in `.pkg.db`. That ending is how the app tells
a package zip from an old-style extension zip. In the download list, give the
entry `"type": "package"`:

```json
{
  "name": "Abhidhamma handbooks (Abhidhammāvatāra, Mohavicchedanī …)",
  "release_date": "18.10.2026",
  "type": "package",
  "category": "Books",
  "url": "https://github.com/bksubhuti/tpr_downloads/releases/download/<tag>/missing_books.pkg.zip",
  "filename": "missing_books.pkg.zip",
  "size": "0.2 MB"
}
```

To test without publishing, copy the `.pkg.db` to `packages/<id>.db` in the
app's data folder. The next start applies it, because nothing has been
recorded as applied yet.

## build_missing_books.py

Builds `missing_books.pkg.db` for ePitaka books TPR had no pages for, paged by
the Myanmar page numbers in VRI's XML
(github.com/VipassanaTech/tipitaka-xml, `romn/<vri_id>.xml`, downloaded when
missing). ePitaka's `para_id` is the position of the `<p>` in that file, so
each marker is placed by aligning the words of one paragraph. A book that runs
over two printed volumes becomes two TPR books, `(pa)` and `(du)`, with the
printed page numbers. The report lists the pages per book and any break placed
inside a stretch where the two texts are worded differently.

The book list is `BOOKS` at the top of the script. Raise `PACKAGE_VERSION`
whenever the output changes, so devices that have the package apply the new
one.
