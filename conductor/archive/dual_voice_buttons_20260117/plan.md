# Plan: Dual Voice Play Buttons

## Phase 1: Research and Analysis
- [x] Task: Identify existing play button HTML and JavaScript implementation in GoldenDict exporter and Webapp.
- [x] Task: Locate the IPA rendering logic in the grammar tab for both platforms.
- [x] Task: Verify the exact URL parameter format for male/female voice requests.

## Phase 2: CSS Styling and Tooltip Implementation
- [x] Task: Add styles for the small triangular buttons (circle/triangle inversion) to `identity/css/`.
- [x] Task: Add global tooltip styles (blue background, white text) to `identity/css/`.
- [x] Task: Run `tools/css_manager.py` to distribute updated CSS across the project.

## Phase 3: GoldenDict Exporter Implementation
- [x] Task: Update the GoldenDict HTML generation logic to include male/female buttons after the IPA.
- [x] Task: Ensure JavaScript in GoldenDict handles the new button clicks and URL parameters correctly.

## Phase 4: Webapp Implementation
- [x] Task: Update the Webapp templates/components to include male/female buttons in the grammar tab.
- [x] Task: Ensure Webapp JavaScript handles the new button clicks and URL parameters correctly.

## Phase 5: Final Verification
- [ ] Task: Manually verify GoldenDict export output (User testing in progress).
- [x] Task: Manually verify Webapp interface and audio playback (Approved).
