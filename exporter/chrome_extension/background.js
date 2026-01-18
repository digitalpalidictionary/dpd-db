chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({
    text: "OFF",
  });
});

const tipitakaOrg = "https://tipitaka.org";

chrome.action.onClicked.addListener(async (tab) => {
  let initialized = false;

  const initialize = async (id) => {
    if (!initialized) {
      // utils.js must be loaded before others as it contains helper functions
      await chrome.scripting.executeScript({
        target: { tabId: id },
        files: ["utils.js", "themes.js", "dictionary-panel.js", "sorter.js"],
      });
      initialized = true;
    }
  };

  // if (tab.url.startsWith(tipitakaOrg)) {
  // Retrieve the action badge to check if the extension is 'ON' or 'OFF'
  const prevState = await chrome.action.getBadgeText({ tabId: tab.id });
  // Next state will always be the opposite
  const nextState = prevState === "ON" ? "OFF" : "ON";

  // Set the action badge to the next state
  await chrome.action.setBadgeText({
    tabId: tab.id,
    text: nextState,
  });

  if (nextState === "ON") {
    // Insert the CSS files when the user turns the extension on
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

    // Remove the CSS files when the user turns the extension off
    await chrome.scripting.removeCSS({
      files: [
        "css/chrome-extension.css",
        "css/dpd-variables.css",
        "css/dpd.css"
      ],
      target: { tabId: tab.id },
    });

    // console.debug("custom-style.css");
  }
  // }
});

// Handle messages from content scripts (e.g., for fetching data to avoid CORS)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchData") {
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
