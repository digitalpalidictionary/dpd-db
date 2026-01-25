import { defineBackground } from 'wxt/sandbox';
import { browser } from 'wxt/browser';

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

  const AUTO_DOMAINS = ["suttacentral.net", "suttacentral.express", "digitalpalireader.online", "thebuddhaswords.net", "tipitaka.org", "tipitaka.lk", "open.tipitaka.lk"];

  const getDomainState = async (url: string | undefined): Promise<"ON" | "OFF"> => {
    if (!url || url.startsWith("chrome://") || url.startsWith("about:") || url.startsWith("moz-extension://")) return "OFF";
    try {
      const urlObj = new URL(url);
      const domain = urlObj.hostname;
      const key = `state_${domain}`;
      const data = await browser.storage.local.get(key) as LocalStorage;
      
      if (data[key]) return data[key];
      
      // Check if it's an auto-domain
      const isAuto = AUTO_DOMAINS.some(d => domain.includes(d));
      return isAuto ? "ON" : "OFF";
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
    if (request.action === "started" && sender.tab?.id) {
      await updateIcon(sender.tab.id, "ON");
      return;
    }
    
    if (request.action === "fetchData" && request.url) {
      try {
        const response = await fetch(request.url);
        const data = await response.json();
        return { success: true, data };
      } catch (e: any) {
        return { success: false, error: e.message };
      }
    }
  });
});