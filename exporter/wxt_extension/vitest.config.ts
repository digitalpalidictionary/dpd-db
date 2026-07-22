import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing';

// WxtVitest wires up the `@/` aliases, the `wxt/browser` polyfill (fake-browser),
// and import.meta.env.BROWSER so util modules import cleanly under test. happy-dom
// gives the pure helpers the window/document they touch (themes' dark detection);
// jsdom is avoided as it overrides Uint8Array and trips esbuild's transform.
export default defineConfig({
  plugins: [WxtVitest()],
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.test.ts'],
  },
});
