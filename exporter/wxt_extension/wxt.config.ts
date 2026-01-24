import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  srcDir: '.',
  entrypointsDir: 'entrypoints',
  manifest: ({ browser }) => ({
    name: "Digital Pāḷi Dictionary",
    description: "Lookup Pāḷi words on any website",
    version: "1.0.0",
    icons: {
      "16": "icons/dpd-logo_16.png",
      "32": "icons/dpd-logo_32.png",
      "64": "icons/dpd-logo_64.png",
      "128": "icons/dpd-logo_128.png"
    },
    permissions: ["storage", "activeTab", "scripting"],
    host_permissions: [
      "https://dpdict.net/*",
      "http://0.0.0.0:8080/*"
    ],
    browser_specific_settings: browser === 'firefox' ? {
      gecko: {
        id: "digitalpalidictionary@digitalpalidictionary.github.io",
        strict_min_version: "109.0"
      }
    } : undefined
  }),
});
