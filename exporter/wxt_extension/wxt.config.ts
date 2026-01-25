import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  srcDir: '.',
  entrypointsDir: 'entrypoints',
  manifest: ({ browser }) => ({
    name: "DPD Dictionary",
    description: "Search Digital Pāḷi Dictionary by double-clicking any word on any website.",
    version: "1.0",
    icons: {
      "16": "icons/dpd-logo_16.png",
      "32": "icons/dpd-logo_32.png",
      "64": "icons/dpd-logo_64.png",
      "128": "icons/dpd-logo_128.png"
    },
    action: {
      default_icon: {
        "16": "icons/dpd-logo-gray_16.png",
        "32": "icons/dpd-logo-gray_32.png",
        "64": "icons/dpd-logo-gray_64.png",
        "128": "icons/dpd-logo-gray_128.png"
      }
    },
    permissions: ["storage", "activeTab", "scripting"],
    web_accessible_resources: [
      {
        resources: ["icons/*.png", "icons/*.svg", "*.png", "*.css"],
        matches: ["<all_urls>"]
      }
    ],
    host_permissions: [
      "https://dpdict.net/*",
      "http://0.0.0.0:8080/*",
      "http://127.0.0.1:8080/*",
      "http://127.1.1.1:8080/*",
      "http://localhost:8080/*"
    ],
    browser_specific_settings: browser === 'firefox' ? {
      gecko: {
        id: "digitalpalidictionary@digitalpalidictionary.github.io",
        strict_min_version: "109.0"
      }
    } : undefined
  }),
});
