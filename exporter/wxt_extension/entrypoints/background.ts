import { defineBackground } from 'wxt/sandbox';
import { browser } from 'wxt/browser';
import { getApiBaseUrl } from '../utils/api';
import { isAutoDomain, isExcludedDomain } from '../utils/domains';

interface LocalStorage {
  [key: string]: any;
}

export default defineBackground(() => {
  // On Install
  browser.runtime.onInstalled.addListener(async (details) => {
    if (details.reason === "install") {
      await browser.storage.local.set({ isFirstRun: true });
    }
  });

  // Icon Management
  const updateIcon = async (tabId: number, state: "ON" | "OFF") => {
    const iconSet = state === "ON"
      ? { 
          16: "icons/dpd-logo_16.png", 
          32: "icons/dpd-logo_32.png", 
          64: "icons/dpd-logo_64.png", 
          128: "icons/dpd-logo_128.png" 
        }
      : { 
          16: "icons/dpd-logo-gray_16.png", 
          32: "icons/dpd-logo-gray_32.png", 
          64: "icons/dpd-logo-gray_64.png", 
          128: "icons/dpd-logo-gray_128.png" 
        };
    
    // browser.action is standard MV3 (chrome.action). 
    // webextension-polyfill normalizes this to browser.action for Firefox MV2 as well if using WXT/polyfill correctly.
    await browser.action.setIcon({ tabId, path: iconSet });
  };

  const getDomainState = async (url: string | undefined): Promise<"ON" | "OFF"> => {
    if (!url || url.startsWith("chrome://") || url.startsWith("about:") || url.startsWith("moz-extension://")) return "OFF";
    try {
      const urlObj = new URL(url);
      const domain = urlObj.hostname;
      const key = `state_${domain}`;
      const data = await browser.storage.local.get(key) as LocalStorage;
      
      if (data[key]) return data[key];
      
      return (!isExcludedDomain(domain) && isAutoDomain(domain)) ? "ON" : "OFF";
    } catch (e) {
      console.error("Error getting domain state:", e);
      return "OFF";
    }
  };

  // Toggle State on Click
  browser.action.onClicked.addListener(async (tab) => {
    if (!tab.id || !tab.url) return;

    try {
      const domain = new URL(tab.url).hostname;

      // If this site is already popped out, its in-page panel is intentionally hidden,
      // so a plain toggle would look like it did nothing. Bring the popout to the front
      // instead — that's the visible DPD for this site. (Stale flag → fall through.)
      const hostKey = `popout_host_${domain}`;
      const winId = (await browser.storage.local.get(hostKey) as LocalStorage)[hostKey];
      if (winId != null) {
        try {
          await browser.windows.get(winId);
          await browser.windows.update(winId, { focused: true });
          return;
        } catch (e) {
          await browser.storage.local.remove(hostKey);
          await browser.storage.session.remove(`popout_win_${winId}`);
        }
      }

      const currentState = await getDomainState(tab.url);
      const nextState = currentState === "ON" ? "OFF" : "ON";
      
      await browser.storage.local.set({ [`state_${domain}`]: nextState });
      
      try {
        await browser.tabs.sendMessage(tab.id, nextState === "ON" ? "init" : "destroy");
      } catch (e) {
        // Content script might not be ready or injected on some pages
        console.warn("Could not send message to tab:", e);
      }
      
      await updateIcon(tab.id, nextState);
    } catch (e) {
      console.error("Error in onClicked:", e);
    }
  });

  // Update Icon on Tab Update
  browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if ((changeInfo.status === 'complete' || changeInfo.url) && tab.url) {
      const state = await getDomainState(tab.url);
      await updateIcon(tabId, state);
    }
  });

  // Update Icon on Tab Activation
  browser.tabs.onActivated.addListener(async (activeInfo) => {
    try {
      const tab = await browser.tabs.get(activeInfo.tabId);
      if (tab.url) {
        const state = await getDomainState(tab.url);
        await updateIcon(activeInfo.tabId, state);
      }
    } catch (e) {
      console.error("[DPD] Error in onActivated:", e);
    }
  });

  // Message Handling
  browser.runtime.onMessage.addListener(async (request: any, sender: any) => {
    console.log("[DPD] Background received message:", request);
    if (request.action === "getApiBaseUrl") {
      const baseUrl = await getApiBaseUrl();
      console.log("[DPD] Background sending baseUrl:", baseUrl);
      return { baseUrl };
    }

    if (request.action === "started" && sender.tab?.id) {
      const tabId = sender.tab.id;
      await updateIcon(tabId, "ON");
      // Is this SITE already popped out (from any tab)? If so, tell this freshly-loaded
      // content script to keep its in-page panel hidden rather than show a duplicate.
      // Validate the window is still open so a stale flag (window closed while the
      // service worker slept) can't wrongly hide us — and clear it if dead.
      let poppedOut = false;
      try {
        const host = sender.url ? new URL(sender.url).hostname : "";
        if (host) {
          const hostKey = `popout_host_${host}`;
          const winId = (await browser.storage.local.get(hostKey) as LocalStorage)[hostKey];
          if (winId != null) {
            try { await browser.windows.get(winId); poppedOut = true; }
            catch {
              await browser.storage.local.remove(hostKey);
              await browser.storage.session.remove(`popout_win_${winId}`);
            }
          }
        }
      } catch (e) { /* leave poppedOut false */ }
      return { tabId, poppedOut };
    }
    
    if (request.action === "fetchData" && request.endpoint) {
      try {
        const baseUrl = await getApiBaseUrl();
        const url = `${baseUrl}${request.endpoint}`;
        const isProduction = baseUrl === "https://dpdict.net";
        const routeDescription = isProduction ? "via dpdict.net" : `via local server ${baseUrl}`;
        console.log(`[DPD] Searching via ${routeDescription}`);
        const response = await fetch(url);
        const data = await response.json();
        return { success: true, data };
      } catch (e: any) {
        return { success: false, error: e.message };
      }
    }

    // Detach the dictionary into its own popup window and hide the in-page panel.
    if (request.action === "openPopout") {
      const sourceTabId = sender.tab?.id;
      if (sourceTabId == null || !sender.url) return;
      let host: string;
      try { host = new URL(sender.url).hostname; } catch (e) { return; }

      // One popout per SITE. Tab ids are ephemeral (close+reopen a tab and the old id is
      // gone), which let popouts breed; keying on hostname and validating the window is
      // still open means a site has at most one popout, reused across tabs and reloads.
      const hostKey = `popout_host_${host}`;
      const existingWin = (await browser.storage.local.get(hostKey) as LocalStorage)[hostKey];
      if (existingWin != null) {
        try {
          await browser.windows.get(existingWin);                       // throws if closed
          browser.windows.update(existingWin, { focused: true }).catch(() => {});
          return;                                                       // flag already hides all tabs
        } catch (e) {
          await browser.storage.local.remove(hostKey);                  // stale → fall through
          await browser.storage.session.remove(`popout_win_${existingWin}`);
        }
      }

      const url =
        (browser.runtime as any).getURL("popout.html") +
        "?q=" + encodeURIComponent(request.q || "") +
        "&theme=" + encodeURIComponent(request.theme || "auto") +
        "&host=" + encodeURIComponent(host);
      const win = await browser.windows.create({ url, type: "popup", width: 480, height: 820 });
      if (win?.id != null) {
        // popout_host_<host> lives in LOCAL storage so EVERY open tab of this site sees
        // the change (content scripts get storage.local events; session ones they don't)
        // and hides its in-page panel — not just the source tab. window id -> {host, tab}
        // stays background-only in session (cleanup + which panel to restore/dismiss).
        await browser.storage.local.set({ [hostKey]: win.id });
        await browser.storage.session.set({ [`popout_win_${win.id}`]: { host, tab: sourceTabId } });
      }
      return;
    }

    // Pop-in: flag the window so onRemoved restores (not dismisses), then close it.
    // Prefer the sender's own window id so a pop-in that fires before the popout page
    // has learned its window id still restores instead of falling through to dismiss.
    if (request.action === "popIn") {
      const winId = request.win ?? sender.tab?.windowId;
      if (winId == null) return;
      await browser.storage.session.set({ [`popout_pin_${winId}`]: true });
      browser.windows.remove(winId).catch(() => {});
      return;
    }
  });

  const dismissOnTab = async (tabId: number, host?: string) => {
    // Faithfully "turn DPD off" on this page: clear popped-out state, remove the
    // in-page panel, persist the OFF state, and gray the toolbar icon. `host` is passed
    // when known (from the popout record) so we don't depend on reading the tab's url.
    browser.tabs.sendMessage(tabId, { action: "dpdReset" }).catch(() => {});
    browser.tabs.sendMessage(tabId, "destroy").catch(() => {});
    try {
      let h = host;
      if (!h) {
        const tab = await browser.tabs.get(tabId);
        if (tab.url) h = new URL(tab.url).hostname;
      }
      if (h) await browser.storage.local.set({ [`state_${h}`]: "OFF" });
    } catch (e) {
      console.warn("[DPD] dismissOnTab failed to set OFF state:", e);
    }
    await updateIcon(tabId, "OFF");
  };

  // A popout closed via its window X (no pin flag) dismisses DPD on the source page;
  // closing via the pop-in button (which sets the pin flag first) restores the panel.
  browser.windows.onRemoved.addListener(async (winId) => {
    const winKey = `popout_win_${winId}`;
    const pinKey = `popout_pin_${winId}`;
    const rec = await browser.storage.session.get([winKey, pinKey]) as LocalStorage;
    const info = rec[winKey] as { host: string; tab: number } | undefined;
    if (info == null) return;
    const { host, tab: tabId } = info;
    const wasPopIn = !!rec[pinKey];
    await browser.storage.session.remove([winKey, pinKey]);
    if (wasPopIn) {
      // Restore the in-page panel on EVERY tab of this site (they watch popout_host_*).
      await browser.storage.local.remove(`popout_host_${host}`);
      browser.tabs.sendMessage(tabId, { action: "dpdShowPanel" }).catch(() => {});
    } else {
      // Turn DPD off across the whole site: set OFF first (all tabs tear down via the
      // state_* watcher), THEN clear the popout flag so nothing briefly un-hides.
      await dismissOnTab(tabId, host);
      await browser.storage.local.remove(`popout_host_${host}`);
    }
  });
});