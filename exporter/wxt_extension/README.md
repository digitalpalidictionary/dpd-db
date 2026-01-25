# DPD WXT Extension

This directory contains the source code for the Digital Pāḷi Dictionary browser extension, rebuilt using the [WXT framework](https://wxt.dev/) for cross-browser compatibility (Chrome and Firefox) and written in TypeScript.

## Project Structure

- `entrypoints/`: Main entrypoints for the extension (background, content scripts).
- `components/`: UI components (e.g., `DictionaryPanel`).
- `utils/`: Helper modules (themes, sorting, general utilities).
- `assets/`: Icons and CSS files.
- `public/`: Static assets copied to the extension root.
- `types/`: TypeScript type definitions.

## Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server (with hot reload):
   ```bash
   # For Chrome
   npm run dev:chrome

   # For Firefox (Manifest V2 during dev)
   npm run dev:firefox
   ```

   *Note: `dev:firefox` uses Manifest V2 because WXT's hot-reloading tool does not yet support MV3 for Firefox. Production builds still use MV3.*

## Build

To build for production:

```bash
# Build for both Chrome and Firefox
npm run build

# Build AND zip for sharing (one-liner)
npm run package

# Build specific browser
npm run build:chrome
npm run build:firefox
```

The output will be in `.output/chrome-mv3` and `.output/firefox-mv3`.

## Packaging for Sharing

To create zip files for sharing or testing:

```bash
# Zip both Chrome and Firefox
npm run zip

# Zip specific browser
npm run zip:chrome
npm run zip:firefox

# Build AND Zip both in one command
npm run package
```

The zip files will be created in the `.output/` directory.

## Deployment

- **Chrome**: Zip the `.output/chrome-mv3` folder and upload to Chrome Web Store.
- **Firefox**: Zip the `.output/firefox-mv3` folder (as `.xpi`) and upload to AMO.

## Implementation Details

- **TypeScript**: Strict mode enabled, full typing for browser APIs and internal data structures.
- **Cross-Browser**: Uses `webextension-polyfill` via WXT for a unified `browser` API.
- **Modern Build**: Uses Vite for fast compilation and bundling.