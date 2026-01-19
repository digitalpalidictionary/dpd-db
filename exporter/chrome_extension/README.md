# DPD Chrome Extension

## Build and Zip

### One-liner (from project root)
```bash
cd exporter/chrome_extension && npm install && npm run build && npm run zip
```

### Step-by-step
1.  **Navigate to the directory:**
    ```bash
    cd exporter/chrome_extension
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Build assets:**
    ```bash
    npm run build
    ```

4.  **Create zip package:**
    ```bash
    npm run zip
    ```

## Installation

1.  Open Chrome and navigate to `chrome://extensions/`.
2.  Enable **Developer mode** (top right toggle).
3.  **Option A (Developer):** Click **Load unpacked** and select the `exporter/chrome_extension` folder.
4.  **Option B (Zip):** Drag and drop the `dpd-chrome-extension.zip` file into the extensions page.
