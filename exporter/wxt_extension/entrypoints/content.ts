import { defineContentScript } from 'wxt/sandbox';
import { browser } from 'wxt/browser';
import { DictionaryPanel } from '../components/dictionary-panel';
import { addListenersToTextElements, removeListenersFromTextElements, cleanWord } from '../utils/utils';
import { applyTheme, detectTheme } from '../utils/themes';
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
    let poppedOut = false; // true while the dictionary lives in its own popout window
    let themeObserver: MutationObserver | null = null;
    let themeDebounce: ReturnType<typeof setTimeout> | null = null;
    let myTabId: number | null = null; // this tab's id, learned from the "started" reply

    // Define handleSelectedWord globally so utils and panel can call it
    (window as any).handleSelectedWord = async (word: string) => {
      // While popped out, route selections to the popout window instead of the
      // (now hidden) in-page panel.
      if (poppedOut) {
        browser.runtime.sendMessage({ action: "popoutSearch", q: word, tab: myTabId }).catch(() => {});
        return;
      }

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

    function currentQuery(): string {
      return panel?.searchInput?.value?.trim() ?? "";
    }

    // Resolve the theme this page is showing to a concrete key, so the popout can
    // reproduce it with applyTheme(key). "auto" is resolved here (via detectTheme,
    // which needs the live page DOM) into a named key like "s4nt_dark"; only a truly
    // unrecognised site stays "auto" and the popout falls back to its own detection.
    async function currentThemeKey(): Promise<string> {
      const key = `theme_${window.location.hostname}`;
      const stored = await browser.storage.local.get(key);
      const saved = (stored[key] as string) || "auto";
      return saved === "auto" ? detectTheme() : saved;
    }

    // Add the "pop out" button to the panel header and enrich the logo tooltip.
    // Popout is Chromium-only: on Firefox the detached extension-page window never
    // renders and its messaging misbehaves, so we don't offer the feature there. This
    // is the single entry point, so gating it disables the whole popout flow on Firefox.
    function injectPopoutButton() {
      if ((import.meta as any).env.BROWSER === "firefox") return;
      const panelEl = document.getElementById("dict-panel-25445");
      if (!panelEl) return;

      const logoTip = panelEl.querySelector<HTMLElement>(".dpd-logo-link .dpd-tooltip-text");
      if (logoTip && !logoTip.dataset.dpdEnhanced) {
        logoTip.dataset.dpdEnhanced = "1";
        logoTip.innerHTML =
          "• Click to open dpdict.net in a new tab<br>" +
          "• To turn DPD off on this page, click the DPD icon in your browser's toolbar";
        logoTip.style.whiteSpace = "normal";
        logoTip.style.textAlign = "left";
        logoTip.style.width = "max-content";
        logoTip.style.maxWidth = "240px";
        logoTip.style.left = "0";
        logoTip.style.transform = "none";
      }

      const group = panelEl.querySelector(".dpd-action-group");
      if (!group || group.querySelector("#dpd-popout-btn")) return;
      const btn = document.createElement("button");
      btn.id = "dpd-popout-btn";
      btn.type = "button";
      btn.className = "dpd-tooltip";
      btn.innerHTML =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>';
      const tip = document.createElement("span");
      tip.className = "dpd-tooltip-text";
      tip.textContent = "Detach the dictionary into its own window";
      btn.appendChild(tip);
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        const theme = await currentThemeKey();
        browser.runtime.sendMessage({ action: "openPopout", q: currentQuery(), theme }).catch(() => {});
      });
      group.insertBefore(btn, group.firstChild);
    }

    // Hide/show the in-page panel and reclaim its reserved space when popped out.
    function setPoppedOut(on: boolean) {
      poppedOut = on;
      const panelEl = document.getElementById("dict-panel-25445");
      if (panelEl) panelEl.style.display = on ? "none" : "";
      document.documentElement.classList.toggle("dpd-popped-out", on);
    }

    async function init() {
      if (panel) return;
      document.documentElement.classList.add("dpd-active");
      document.body.classList.add("dpd-active");

      addListenersToTextElements();
      panel = new DictionaryPanel();
      (window as any).panel = panel; // Assign to window so inline event handlers work
      injectPopoutButton();

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

      // Notify background that we've started to sync icon state; it replies with this
      // tab's id, which we stamp on forwarded popout selections (see handleSelectedWord).
      browser.runtime
        .sendMessage({ action: "started" })
        .then((r: any) => {
          if (r?.tabId != null) myTabId = r.tabId;
        })
        .catch(() => {});

      // If auto, try again shortly in case the SPA theme applied late
      if (savedTheme === "auto") {
        setTimeout(() => applyTheme("auto"), 300);
        setTimeout(() => applyTheme("auto"), 1000);
      }

      // Watch for theme changes on the host page. Debounced and de-duplicated: a busy
      // page can fire hundreds of attribute mutations a second, so we coalesce them and
      // only re-apply when the resolved theme actually changed — otherwise an unthrottled
      // storage.local.get + applyTheme per mutation floods the extension process and
      // leaks memory badly. Also self-disconnects if the extension context is invalidated.
      let lastAutoTheme = detectTheme();
      themeObserver = new MutationObserver(() => {
        if (!browser.runtime?.id) {
          themeObserver?.disconnect();
          return;
        }
        if (themeDebounce) return;
        themeDebounce = setTimeout(() => {
          themeDebounce = null;
          browser.storage.local
            .get(storageKey)
            .then((data) => {
              if (((data[storageKey] as string) || "auto") !== "auto") return;
              const next = detectTheme();
              if (next === lastAutoTheme) return;
              lastAutoTheme = next;
              applyTheme("auto");
            })
            .catch(() => themeObserver?.disconnect());
        }, 200);
      });
      themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class", "theme", "data-theme"],
      });
      // Also watch body as some sites put themes there
      themeObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ["class", "theme", "data-theme"],
      });
    }

    browser.runtime.onMessage.addListener((request: any) => {
      if (request === "init") init();
      if (request === "destroy") {
        document.documentElement.classList.remove("dpd-active");
        document.documentElement.classList.remove("dpd-popped-out");
        document.body.classList.remove("dpd-active");
        themeObserver?.disconnect();
        themeObserver = null;
        if (themeDebounce) {
          clearTimeout(themeDebounce);
          themeDebounce = null;
        }
        panel?.destroy();
        panel = null;
        poppedOut = false;
        removeListenersFromTextElements();
      }
      // Popout coordination messages (objects; the core sends plain strings above).
      if (request && typeof request === "object") {
        if (request.action === "dpdHidePanel") setPoppedOut(true);
        else if (request.action === "dpdShowPanel") setPoppedOut(false);
        else if (request.action === "dpdReset") {
          // Clear popped-out state without un-hiding; a "destroy" follows to remove the panel.
          poppedOut = false;
          document.documentElement.classList.remove("dpd-popped-out");
        }
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
