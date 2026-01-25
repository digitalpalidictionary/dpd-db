import { defineContentScript } from 'wxt/sandbox';
import { browser } from 'wxt/browser';
import { DictionaryPanel } from '../components/dictionary-panel';
import { addListenersToTextElements, removeListenersFromTextElements } from '../utils/utils';
import { applyTheme } from '../utils/themes';
import '@/assets/styles/chrome-extension.css';
import '@/assets/styles/dpd-variables.css';
import '@/assets/styles/dpd.css';

export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_end',
  main() {
    let panel: DictionaryPanel | null = null;

    // Define handleSelectedWord globally so utils and panel can call it
    (window as any).handleSelectedWord = (word: string) => {
      console.log("[DPD] Searching for:", word);
      // Normalize curly quotes to straight apostrophes
      // Remove common punctuation and numbers but PRESERVE internal spaces
      let cleanWord = word
        .replace(/[’‘“”]/g, "'")
        .replace(/[.,;:!?()\[\]{}\\\/"0-9]/g, "")
        .trim()
        .toLowerCase();

      // Handle double-click "word expansion" artifact for some Pāli words
      if (cleanWord.length >= 6 && cleanWord.length % 2 === 0 && !cleanWord.includes(" ")) {
        const mid = cleanWord.length / 2;
        if (
          cleanWord.slice(0, mid).toLowerCase() ===
          cleanWord.slice(mid).toLowerCase()
        ) {
          cleanWord = cleanWord.slice(0, mid);
        }
      }

      if (panel) {
        panel.setSearchValue(cleanWord);
        panel.setText("Loading...");
      }

      browser.runtime.sendMessage(
        {
          action: "fetchData",
          url: "https://dpdict.net/search_json?q=" + encodeURIComponent(cleanWord),
        }
      ).then((response: any) => {
          if (response?.success) {
            const data = response.data;
            if (!data || (!data.summary_html && !data.dpd_html)) {
              panel?.setText("No results for " + cleanWord);
            } else {
              panel?.setText("Result for " + cleanWord);
              panel?.setContent(
                (data.summary_html || "") + '<hr class="dpd">' + (data.dpd_html || ""),
              );
            }
          } else {
            panel?.setText("Error: " + (response?.error || "Unknown error"));
          }
      }).catch(err => {
         panel?.setText("Error: " + err.message);
      });
    };

    async function init() {
      if (panel) return;
      document.documentElement.classList.add("dpd-active");
      document.body.classList.add("dpd-active");

      // Wrap content to avoid interference (or whatever the original reason was)
      if (!document.getElementById("main-content-32050248")) {
        const container = document.createElement("div");
        container.id = "main-content-32050248";
        Array.from(document.body.childNodes).forEach((node) => {
          if (node.nodeName !== "SCRIPT" && (node as Element).id !== "dict-panel-25445")
            container.appendChild(node);
        });
        document.body.appendChild(container);
      }

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

    const AUTO_DOMAINS = [
      "suttacentral.net",
      "suttacentral.express",
      "digitalpalireader.online",
      "thebuddhaswords.net",
      "tipitaka.org",
      "tipitaka.lk",
      "open.tipitaka.lk",
    ];
    if (AUTO_DOMAINS.some((d) => window.location.hostname.includes(d))) {
        init();
    } else {
      browser.storage.local.get(`state_${window.location.hostname}`).then((data) => {
        if (data[`state_${window.location.hostname}`] === "ON") init();
      });
    }
  },
});
