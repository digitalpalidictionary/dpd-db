# Device test protocol

Two dictionaries, built 2026-09-13 from **one identical render** of the current
`dpd.db` (189,505 entries). Same data, same templates — the only difference is
the compiler.

| File | Built by | Size |
|---|---|---|
| `exporter/share/dpd-kindle-kindlegen.mobi` | kindlegen V2.9 (today's tool) | 75.2 MB |
| `exporter/share/dpd-kindle-kindling.mobi` | kindling 0.45.1 | 40.1 MB |

## Setup

Copy **both** files to `/documents/dictionaries` on the Kindle, restart the
device, then long-press a Pāḷi word and pick the dictionary from the list. Both
will appear under the same title, so rename one on the device first if you
cannot tell them apart — or test one, delete it, then test the other. Testing
them one at a time is safer.

## The words to tap

The first group is the whole point: every one of these is an **inflected form**,
not a headword. kindlegen stores them in a separate inflection index; kindling
puts them in the main index. If these fail in the kindling build and work in the
kindlegen build, the migration is dead.

| Word | Why it is in the list |
|---|---|
| `dhammassa` | plain inflection of a very common noun |
| `bhikkhussa` | inflection, different declension |
| `buddhaṃ` | inflection ending in niggahita |
| `ariyasaccaṃ` | inflection of a compound headword |
| `gacchati` | verb form |
| `bhikkhūti` | sandhi form, resolves through the deconstructor |
| `evaṃvipāko` | inflected form of a compound |

Second group — headwords, which should be uncontroversial, and are there to
prove the dictionary is working at all before you trust a failure above:

`dhamma` · `ṭhāna` · `okkamati`

(`evaṃvipāko` was in this group by mistake — it is an inflected form, not a
headword, so it belongs in group 1. Tap it there.)

Third group — the known weak spot. `okārassa` is an inflected form claimed by
more than one entry (88,775 of our forms are). In the new build each form points
at exactly one entry. **Look at what the popup shows, and whether scrolling in
the popup reveals the other senses.** Compare the two builds carefully here:

`okārassa` · `okkamati` (a headword spelled the same as another headword)

Fifth group — the new build splits the text into **3 sections** where the old
one used 1, which is exactly the kind of structural change old firmware can
mishandle. `suffering` sits in the third section, so if it opens, all three
sections are reachable.

Fourth group — the English-to-Pāḷi side, which also lives in this file:

`suffering` · `compassion`

## What to report back

For each build, three things:

1. Did the inflected words in group 1 resolve at all?
2. For `okārassa`, did you see one sense or several?
3. Anything that looks wrong — layout, missing text, a popup that will not open.

Every word above already resolves in the build-side simulation of the kindling
file, so a failure on the device is exactly the information this test exists to
produce. The simulation is explicitly not a hardware oracle.
