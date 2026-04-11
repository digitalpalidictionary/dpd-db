import { defineContentScript } from 'wxt/sandbox';
import { browser } from 'wxt/browser';
import { DictionaryPanel } from '../components/dictionary-panel';
import { addListenersToTextElements, removeListenersFromTextElements, cleanWord } from '../utils/utils';
import { applyTheme } from '../utils/themes';
import { isAutoDomain, isExcludedDomain } from '../utils/domains';
import '@/assets/styles/chrome-extension.css';
import '@/assets/styles/dpd-variables.css';
import '@/assets/styles/dpd.css';

type ApiBaseUrlResponse = {
  baseUrl?: string;
};

export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_end',
  main() {
    let panel: DictionaryPanel | null = null;

    // Define handleSelectedWord globally so utils and panel can call it
    (window as any).handleSelectedWord = async (word: string) => {
      const cleanedWord = cleanWord(word);
      
      // Check "Use GoldenDict" setting - if ON, always use GoldenDict
      if (panel?.settings?.goldenDict) {
        panel.openInGoldenDict(cleanedWord);
        return;
      }

      // Get API route for logging
      try {
        const response = await browser.runtime.sendMessage({ action: "getApiBaseUrl" }) as ApiBaseUrlResponse;
        const baseUrl = response?.baseUrl || "https://dpdict.net";
        const isProduction = baseUrl === "https://dpdict.net";
        const routeDescription = isProduction ? "via dpdict.net" : `via local server ${baseUrl}`;
        console.log(`[DPD] Searching for: ${word} ${routeDescription}`);
      } catch (e) {
        console.log("[DPD] Searching for:", word, "(route detection failed)");
      }

      if (panel) {
        panel.setSearchValue(cleanedWord);
        panel.setText("Loading...");
      }

      // Check if offline - use GoldenDict fallback
      if (!navigator.onLine) {
        panel?.openInGoldenDict(cleanedWord);
        return;
      }

      browser.runtime.sendMessage(
        {
          action: "fetchData",
          endpoint: "/search_json?q=" + encodeURIComponent(cleanedWord),
        }
      ).then((response: any) => {
          if (response?.success) {
            const data = response.data;
            if (!data || (!data.summary_html && !data.dpd_html)) {
              panel?.setText("No results for " + cleanedWord);
            } else {
              panel?.setText("Result for " + cleanedWord);
              panel?.setContent(
                (data.summary_html || "") + '<hr class="dpd">' + (data.dpd_html || ""),
              );
            }
          } else {
            // API error - use GoldenDict fallback
            panel?.openInGoldenDict(cleanedWord);
          }
      }).catch(err => {
          // API failure - use GoldenDict fallback
          panel?.openInGoldenDict(cleanedWord);
      });
    };

    async function init() {
      if (panel) return;
      document.documentElement.classList.add("dpd-active");
      document.body.classList.add("dpd-active");

      addListenersToTextElements();
      panel = new DictionaryPanel();
      (window as any).panel = panel; // Assign to window so inline event handlers work

      // Show info on first run
      const data = await browser.storage.local.get("isFirstRun");
      if (data.isFirstRun !== false) {
          // Access private method if needed, or make public. _showInfo is private in my TS class.
          // I should make it public or ignore TS error.
          (panel as any)._showInfo();
          await browser.storage.local.set({ isFirstRun: false });
      }

      const domain = window.location.hostname;
      const storageKey = `theme_${domain}`;
      const storage = await browser.storage.local.get(storageKey);
      const savedTheme = (storage[storageKey] as string) || "auto";
      applyTheme(savedTheme);

      // Notify background that we've started to sync icon state
      browser.runtime.sendMessage({ action: "started" });

      // If auto, try again shortly in case the SPA theme applied late
      if (savedTheme === "auto") {
        setTimeout(() => applyTheme("auto"), 300);
        setTimeout(() => applyTheme("auto"), 1000);
      }

      // Watch for theme changes on the host page
      const observer = new MutationObserver(() => {
        browser.storage.local.get(storageKey).then((data) => {
          if (((data[storageKey] as string) || "auto") === "auto") {
            applyTheme("auto");
          }
        });
      });
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class", "theme", "data-theme"],
      });
      // Also watch body as some sites put themes there
      observer.observe(document.body, {
        attributes: true,
        attributeFilter: ["class", "theme", "data-theme"],
      });
    }

    browser.runtime.onMessage.addListener((request: any) => {
      if (request === "init") init();
      if (request === "destroy") {
        document.documentElement.classList.remove("dpd-active");
        document.body.classList.remove("dpd-active");
        panel?.destroy();
        panel = null;
        removeListenersFromTextElements();
      }
    });

    const hostname = window.location.hostname;

    browser.storage.local.get(`state_${hostname}`).then((data) => {
      const savedState = data[`state_${hostname}`];
      
      if (savedState === "ON") {
        init();
      } else if (savedState === "OFF") {
        // User explicitly turned it off - do nothing
      } else if (!isExcludedDomain(hostname) && isAutoDomain(hostname)) {
        // No saved state, use default behavior for auto-domains
        init();
      }
    });
  },
});
