# DPD for Anki

A DPD vocabulary deck is available for [Anki](https://apps.ankiweb.net){target="_blank"}, the popular flashcard app. It works on desktop, AnkiDroid and AnkiMobile.

## Install

(1) Download the latest version of **dpd-anki.apkg** from **[the releases page on GitHub](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"}**.

(2) Double-click **dpd-anki.apkg**. Anki opens and imports the deck.

That's it. The deck appears in your deck list, ready to study.

## Updating

When a new version is released, download and open the latest **dpd-anki.apkg** again. Anki will recognise the existing deck and ask if you want to update it. Choose to update.

<!-- placeholder: screenshot of the Anki update prompt -->
<!-- ![update prompt](../pics/anki/anki_update.png) -->

## Theme

You can change the colours and fonts of the cards by editing the card styling (CSS). The theme is controlled by the `:root` colour variables at the top of the styling.

These are the settings used to make the default DPD theme:

```css
:root {
  --label: hsl(205, 79%, 48%);
  --hl:    hsl(198, 100%, 50%);
  --soft:  hsl(198, 100%, 95%);
  --bg:    hsl(198, 100%, 5%);
}
```

Change the `hsl(...)` values to set your own colours, then save.

### Anki Desktop

(1) Click **Browse** to open the card browser.

(2) Select any DPD card.

(3) Click **Cards…**.

(4) Open the **Styling** tab and edit the CSS.

(5) Close the window to save.

### AnkiDroid

(1) Open the **Card Browser** and tap a DPD card.

(2) Tap the **⋮** menu and choose **Edit note**.

(3) Tap the **⋮** menu again and choose **Cards…**.

(4) Open the **Styling** section and edit the CSS.

(5) Tap the **back arrow** to save.
