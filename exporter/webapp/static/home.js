const c = console.log;

//// elements

const docBody = document.body;
const titleClear = document.getElementById("title-clear");
const logoLink = document.getElementById("logo-link");
const mainPane = document.getElementById("main-pane");
const dpdPane = document.getElementById("dpd-pane");
const summaryResults = document.getElementById("summary-results");
const dpdResults = document.getElementById("dpd-results");
const historyPane = document.getElementById("history-pane");
const historyListPane = document.getElementById("history-list-pane");
const historyCollapseToggle = document.getElementById(
  "history-collapse-toggle",
);
const settingsCollapseToggle = document.getElementById(
  "settings-collapse-toggle",
);
const subTitle = document.getElementById("subtitle");
const searchBox = document.getElementById("search-box");
const entryBoxClass = document.getElementsByClassName("search-box");
const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const clearButton = document.getElementById("clear-button");
const footerText = document.getElementById("footer");

const themeToggle = document.getElementById("theme-toggle");
const sansSerifToggle = document.getElementById("sans-serif-toggle");
const niggahitaToggle = document.getElementById("niggahita-toggle");
const grammarToggle = document.getElementById("grammar-toggle");
const exampleToggle = document.getElementById("example-toggle");
const oneButtonToggle = document.getElementById("one-button-toggle");
const summaryToggle = document.getElementById("summary-toggle");
const sandhiToggle = document.getElementById("sandhi-toggle");
const audioToggle = document.getElementById("audio-toggle");
var fontSize;
const fontSizeUp = document.getElementById("font-size-up");
const fontSizeDown = document.getElementById("font-size-down");
var fontSizeDisplay = document.getElementById("font-size-display");

let dpdResultsContent = "";
let language;

const startMessage = `
        <p class="message">Search for Pāḷi or English words above using <b>Unicode</b> or <b>Velthuis</b> characters.</p>
        <p class="message"><b>Double click</b> on any word to search for it.</p>
        <p class="message">Adjust the <b>settings</b> to suit your preferences.</p>
        <p class="message"><b>Refresh</b> the page if you experience any problems.</p>
        <p class="message">
            <a href="https://docs.dpdict.net/webapp/" target="_blank">Click here</a>
            for more details about this website or
            <a href="https://docs.dpdict.net/" target="_blank">more information</a>
            about DPD in general.
        </p>
        <p class="message">Start by <b>double clicking</b> on any word in the list below:</p>
        <p class="message">atthi kāmarāgapariyuṭṭhitena peace kar gacchatīti Root ✓</p>
        `;

//// load state

function loadToggleState(id) {
  var savedState = localStorage.getItem(id);
  if (savedState !== null) {
    document.getElementById(id).checked = JSON.parse(savedState);
  }
}

//// Page load
document.addEventListener("DOMContentLoaded", function () {
  const htmlElement = document.documentElement;
  language = htmlElement.lang || "en";

  if (dpdResults.innerHTML.trim() === "") {
    dpdResults.innerHTML = startMessage;
  }

  // Set the toggle switch to the correct state and apply the theme
  try {
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      themeToggle.checked = true;
      document.documentElement.classList.add("dark-mode");
    } else {
      themeToggle.checked = false;
      document.documentElement.classList.remove("dark-mode");
    }
  } catch (e) {
    console.log("LocalStorage is not available.");
  }

  loadToggleState("sans-serif-toggle");
  loadToggleState("niggahita-toggle");
  loadToggleState("grammar-toggle");
  loadToggleState("example-toggle");
  loadToggleState("one-button-toggle");
  loadToggleState("summary-toggle");
  loadToggleState("sandhi-toggle");
  loadToggleState("audio-toggle");
  loadFontSize();
  swopSansSerif();
  showHideSandhi();

  // Language switcher dropdown control
  const languageIcon = document.querySelector(".language-icon");
  const dropdown = document.querySelector(".dropdown");

  // Ensure both elements exist before adding event listeners
  if (languageIcon && dropdown) {
    // Show or hide dropdown on icon click
    languageIcon.addEventListener("click", function () {
      dropdown.style.display =
        dropdown.style.display === "block" ? "none" : "block";
    });

    // Hide dropdown if clicked outside
    document.addEventListener("click", function (e) {
      if (!languageIcon.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });
  } else {
    console.error(
      "Error: .language-icon or .dropdown element not found in the DOM.",
    );
  }
});

//// listeners

//// trigger title clear - go home

titleClear.addEventListener("dblclick", function () {
  dpdPane.innerHTML = "";
});

logoLink.addEventListener("click", function (e) {
  e.preventDefault();
  clearSearch();
});

// Original double-click functionality
dpdPane.addEventListener("dblclick", processSelection);
historyPane.addEventListener("dblclick", processSelection);

