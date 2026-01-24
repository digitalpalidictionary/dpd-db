const updateIcon = (tabId, state) => {
  const iconSet = state === "ON"
    ? { 16: "images/dpd-logo_16.png", 32: "images/dpd-logo_32.png", 64: "images/dpd-logo_64.png", 128: "images/dpd-logo_128.png" }
    : { 16: "images/dpd-logo-gray_16.png", 32: "images/dpd-logo-gray_32.png", 64: "images/dpd-logo-gray_64.png", 128: "images/dpd-logo-gray_128.png" };
  chrome.action.setIcon({ tabId, path: iconSet });
};

const AUTO_DOMAINS = ["suttacentral.net", "suttacentral.express", "digitalpalireader.online", "thebuddhaswords.net", "tipitaka.org", "tipitaka.lk", "open.tipitaka.lk"];

const getDomainState = async (url) => {
  if (!url || url.startsWith("chrome://") || url.startsWith("about:")) return "OFF";
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname;
    const data = await chrome.storage.local.get(`state_${domain}`);
    if (data[`state_${domain}`]) return data[`state_${domain}`];
    
    // Check if it's an auto-domain (matching main.js logic)
    const isAuto = AUTO_DOMAINS.some(d => domain.includes(d));
    return isAuto ? "ON" : "OFF";
  } catch (e) {
    return "OFF";
  }
};

chrome.action.onClicked.addListener(async (tab) => {
  const domain = new URL(tab.url).hostname;
  const currentState = await getDomainState(tab.url);
  const nextState = currentState === "ON" ? "OFF" : "ON";
  await chrome.storage.local.set({ [`state_${domain}`]: nextState });
  chrome.tabs.sendMessage(tab.id, nextState === "ON" ? "init" : "destroy");
  updateIcon(tab.id, nextState);
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if ((changeInfo.status === 'complete' || changeInfo.url) && tab.url) {
    updateIcon(tabId, await getDomainState(tab.url));
  }
});

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      updateIcon(activeInfo.tabId, await getDomainState(tab.url));
    }
  } catch (e) {
    console.error("[DPD] Error in onActivated:", e);
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "started" && sender.tab) {
    updateIcon(sender.tab.id, "ON");
  }
  if (request.action === "fetchData") {
    fetch(request.url).then(r => r.json()).then(d => sendResponse({ success: true, data: d })).catch(e => sendResponse({ success: false, error: e.message }));
    return true;
  }
});
