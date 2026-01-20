/**
 * Handle a selected word by looking it up in the dictionary.
 *
 * @param {string} word - The selected word.
 */
function handleSelectedWord(word) {
  console.log("Selected word:", word);
  panel?.setSearchValue(word);
  panel?.setText("Loading...");

  const url =
    // "https://www.dpdict.net/search_json?q=" + encodeURIComponent(word);
    "http://0.0.0.0:8080/search_json?q=" + encodeURIComponent(word);

  // Use background script to fetch data to avoid CORS issues
  chrome.runtime.sendMessage(
    { action: "fetchData", url: url },
    (response) => {
      // Handle the response from the background script
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError);
        panel?.setText("Error: " + chrome.runtime.lastError.message);
        panel?.setContent("<p style='padding:10px;'>Communication error. Please reload the page and try again.</p>");
        return;
      }

      if (response && response.success) {
        const data = response.data;
        if (!data || (!data.summary_html && !data.dpd_html)) {
          panel?.setText("No results for " + word);
          panel?.setContent("<p style='padding:10px;'>Try another word or check the spelling.</p>");
          return;
        }
        panel?.setText("Result for " + word);
        panel?.setContent(data.summary_html + "<hr class=\"dpd\">" + data.dpd_html);
      } else {
        console.error(response?.error);
        if (response?.error?.includes("429")) {
          panel?.setText("Error: Too many requests");
        } else {
          panel?.setText("Error: " + (response?.error || "Unknown error"));
        }
        panel?.setContent("<p style='padding:10px;'>Could not fetch data. Please check your connection.</p>");
      }
    }
  );
}

async function init() {
  document.documentElement.classList.add("dpd-active");
  document.body.classList.add("dpd-active");

  if (document.getElementById("main-content-32050248") === null) {
    const newContentContainer = document.createElement("div");
    const nodes = document.body.childNodes;
    newContentContainer.id = "main-content-32050248";
    [...nodes]
      .filter((node) => node.tagName !== "SCRIPT")
      .forEach((node) => {
        newContentContainer.appendChild(node);
      });

    document.body.appendChild(newContentContainer);
    addListenersToTextElements();
    chrome.runtime.onMessage.addListener(function (
      request,
      sender,
      sendResponse
    ) {
      if (request === "destroy") {
        document.documentElement.classList.remove("dpd-active");
        document.body.classList.remove("dpd-active");
        panel?.destroy();
        delete panel;
        panel = null;
        sendResponse("done");
      }
    });
  }

  panel = panel || new DictionaryPanel();
  
  const domain = window.location.hostname;
  const storage = await chrome.storage.local.get(`theme_${domain}`);
  const savedTheme = storage[`theme_${domain}`] || "auto";
  applyTheme(savedTheme);
}

// Run the script after the DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