function processSelection(event) {
  const selection = window.getSelection();

  // First, expand the selection to include the full word across HTML elements
  expandSelectionToWord();

  // Get the expanded selection text
  let selectedText = selection.toString().trim();

  // If still no text, return
  if (!selectedText || selectedText === "") {
    return;
  }

  // Update appState before calling performSearch to prevent flashing
  if (typeof appState !== "undefined" && appState.activeTab === "dpd") {
    appState.dpd.searchTerm = selectedText;
  }
  searchBox.value = selectedText;
  window.performSearch();
}

// Check if a character is a word character (Pāḷi or English alphabet)
function isWordChar(char) {
  // Pāḷi alphabet: a-z, A-Z, ā, ī, ū, ṅ, ñ, ṭ, ḍ, ṇ, ṁ, ṃ, ḷ
  // Using Unicode ranges and specific characters
  const wordCharRegex =
    /[a-zA-Z\u0101\u012b\u016b\u1e45\u00f1\u1e6d\u1e0d\u1e47\u1e41\u1e43\u1e37]/;
  return wordCharRegex.test(char);
}

// Expand selection to include the full word across HTML elements
// Adapted from exporter/wxt_extension/utils/utils.ts
function expandSelectionToWord() {
  const selection = window.getSelection();
  if (!selection || !selection.rangeCount) return;
  const range = selection.getRangeAt(0);

  // If the selection already spans across multiple nodes, trust it.
  if (range.startContainer !== range.endContainer) return;

  const initialNode = range.startContainer;
  if (initialNode.nodeType !== Node.TEXT_NODE) return;

  // Characters to stop on.
  // Note: Closing quotes (' ") are removed from stopChars so expansion includes suffixes like "ti.
  const stopChars =
    /[ \t\n\r\.\,\;\:\!\?\(\)\[\]\{\}\\\/\*\&\%\$\#\@\+\=\<\>\♦0-9'"]/;
  const isStop = (char) => !char || stopChars.test(char);

  let startNode = initialNode;
  let startOffset = range.startOffset;
  let endNode = initialNode;
  let endOffset = range.endOffset;

  // Helper to find the next/previous text node in the document order
  const getNextTextNode = (node, forward) => {
    let current = node;
    while (current) {
      // Move to sibling or parent's sibling
      let next = forward ? current.nextSibling : current.previousSibling;
      if (!next) {
        current = current.parentElement;
        // Don't cross out of a block element
        if (current && window.getComputedStyle(current).display !== "inline")
          return null;
        continue;
      }
      current = next;

      // If we hit a block element or <br> tag, stop
      if (current.nodeType === Node.ELEMENT_NODE) {
        const element = current;
        if (
          window.getComputedStyle(element).display !== "inline" ||
          element.tagName.toLowerCase() === "br"
        ) {
          return null;
        }
      }

      // If it's a text node, return it
      if (current.nodeType === Node.TEXT_NODE) return current;

      // If it's an inline element, go inside it
      if (current.nodeType === Node.ELEMENT_NODE) {
        const walker = document.createTreeWalker(
          current,
          NodeFilter.SHOW_TEXT,
          null,
        );
        const textNode = forward ? walker.firstChild() : walker.lastChild();
        if (textNode) return textNode;
      }
    }
    return null;
  };

  // Expand backwards
  while (startNode && startNode.nodeValue) {
    const text = startNode.nodeValue;
    while (startOffset > 0 && !isStop(text[startOffset - 1])) {
      startOffset--;
    }

    if (startOffset === 0) {
      const prev = getNextTextNode(startNode, false);
      if (
        prev &&
        prev.nodeValue &&
        prev.nodeValue.length > 0 &&
        !isStop(prev.nodeValue[prev.nodeValue.length - 1])
      ) {
        startNode = prev;
        startOffset = prev.nodeValue.length;
        continue;
      }
    }
    break;
  }

  // Expand forwards
  while (endNode && endNode.nodeValue) {
    const text = endNode.nodeValue;
    while (endOffset < text.length && !isStop(text[endOffset])) {
      endOffset++;
    }

    if (endOffset === text.length) {
      const next = getNextTextNode(endNode, true);
      if (
        next &&
        next.nodeValue &&
        next.nodeValue.length > 0 &&
        !isStop(next.nodeValue[0])
      ) {
        endNode = next;
        endOffset = 0;
        continue;
      }
    }
    break;
  }

  // Update selection
  try {
    if (startNode && endNode) {
      selection.setBaseAndExtent(startNode, startOffset, endNode, endOffset);
    }
  } catch (e) {
    console.error("[DPD] Expansion error:", e);
  }
}

//// font size ////

function loadFontSize() {
  fontSize = localStorage.getItem("fontSize");
  if (fontSize === null) {
    bodyStyle = window.getComputedStyle(document.body);
    fontSize = parseInt(bodyStyle.getPropertyValue("font-size"), 10);
  } else {
    setFontSize();
  }
}

function saveFontSize() {
  localStorage.setItem("fontSize", fontSize);
}

function setFontSize() {
  document.body.style.fontSize = fontSize + "px";
  fontSizeDisplay.innerHTML = `${fontSize}px`;
}

fontSizeUp.addEventListener("click", increaseFontSize);
fontSizeDown.addEventListener("click", decreaseFontSize);

function increaseFontSize() {
  fontSize = parseInt(fontSize, 10) + 1;
  setFontSize();
  saveFontSize();
}

function decreaseFontSize() {
  fontSize = parseInt(fontSize, 10) - 1;
  setFontSize();
  saveFontSize();
}

function changeLanguage(lang) {
  const currentUrl = new URL(window.location.href);
  const hostname = currentUrl.hostname;
  const pathname = currentUrl.pathname;
  const search = currentUrl.search;
  const protocol = currentUrl.protocol; // e.g., 'https:'
  const port = currentUrl.port; // Get the port (e.g., '8080')

  let newHostname = hostname;

  if (lang === "ru") {
    // For Russian: remove www. and ru. if present, then add ru.
    if (hostname.startsWith("www.")) {
      newHostname = `ru.${hostname.substring(4)}`;
    } else if (hostname.startsWith("ru.")) {
      newHostname = hostname;
    } else {
      newHostname = `ru.${hostname}`;
    }
  } else if (lang === "en") {
    // For English: remove ru. if present, and ensure www. is added
    if (hostname.startsWith("ru.www.")) {
      newHostname = `www.${hostname.substring(7)}`;
    } else if (hostname.startsWith("ru.")) {
      newHostname = `www.${hostname.substring(3)}`;
    } else if (!hostname.startsWith("www.")) {
      newHostname = `www.${hostname}`;
    } else {
      newHostname = hostname;
    }
  }

  // Only redirect if the hostname actually changed
  if (newHostname !== hostname) {
    // Construct new URL, including the port if it exists
    const portString = port ? `:${port}` : ""; // Add colon only if port exists
    const newUrl = `${protocol}//${newHostname}${portString}${pathname}${search}`;
    // Redirect
    window.location.href = newUrl;
  }
}

//// enter or click button to search

// Let app.js handle the search
// searchForm.addEventListener("submit", handleFormSubmit);
// searchButton.addEventListener("submit", handleFormSubmit);

//// submit search

// Let app.js handle the search
// async function handleFormSubmit(event) {
//     if (event) {
//         event.preventDefault();
//     }
//     // Let app.js handle the search
//     window.performSearch();
// }

//// save settings on toggle

function saveToggleState(event) {
  try {
    localStorage.setItem(event.target.id, JSON.stringify(event.target.checked));
  } catch (e) {
    console.log("LocalStorage is not available.");
  }
}

sansSerifToggle.addEventListener("change", saveToggleState);
niggahitaToggle.addEventListener("change", saveToggleState);
grammarToggle.addEventListener("change", saveToggleState);
exampleToggle.addEventListener("change", saveToggleState);
oneButtonToggle.addEventListener("change", saveToggleState);
summaryToggle.addEventListener("change", saveToggleState);
sandhiToggle.addEventListener("change", saveToggleState);
audioToggle.addEventListener("change", saveToggleState);

//// theme

themeToggle.addEventListener("change", function (event) {
  document.documentElement.classList.toggle("dark-mode", event.target.checked);
  try {
    localStorage.setItem("theme", event.target.checked ? "dark" : "light");
  } catch (e) {
    console.log("LocalStorage is not available.");
  }
});

//// toggle sans / serif

sansSerifToggle.addEventListener("change", function () {
  swopSansSerif();
});

function swopSansSerif() {
  const serifFonts = "'Source Serif 4', serif"; // Use Source Serif 4 here
  const sansFonts = "'Inter', sans-serif"; // Use Inter font here
  if (sansSerifToggle.checked) {
    document.body.style.fontFamily = serifFonts;
    searchBox.style.fontFamily = serifFonts;
    searchButton.style.fontFamily = serifFonts;
  } else {
    document.body.style.fontFamily = sansFonts;
    searchBox.style.fontFamily = sansFonts;
    searchButton.style.fontFamily = sansFonts;
  }
}

//// niggahita

function niggahitaUp(element) {
  element.innerHTML = element.innerHTML.replace(/ṃ/g, "ṁ");
}

function niggahitaDown(element) {
  element.innerHTML = element.innerHTML.replace(/ṁ/g, "ṃ");
}

niggahitaToggle.addEventListener("change", function () {
  if (this.checked) {
    niggahitaUp(dpdPane);
    niggahitaUp(historyPane);
  } else {
    niggahitaDown(dpdPane);
    niggahitaDown(historyPane);
  }
});

//// grammar button closed / open

grammarToggle.addEventListener("change", function () {
  const grammarButtons = document.getElementsByName("grammar-button");
  const grammarDivs = document.getElementsByName("grammar-div");
  if (this.checked) {
    grammarButtons.forEach((button) => {
      button.classList.add("active");
    });
    grammarDivs.forEach((div) => {
      div.classList.remove("hidden");
    });
  } else {
    grammarButtons.forEach((button) => {
      button.classList.remove("active");
    });
    grammarDivs.forEach((div) => {
      div.classList.add("hidden");
    });
  }
});

//// examples button toggle

exampleToggle.addEventListener("change", function () {
  const exampleButtons = document.getElementsByName("example-button");
  const exampleDivs = document.getElementsByName("example-div");
  if (this.checked) {
    exampleButtons.forEach((button) => {
      button.classList.add("active");
    });
    exampleDivs.forEach((div) => {
      div.classList.remove("hidden");
    });
  } else {
    exampleButtons.forEach((button) => {
      button.classList.remove("active");
    });
    exampleDivs.forEach((div) => {
      div.classList.add("hidden");
    });
  }
});

//// summary

summaryToggle.addEventListener("change", function () {
  showHideSummary();
});

function showHideSummary() {
  if (summaryToggle.checked) {
    summaryResults.style.display = "block";
  } else {
    summaryResults.style.display = "none";
  }
}

//// sandhi ' toggle

sandhiToggle.addEventListener("change", function () {
  showHideSandhi();
});

function showHideSandhi() {
  const dpdResults = document.getElementById("dpd-results");
  if (!dpdResults) return;

  // Simply add/remove a CSS class to hide/show apostrophes
  if (sandhiToggle.checked) {
    // Sandhi toggle ON - show apostrophes
    dpdResults.classList.remove("hide-apostrophes");
  } else {
    // Sandhi toggle OFF - hide apostrophes
    dpdResults.classList.add("hide-apostrophes");
  }
}

// Expose showHideSandhi to the global scope
window.showHideSandhi = showHideSandhi;

//// text to unicode

function uniCoder(textInput) {
  if (!textInput || textInput == "") return textInput;
  return textInput
    .replace(/aa/g, "ā")
    .replace(/ii/g, "ī")
    .replace(/uu/g, "ū")
    .replace(/\"n/g, "ṅ")
    .replace(/\~n/g, "ñ")
    .replace(/\.t/g, "ṭ")
    .replace(/\.d/g, "ḍ")
    .replace(/\.n/g, "ṇ")
    .replace(/\.m/g, "ṃ")
    .replace(/\.l/g, "ḷ")
    .replace(/\.h/g, "ḥ");
}

// Expose uniCoder to the global scope
window.uniCoder = uniCoder;

searchBox.addEventListener("input", function () {
  let textInput = searchBox.value;
  let convertedText = uniCoder(textInput);
  searchBox.value = convertedText;
});

//// clear search function

function clearSearch() {
  searchBox.value = "";
  dpdResults.innerHTML = "";
  summaryResults.innerHTML = "";
  if (typeof appState !== "undefined") {
    appState.dpd.searchTerm = "";
  }
  window.history.pushState({}, "", window.location.pathname);
  searchBox.focus();
}

clearButton.addEventListener("click", clearSearch);

//// collapse/expand functionality for mobile

function initCollapseToggle(toggleButton, paneElement) {
  if (!toggleButton || !paneElement) return;

  const isMobile = window.innerWidth <= 576;

  const handleToggle = function () {
    paneElement.classList.toggle("collapsed");
    const isCollapsed = paneElement.classList.contains("collapsed");
    try {
      localStorage.setItem(paneElement.id + "_collapsed", isCollapsed);
    } catch (e) {
      console.log("LocalStorage is not available.");
    }
  };

  toggleButton.addEventListener("click", handleToggle);

  const paneHeader = paneElement.querySelector(".pane-header");
  if (paneHeader) {
    paneHeader.addEventListener("click", function (e) {
      if (e.target !== toggleButton && !toggleButton.contains(e.target)) {
        handleToggle();
      }
    });
  }

  if (!isMobile) {
    return;
  }

  const savedState = localStorage.getItem(paneElement.id + "_collapsed");
  if (savedState === "true") {
    paneElement.classList.add("collapsed");
  } else if (savedState === null) {
    paneElement.classList.add("collapsed");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  initCollapseToggle(historyCollapseToggle, historyPane);

  const settingsPane = document.querySelector(".settings-pane");
  if (settingsPane) {
    initCollapseToggle(settingsCollapseToggle, settingsPane);
  }
});
