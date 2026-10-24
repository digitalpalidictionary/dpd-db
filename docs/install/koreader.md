# DPD for KOReader

Read Pāḷi with DPD right inside [KOReader](https://koreader.rocks){target="_blank"}, the free e-book reading app that runs on Kindle, Kobo, PocketBook and many other devices.

Long-press any Pāḷi word while you are reading, and the DPD entry pops up on the page. All the meanings appear together, compounds are broken into their parts, and the grammar tables are a tap away. Close the popup and you are back on your page, exactly where you left off.

The plugin is made by [Ven. Nirodhavihārī](https://github.com/nirodhav){target="_blank"} and uses the full DPD mobile database, so it works offline, on the device. It is a free download from the [plugin's releases page](https://github.com/digitalpalidictionary/dpd-koreader/releases/latest){target="_blank"}.

![DPD for KOReader: compounds explained in one lookup, every sense in one view, declensions and conjugations](../pics/koreader/hero_light.png#only-light)
![DPD for KOReader: compounds explained in one lookup, every sense in one view, declensions and conjugations](../pics/koreader/hero_dark.png#only-dark)

## What It Shows

- every sense of the word in one popup, not one at a time
- compounds split into their parts, each with a brief meaning — tap a part to expand it, or follow it to its own entry
- declension and conjugation tables, roots, families and frequency
- search in Pāḷi or English, with spelling suggestions
- DPD's other dictionaries too, such as CPD and DPPN

Here a long compound from a sutta is looked up while reading. Each part of the compound is listed with its own meaning:

![a compound looked up while reading, split into its parts](../pics/koreader/main_light.png#only-light){width="360"}
![a compound looked up while reading, split into its parts](../pics/koreader/main_dark.png#only-dark){width="360"}

And here are the senses of *dhammaṃ*, with one expanded in place:

![the senses of dhammaṃ, one expanded](../pics/koreader/lookup_light.png#only-light){width="360"}
![the senses of dhammaṃ, one expanded](../pics/koreader/lookup_dark.png#only-dark){width="360"}

## Installation

You will need KOReader v2026.07 or newer (on a Kindle this means a jailbroken device) and about 1.1 GB of free space.

1. Download the plugin zip from the [releases page](https://github.com/digitalpalidictionary/dpd-koreader/releases/latest){target="_blank"} and extract it into `koreader/plugins/` on the device.
2. Download `dpd-mobile-db.zip` from the [latest DPD release](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"} and copy the `dpd-mobile.db` inside it to `koreader/data/dpd/`.
3. Restart KOReader. **Database status** in the DPD menu should say **Core columns: OK**.

Full instructions are in the plugin's [usage guide](https://github.com/digitalpalidictionary/dpd-koreader/blob/main/docs/USAGE.md){target="_blank"}, which is also included in the download.

## Keeping DPD Up to Date

DPD has a new release every month, on the Uposatha day. To update:

1. Download `dpd-mobile-db.zip` from the [latest DPD release](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"}.
2. Exit KOReader, replace `koreader/data/dpd/dpd-mobile.db` with the new one, and delete any `-wal` and `-shm` files beside it.
3. Restart KOReader. **Database status** in the DPD menu shows the new release.

The DPD menu lives under **Search → Digital Pāḷi Dictionary**:

![the DPD menu in KOReader](../pics/koreader/database_status_menu_light.png#only-light){width="400"}
![the DPD menu in KOReader](../pics/koreader/database_status_menu_dark.png#only-dark){width="400"}

![database status: core columns OK](../pics/koreader/database_status_light.png#only-light){width="400"}
![database status: core columns OK](../pics/koreader/database_status_dark.png#only-dark){width="400"}

## Bugs and Feedback

Please report bugs on the [issue tracker](https://github.com/digitalpalidictionary/dpd-koreader/issues){target="_blank"}, or write to [dpd-koreader@nirodha.8shield.net](mailto:dpd-koreader@nirodha.8shield.net).
