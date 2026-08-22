let panel = null;

function handleSelectedWord(word) {
  console.log("[DPD] Searching for:", word);
  // Normalize curly quotes to straight apostrophes
  // Remove common punctuation but PRESERVE internal spaces
  let cleanWord = word
    .replace(/[’‘“”]/g, "'")
    .replace(/[.,;:!?()\[\]{}\\\/"]/g, "")
    .trim();

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

  chrome.runtime.sendMessage(
    {
      action: "fetchData",
      url: "https://dpdict.net/search_json?q=" + encodeURIComponent(cleanWord),
    },
    (response) => {
      if (response?.success) {
        const data = response.data;
        if (!data || (!data.summary_html && !data.dpd_html)) {
          panel?.setText("No results for " + cleanWord);
        } else {
          panel?.setText("Result for " + cleanWord);
          panel?.setContent(
            data.summary_html + '<hr class="dpd">' + data.dpd_html,
          );
        }
      } else {
        panel?.setText("Error: " + (response?.error || "Unknown error"));
      }
    },
  );
}

async function init() {
  if (panel) return;
  document.documentElement.classList.add("dpd-active");
  document.body.classList.add("dpd-active");

  if (!document.getElementById("main-content-32050248")) {
    const container = document.createElement("div");
    container.id = "main-content-32050248";
    Array.from(document.body.childNodes).forEach((node) => {
      if (node.tagName !== "SCRIPT" && node.id !== "dict-panel-25445")
        container.appendChild(node);
    });
    document.body.appendChild(container);
  }

  window.addListenersToTextElements();
  panel = new DictionaryPanel();
  window.panel = panel; // Assign to window so inline event handlers work

  // Show info on first run
  chrome.storage.local.get("isFirstRun").then((data) => {
    if (data.isFirstRun !== false) {
      panel._showInfo();
      chrome.storage.local.set({ isFirstRun: false });
    }
  });

  const domain = window.location.hostname;
  const storage = await chrome.storage.local.get(`theme_${domain}`);
  const savedTheme = storage[`theme_${domain}`] || "auto";
  applyTheme(savedTheme);

  // Notify background that we've started to sync icon state
  chrome.runtime.sendMessage({ action: "started" });

  // If auto, try again shortly in case the SPA theme applied late
  if (savedTheme === "auto") {
    setTimeout(() => applyTheme("auto"), 300);
    setTimeout(() => applyTheme("auto"), 1000);
  }

  // Watch for theme changes on the host page
  const observer = new MutationObserver(() => {
    chrome.storage.local.get(`theme_${domain}`).then((data) => {
      if ((data[`theme_${domain}`] || "auto") === "auto") {
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

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request === "init") init();
  if (request === "destroy") {
    document.documentElement.classList.remove("dpd-active");
    document.body.classList.remove("dpd-active");
    panel?.destroy();
    panel = null;
    window.removeListenersFromTextElements();
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
if (AUTO_DOMAINS.some((d) => window.location.hostname.includes(d))) init();
else {
  chrome.storage.local.get(`state_${window.location.hostname}`).then((data) => {
    if (data[`state_${window.location.hostname}`] === "ON") init();
  });
}
