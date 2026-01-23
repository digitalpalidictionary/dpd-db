const updateIcon = (tabId, state) => {
  const iconSet = state === "ON"
    ? {
      16: "images/dpd-logo_16.png",
      32: "images/dpd-logo_32.png",
      64: "images/dpd-logo_64.png",
      128: "images/dpd-logo_128.png"
    }
    : {
      16: "images/dpd-logo-gray_16.png",
      32: "images/dpd-logo-gray_32.png",
      64: "images/dpd-logo-gray_64.png",
      128: "images/dpd-logo-gray_128.png"
    };

  chrome.action.setIcon({
    tabId: tabId,
    path: iconSet
  });
};

chrome.runtime.onInstalled.addListener(() => {
  console.log("DPD Extension installed");
  // Clear all states on install/update
  chrome.storage.local.get(null, (items) => {
    const keysToRemove = Object.keys(items).filter(key => key.startsWith('state_'));
    chrome.storage.local.remove(keysToRemove);
  });
});

// Also clear states when the background script loads (e.g. browser restart or extension reload)
chrome.storage.local.get(null, (items) => {
  const keysToRemove = Object.keys(items).filter(key => key.startsWith('state_'));
  chrome.storage.local.remove(keysToRemove);
});

const tipitakaOrg = "https://tipitaka.org";
const ALLOWED_ORIGINS = [
  "https://dpdict.net",
  "http://0.0.0.0:8080"
];
const initializedTabs = new Set();

chrome.action.onClicked.addListener(async (tab) => {
  const initialize = async (id) => {
    if (!initializedTabs.has(id)) {
      await chrome.scripting.executeScript({
        target: { tabId: id },
        files: ["utils.js", "themes.js", "dictionary-panel.js"],
      });
      initializedTabs.add(id);
    }
  };

  // Retrieve the state for the current tab (defaults to OFF)
  const key = `state_${tab.id}`;
  const data = await chrome.storage.local.get(key);
  const prevState = data[key] || "OFF";
  const nextState = prevState === "ON" ? "OFF" : "ON";

  // Update storage
  await chrome.storage.local.set({ [key]: nextState });

  // Update the icon
  updateIcon(tab.id, nextState);

  if (nextState === "ON") {
    await chrome.scripting.insertCSS({
      files: [
        "css/chrome-extension.css",
        "css/dpd-variables.css",
        "css/dpd.css"
      ],
      target: { tabId: tab.id },
    });

    await initialize(tab.id);

    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["main.js"],
    });
  } else if (nextState === "OFF") {
    chrome.tabs.sendMessage(tab.id, "destroy");

    await chrome.scripting.removeCSS({
      files: [
        "css/chrome-extension.css",
        "css/dpd-variables.css",
        "css/dpd.css"
      ],
      target: { tabId: tab.id },
    });
  }
});

// Cleanup storage when tab is closed
chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.remove(`state_${tabId}`);
  initializedTabs.delete(tabId);
});

// Handle messages from content scripts (e.g., for fetching data to avoid CORS)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchData") {
    try {
      const url = new URL(request.url);
      if (!ALLOWED_ORIGINS.includes(url.origin)) {
        console.error("Blocked request to unauthorized origin:", url.origin);
        sendResponse({ success: false, error: "Unauthorized origin" });
        return true;
      }
    } catch (e) {
      sendResponse({ success: false, error: "Invalid URL" });
      return true;
    }

    fetch(request.url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => sendResponse({ success: true, data: data }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    // Return true to indicate we want to send a response asynchronously
    return true;
  }
});
