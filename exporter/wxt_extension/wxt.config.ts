import { defineConfig } from 'wxt';

export default defineConfig({
  srcDir: '.',
  entrypointsDir: 'entrypoints',
  manifest: {
    name: "Digital Pāḷi Dictionary",
    permissions: ["storage", "activeTab", "scripting"],
  }
});
