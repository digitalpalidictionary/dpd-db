# Specification: Integrate Play Button into GoldenDict Exporter

## Overview
This track involves porting the "Play Audio" feature from the DPD WebApp to the GoldenDict exporter. This allows users to hear the pronunciation of headwords directly within GoldenDict, fetching the audio from the `dpdict.net` servers.

## Functional Requirements
1.  **UI Component:** Add a play button (with an SVG icon) to the headword summary section in GoldenDict, matching the styling and positioning of the WebApp.
2.  **Audio Playback:** Implement a `playAudio` JavaScript function in GoldenDict's `main.js` that:
    -   Constructs a URL to `https://www.dpdict.net/audio/<headword>?gender=<gender>`.
    -   Handles gender selection (defaulting to "male").
    -   Plays the audio using the standard browser `Audio` API.
3.  **Headword Cleaning:** When constructing the audio URL, any trailing digits or numbers from the `lemma_1` (e.g., "dhamma 1.1") must be removed to match the audio database keys (e.g., "dhamma").
4.  **Error Handling:** If audio is missing (404), the button should visually indicate failure (e.g., change icon to a cross) and become disabled, mirroring WebApp behavior.
5.  **Styling:** Ensure the `a.button.play` CSS in `identity/css/dpd.css` is correctly applied to the GoldenDict output.

## Technical Requirements
-   **Templates:** Update `exporter/goldendict/templates/dpd_button_box.html`.
-   **Exporter Logic:** Update `exporter/goldendict/export_dpd.py` to generate the play button HTML.
-   **JavaScript:** Append or integrate the `playAudio` logic into `exporter/goldendict/javascript/main.js`.
-   **Network:** The audio will be fetched from `https://www.dpdict.net`, requiring an internet connection for this specific feature.

## Acceptance Criteria
-   A play button appears for headwords in the GoldenDict export.
-   Clicking the button plays the correct audio from the DPD server.
-   Trailing digits in headwords are correctly handled for audio fetching.
-   The button handles missing audio gracefully by changing its state.
-   The visual appearance matches the WebApp (colors, SVG icon, hover states).

## Out of Scope
-   Packaging audio files offline (due to 1.5GB size).
-   Advanced audio settings (e.g., speed control).
