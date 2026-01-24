# Specification: Dual Voice Play Buttons

## Overview
Add two small triangular play buttons (Male and Female voices) to the grammar tab in both the DPD GoldenDict exporter and the Webapp. These buttons will be placed directly after the IPA (International Phonetic Alphabet) and will allow users to quickly toggle between two pronunciations.

## Functional Requirements
- **Dual Voice Support:** Provide separate buttons for male and female voices.
- **Audio Retrieval:** Use a URL parameter to specify the voice in the audio request (e.g., `?voice=male` or `?voice=female`).
- **JavaScript Integration:** Replicate the existing play button logic for audio playback, including handling cases where audio is unavailable.
- **Placement:** Position the buttons immediately following the IPA text in the grammar tab.

## UI/UX Requirements
- **Button Styling:**
    - Use the same small triangle icon as the current play button.
    - Surround the triangle with a smaller circle compared to the standard button.
    - The circle color must match the text color, and the triangle icon must match the background color (inverted style).
- **Tooltips:**
    - Add tooltips: "Male Voice" and "Female Voice".
    - Apply a global CSS theme: Blue background and white text for all tooltips (CSS rule: `.tooltip { background-color: theme-blue; color: white; }` or equivalent).

## Non-Functional Requirements
- **Consistency:** Maintain visual and functional parity between the GoldenDict exporter and the Webapp.
- **Maintainability:** Use centralized CSS (via `identity/css/`) for styling.
- **No UI Testing:** Per project guidelines, UI, CSS, and HTML changes will be manually verified.

## Acceptance Criteria
- [ ] Male and female play buttons appear after the IPA in the grammar tab.
- [ ] Clicking the male button plays the male voice.
- [ ] Clicking the female button plays the female voice.
- [ ] Tooltips appear on hover with the correct text and styling.
- [ ] JavaScript gracefully handles missing audio files as per existing patterns.

## Out of Scope
- Adding audio for words that currently have no audio files.
- Changing the primary play button behavior elsewhere in the dictionary.
