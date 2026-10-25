# DPD Newsletter Builder

Markdown → branded, responsive HTML email for the monthly DPD newsletter.

## Monthly workflow

```bash
just newsletter-new 2026-12     # 1. start the month from the template
just newsletter-preview         # 2. live preview: edit newsletter.md, drop pics into pics/,
                                #    the browser reloads on every save (Ctrl-C to stop)
just newsletter-publish         # 3. Gmail draft with the pics embedded;
                                #    on uposatha days also adds it to docs/newsletters.md
# open Gmail → Drafts → address to group 1 → send
# next day: same draft for group 2 (duplicate it before sending)
# commit docs/newsletters.md + docs/pics/newsletters/<YYYY-MM>/ to publish the docs page
```

Preview and publish use the newest month folder unless you name one.

## Layout

```
newsletter/
├── newsletter_build.py       the builder
├── newsletter_template.md    copied into each new month
├── useful_links.md          the "Useful DPD links" footer every mail shares
├── README.md                 this file
└── <YYYY-MM>/
    ├── newsletter.md         what you write
    ├── pics/                 images for this month
    └── preview.html          generated, gitignored
```

## Writing the newsletter

Everything above the first `# heading` is ignored; that heading becomes the
subject line. The greeting is yours to write; the signoff ("With much
*mettā*, Bodhirasa") is added by the template — don't type it.

Structure that matches the usual mail:

```markdown
# Digital Pāḷi Dictionary update (July 2026)

Dear Venerable monastics, professors, and Pāḷi enthusiasts,

Intro sentence or two.

## Topic Heading

Body text with **bold** and [links](https://example.com).

![a caption](pics/example.jpg)

## Latest Release

* [DPD online](https://www.dpdict.net/)
* ...

## Useful Links

* ...
```

Each `## heading` renders with the DPD cyan underline.

The "Useful DPD links" footer lives in `useful_links.md`, shared by every
month. Each line there is its own line in the mail; a blank line starts a new
group. Edit it while the preview runs and the page reloads.

## Outputs

- `preview.html` — generated next to the markdown. `just newsletter-preview`
  serves it on a local port and reloads the browser on every save, keeping
  your scroll position.
- **Gmail draft** — `just newsletter-publish` creates a draft with the pics
  embedded as inline attachments (nothing is hosted anywhere; images travel
  with the mail). Auth is the app password in `config.ini` (`[gmail]` →
  `mail`, `password`) — no Google sign-in, ever.
- **Docs page** — on uposatha days only, publish also puts the newsletter at
  the top of `docs/newsletters.md` (section headings one level down, under the
  date) and copies its pics to `docs/pics/newsletters/<YYYY-MM>/`. Publishing
  again replaces that entry. The RSS feed is built from this page.

**Pictures.** Gmail never shrinks pictures, so the builder does. Each picture
is shown inside a box 520 px wide and 560 px tall (what Gmail's "best fit"
gave past newsletters, so phone screenshots show narrow). On publish, a
picture is cut down to twice that size and saved as PNG or JPEG, whichever is
smaller; small screenshots go out untouched. Your originals in `pics/` never
change. Publish prints the total mail size.

The builder warns when the HTML approaches Gmail's ~102 KB clipping limit.
