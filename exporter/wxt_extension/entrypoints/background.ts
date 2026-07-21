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
      await updateIcon(sender.tab.id, "ON");
      // Hand the content script its own tab id so it can stamp forwarded popout
      // selections, letting each popout ignore selections from other tabs.
      return { tabId: sender.tab.id };
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
      if (sourceTabId == null) return;
      const url =
        (browser.runtime as any).getURL("popout.html") +
        "?q=" + encodeURIComponent(request.q || "") +
        "&theme=" + encodeURIComponent(request.theme || "auto") +
        "&tab=" + sourceTabId;
      const win = await browser.windows.create({ url, type: "popup", width: 480, height: 820 });
      if (win?.id != null) {
        // Remember which tab this popout belongs to, so closing it acts on that panel.
        await browser.storage.session.set({ [`popout_win_${win.id}`]: sourceTabId });
        browser.tabs.sendMessage(sourceTabId, { action: "dpdHidePanel" }).catch(() => {});
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

  const dismissOnTab = async (tabId: number) => {
    // Faithfully "turn DPD off" on this page: clear popped-out state, remove the
    // in-page panel, persist the OFF state, and gray the toolbar icon.
    browser.tabs.sendMessage(tabId, { action: "dpdReset" }).catch(() => {});
    browser.tabs.sendMessage(tabId, "destroy").catch(() => {});
    try {
      const tab = await browser.tabs.get(tabId);
      if (tab.url) {
        const host = new URL(tab.url).hostname;
        await browser.storage.local.set({ [`state_${host}`]: "OFF" });
      }
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
    const tabId = rec[winKey];
    if (tabId == null) return;
    const wasPopIn = !!rec[pinKey];
    await browser.storage.session.remove([winKey, pinKey]);
    if (wasPopIn) {
      browser.tabs.sendMessage(tabId, { action: "dpdShowPanel" }).catch(() => {});
    } else {
      await dismissOnTab(tabId);
    }
  });
});