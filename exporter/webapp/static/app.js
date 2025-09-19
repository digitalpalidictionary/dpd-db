const appState = {
  activeTab: "dpd", // 'dpd' or 'bd'
  dpd: {
    searchTerm: "",
    resultsHTML: "",
  },
  bd: {
    searchTerm1: "",
    searchTerm2: "",
    searchOption: "regex",
    resultsHTML: "",
  },
  history: [], // An array of state snapshots
  historyIndex: -1, // Current position in the history stack
  // History panel entries - simpler list of search terms for persistence
  historyPanelEntries: [], // Array of search terms for the history panel
};

// Initialize the application
function initializeApp() {
  console.log("Initializing app...");
  
  // Initialize history panel entries array
  appState.historyPanelEntries = [];
  
  // Load history from LOCAL storage if available
  try {
    // Load full history
    const savedFullHistory = localStorage.getItem("dpdFullHistory");
    console.log("Raw saved full history from LOCAL storage:", savedFullHistory);
    if (savedFullHistory) {
      appState.history = JSON.parse(savedFullHistory);
      // Update history index to point to the last item
      appState.historyIndex = appState.history.length - 1;
      console.log("Loaded full history from LOCAL storage:", appState.history);
    } else {
      console.log("No full history found in LOCAL storage");
    }
    
    // Load history panel entries
    const savedHistoryPanelEntries = localStorage.getItem("dpdHistoryPanel");
    console.log("Raw saved history panel entries from LOCAL storage:", savedHistoryPanelEntries);
    if (savedHistoryPanelEntries) {
      appState.historyPanelEntries = JSON.parse(savedHistoryPanelEntries);
      console.log("Loaded history panel entries from LOCAL storage:", appState.historyPanelEntries);
    } else {
      console.log("No history panel entries found in LOCAL storage");
    }
  } catch (e) {
    console.log("Failed to load history from LOCAL storage:", e);
  }

  // Parse the URL to determine the initial state
  const urlParams = new URLSearchParams(window.location.search);
  const tab = urlParams.get("tab") || "dpd";
  const q = urlParams.get("q") || "";
  const q1 = urlParams.get("q1") || "";
  const q2 = urlParams.get("q2") || "";
  const option = urlParams.get("option") || "regex";

  // Populate appState from the URL
  appState.activeTab = tab;
  appState.dpd.searchTerm = q;
  appState.bd.searchTerm1 = q1;
  appState.bd.searchTerm2 = q2;
  appState.bd.searchOption = option;

  // If the URL contains search parameters, perform an initial search
  if (
    (q && q.trim() !== "") ||
    (q1 && q1.trim() !== "") ||
    (q2 && q2.trim() !== "")
  ) {
    performSearch(false); // Don't add to history on initial load
  }

  // Add the initial state to the history stack only if there's an actual search
  if (
    (q && q.trim() !== "") ||
    (q1 && q1.trim() !== "") ||
    (q2 && q2.trim() !== "")
  ) {
    addToHistory();
  }

  // Render the initial UI
  render();
  
  // Set up event listener for clear history button
  const clearHistoryButton = document.getElementById("clear-history-button");
  if (clearHistoryButton) {
    clearHistoryButton.addEventListener("click", clearHistory);
  }
  
  // Log the initial state for debugging
  console.log("Initial appState:", appState);
  console.log("Initial history:", appState.history);
  console.log("Initial history panel entries:", appState.historyPanelEntries);
}

// Perform a search operation
async function performSearch(addHistory = true) {
  try {
    if (appState.activeTab === "dpd") {
      // DPD search
      if (appState.dpd.searchTerm.trim() !== "") {
        const response = await fetch(
          `/search_json?q=${encodeURIComponent(appState.dpd.searchTerm)}`
        );
        const data = await response.json();

        // Handle summary HTML
        const summaryResults = document.getElementById("summary-results");
        if (summaryResults) {
          if (data.summary_html && data.summary_html.trim() !== "") {
            // Get language from HTML element
            const htmlElement = document.documentElement;
            const language = htmlElement.lang || "en";

            if (language === "en") {
              summaryResults.innerHTML = "<h3>Summary</h3>";
            } else {
              summaryResults.innerHTML = "<h3>Сводка</h3>";
            }
            summaryResults.innerHTML += data.summary_html;
            summaryResults.innerHTML += "<hr>";
          } else {
            summaryResults.innerHTML = "";
          }

          // Apply summary toggle
          const summaryToggle = document.getElementById("summary-toggle");
          if (summaryToggle) {
            if (summaryToggle.checked) {
              summaryResults.style.display = "block";
            } else {
              summaryResults.style.display = "none";
            }
          }
        }

        // Create a temporary div to manipulate the HTML before storing it
        const dpdDiv = document.createElement("div");
        dpdDiv.innerHTML = data.dpd_html;

        // Apply grammar toggle settings to newly loaded content
        const grammarToggle = document.getElementById("grammar-toggle");
        if (grammarToggle && grammarToggle.checked) {
          const grammarButtons = dpdDiv.querySelectorAll(
            '[name="grammar-button"]'
          );
          const grammarDivs = dpdDiv.querySelectorAll('[name="grammar-div"]');
          grammarButtons.forEach((button) => {
            button.classList.add("active");
          });
          grammarDivs.forEach((div) => {
            div.classList.remove("hidden");
          });
        }

        // Apply example toggle settings to newly loaded content
        const exampleToggle = document.getElementById("example-toggle");
        if (exampleToggle && exampleToggle.checked) {
          const exampleButtons = dpdDiv.querySelectorAll(
            '[name="example-button"]'
          );
          const exampleDivs = dpdDiv.querySelectorAll('[name="example-div"]');
          exampleButtons.forEach((button) => {
            button.classList.add("active");
          });
          exampleDivs.forEach((div) => {
            div.classList.remove("hidden");
          });
        }

        // Store the processed HTML and original content for sandhi toggle
        const processedHTML = dpdDiv.innerHTML;
        window.dpdResultsContent = processedHTML; // Make it available globally for sandhi toggle

        // Apply sandhi toggle to the processed HTML
        const sandhiToggle = document.getElementById("sandhi-toggle");
        if (sandhiToggle && !sandhiToggle.checked) {
          // If sandhi toggle is OFF, wrap apostrophes in spans for hiding
          appState.dpd.resultsHTML = wrapApostrophesInHTML(processedHTML);
        } else {
          // If sandhi toggle is ON or not found, keep the processed HTML as is
          appState.dpd.resultsHTML = processedHTML;
        }

        // If addHistory is true, add the new state to the history stack
        if (addHistory) {
          addToHistory();
        }

        // Update the UI with the new search results
        render();
      }
    } else if (appState.activeTab === "bd") {
      // BD search
      // Always perform BD search if we're on the BD tab, regardless of whether search terms are empty
      // This ensures history is properly managed even when search terms are cleared

      const response = await fetch(
        `/bd_search?q1=${encodeURIComponent(
          appState.bd.searchTerm1
        )}&q2=${encodeURIComponent(appState.bd.searchTerm2)}&option=${
          appState.bd.searchOption
        }`
      );
      const data = await response.text();

      // Update the appState with the new search results
      appState.bd.resultsHTML = data;

      // If addHistory is true, add the new state to the history stack
      if (addHistory) {
        addToHistory();
      }

      // Update the UI with the new search results
      render();
    }
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

// Render the UI based on the current state
function render() {
  // Set the active tab
  const dpdTab = document.getElementById("dpd-tab");
  const bdTab = document.getElementById("bold-def-tab");
  const dpdTabLink = document.querySelector(".tab-link:nth-child(1)");
  const bdTabLink = document.querySelector(".tab-link:nth-child(2)");

  if (appState.activeTab === "dpd") {
    dpdTab.classList.add("active");
    bdTab.classList.remove("active");
    dpdTabLink.classList.add("active");
    bdTabLink.classList.remove("active");
  } else {
    dpdTab.classList.remove("active");
    bdTab.classList.add("active");
    dpdTabLink.classList.remove("active");
    bdTabLink.classList.add("active");
  }

  // Update the content of the search input fields
  const searchBox = document.getElementById("search-box");
  const bdSearchBox1 = document.getElementById("bd-search-box-1");
  const bdSearchBox2 = document.getElementById("bd-search-box-2");

  if (searchBox) searchBox.value = appState.dpd.searchTerm;
  if (bdSearchBox1) bdSearchBox1.value = appState.bd.searchTerm1;
  if (bdSearchBox2) bdSearchBox2.value = appState.bd.searchTerm2;

  // Update the search option
  const bdSearchOptions = document.getElementsByName("option");
  if (bdSearchOptions) {
    for (const bdSearchOption of bdSearchOptions) {
      if (bdSearchOption.value === appState.bd.searchOption) {
        bdSearchOption.checked = true;
        break;
      }
    }
  }

  // Update the content of the results panes
  const dpdResults = document.getElementById("dpd-results");
  const bdResults = document.getElementById("bd-results");

  // Update the history panel
  updateHistoryPanel();

  if (dpdResults) {
    // If there are no search results, show the startMessage
    if (appState.dpd.resultsHTML === "" && appState.dpd.searchTerm === "") {
      // Get the startMessage from home.js
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
      dpdResults.innerHTML = startMessage;
    } else {
      dpdResults.innerHTML = appState.dpd.resultsHTML;
    }
    // Apply sandhi toggle to the newly rendered content
    showHideSandhi();
  }
  if (bdResults) {
    bdResults.innerHTML = appState.bd.resultsHTML;
  }
}

// Switch to a different tab
function switchTab(tabName) {
  // Update appState.activeTab
  appState.activeTab = tabName;

  // Add the new state to the history stack
  addToHistory();

  // Display the new active tab
  render();
}

// Add a new state to the history array
function addToHistory() {
  // Create a snapshot of the current state
  const stateSnapshot = {
    activeTab: appState.activeTab,
    dpd: { ...appState.dpd },
    bd: { ...appState.bd },
  };

  // Handle the history stack (truncating forward history if necessary)
  if (appState.historyIndex < appState.history.length - 1) {
    // Truncate forward history
    appState.history = appState.history.slice(0, appState.historyIndex + 1);
  }

  // Add the new state to the history array
  appState.history.push(stateSnapshot);
  appState.historyIndex = appState.history.length - 1;
  
  // For the history panel, we only care about DPD search terms
  if (appState.activeTab === "dpd" && appState.dpd.searchTerm) {
    // Add the search term to the history panel entries
    // Avoid duplicates by checking if the term already exists
    if (!appState.historyPanelEntries.includes(appState.dpd.searchTerm)) {
      appState.historyPanelEntries.unshift(appState.dpd.searchTerm); // Add to beginning
      
      // Limit to 50 entries to prevent excessive storage
      if (appState.historyPanelEntries.length > 50) {
        appState.historyPanelEntries = appState.historyPanelEntries.slice(0, 50);
      }
    }
    
    // Save history panel entries to LOCAL storage (persists across tabs)
    try {
      const historyPanelString = JSON.stringify(appState.historyPanelEntries);
      localStorage.setItem("dpdHistoryPanel", historyPanelString);
      console.log("Saved history panel entries to LOCAL storage:", historyPanelString);
    } catch (e) {
      console.log("Failed to save history panel entries to LOCAL storage:", e);
    }
  }

  // Save full history to LOCAL storage (persists across tabs)
  try {
    const historyString = JSON.stringify(appState.history);
    localStorage.setItem("dpdFullHistory", historyString);
    console.log("Saved full history to LOCAL storage:", historyString);
    
    // Verify that the history was actually saved
    const verification = localStorage.getItem("dpdFullHistory");
    console.log("Verification - Retrieved full history from LOCAL storage:", verification);
  } catch (e) {
    console.log("Failed to save full history to LOCAL storage:", e);
  }

  // Update the browser's URL
  updateURL();

  // Log the history update for debugging
  console.log("History updated:", appState.history);
  console.log("Current history index:", appState.historyIndex);
  console.log("History panel entries:", appState.historyPanelEntries);
}

// Update the browser's URL
function updateURL() {
  let url;
  if (appState.activeTab === "dpd") {
    url = `/?tab=dpd&q=${encodeURIComponent(appState.dpd.searchTerm)}`;
  } else {
    url = `/?tab=bd&q1=${encodeURIComponent(
      appState.bd.searchTerm1
    )}&q2=${encodeURIComponent(appState.bd.searchTerm2)}&option=${
      appState.bd.searchOption
    }`;
  }

  // Update the browser's URL using history.pushState()
  window.history.pushState({ ...appState }, "", url);
}

// Handle browser back/forward navigation
function handlePopState(event) {
  if (event.state) {
    // Update appState with the new state from the history
    appState.activeTab = event.state.activeTab;
    appState.dpd = { ...event.state.dpd };
    appState.bd = { ...event.state.bd };

    // Update the browser's URL to match the restored state without adding to history
    let url;
    if (appState.activeTab === "dpd") {
      url = `/?tab=dpd&q=${encodeURIComponent(appState.dpd.searchTerm)}`;
    } else {
      url = `/?tab=bd&q1=${encodeURIComponent(
        appState.bd.searchTerm1
      )}&q2=${encodeURIComponent(appState.bd.searchTerm2)}&option=${
        appState.bd.searchOption
      }`;
    }
    window.history.replaceState({ ...appState }, "", url);

    // Update the UI
    render();
  }
}

// Set up event listeners when the page loads
document.addEventListener("DOMContentLoaded", function () {
  // Initialize the application
  initializeApp();

  // Set up event listener for browser back/forward buttons
  window.addEventListener("popstate", handlePopState);

  // Set up event listeners for tab switching
  const dpdTabLink = document.querySelector(".tab-link:nth-child(1)");
  const bdTabLink = document.querySelector(".tab-link:nth-child(2)");

  if (dpdTabLink) {
    dpdTabLink.addEventListener("click", function (e) {
      e.preventDefault();
      switchTab("dpd");
    });
  }

  if (bdTabLink) {
    bdTabLink.addEventListener("click", function (e) {
      e.preventDefault();
      switchTab("bd");
    });
  }

  // Set up event listeners for search forms
  const searchForm = document.getElementById("search-form");
  const bdSearchButton = document.getElementById("bd-search-button");
  const bdSearchBox1 = document.getElementById("bd-search-box-1");
  const bdSearchBox2 = document.getElementById("bd-search-box-2");

  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const searchBox = document.getElementById("search-box");
      if (searchBox) {
        appState.dpd.searchTerm = searchBox.value;
        performSearch();
      }
    });
  }

  if (bdSearchButton) {
    bdSearchButton.addEventListener("click", function (e) {
      e.preventDefault();

      if (bdSearchBox1) appState.bd.searchTerm1 = bdSearchBox1.value;
      if (bdSearchBox2) appState.bd.searchTerm2 = bdSearchBox2.value;

      // Get selected option
      const bdSearchOptions = document.getElementsByName("option");
      for (const option of bdSearchOptions) {
        if (option.checked) {
          appState.bd.searchOption = option.value;
          break;
        }
      }

      performSearch();
    });
  }

  // Add event listeners for BD search boxes to trigger search on Enter key
  if (bdSearchBox1) {
    bdSearchBox1.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        appState.bd.searchTerm1 = bdSearchBox1.value;
        // Get selected option
        const bdSearchOptions = document.getElementsByName("option");
        for (const option of bdSearchOptions) {
          if (option.checked) {
            appState.bd.searchOption = option.value;
            break;
          }
        }
        performSearch();
      }
    });
  }

  if (bdSearchBox2) {
    bdSearchBox2.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        // Update both search terms to ensure they have the current values from the input fields
        if (bdSearchBox1) appState.bd.searchTerm1 = bdSearchBox1.value;
        if (bdSearchBox2) appState.bd.searchTerm2 = bdSearchBox2.value;
        // Get selected option
        const bdSearchOptions = document.getElementsByName("option");
        for (const option of bdSearchOptions) {
          if (option.checked) {
            appState.bd.searchOption = option.value;
            break;
          }
        }
        performSearch();
      }
    });
  }

  // Add touch double-tap functionality
  const doubleTapDelay = 300; // milliseconds between taps to count as double-tap
  let lastTap = 0; // Last tap timestamp

  // Add touch listeners for DPD pane
  const dpdPane = document.getElementById("dpd-pane");
  const historyPane = document.getElementById("history-pane");
  if (dpdPane) {
    dpdPane.addEventListener("touchend", function (event) {
      const currentTime = new Date().getTime();
      const tapLength = currentTime - lastTap;

      // Detect double-tap
      if (tapLength < doubleTapDelay && tapLength > 0) {
        // Prevent default behavior (like zooming)
        event.preventDefault();

        // Get the selection and process it
        const selection = window.getSelection().toString();
        if (selection.trim() !== "") {
          // Update appState before calling performSearch to prevent flashing
          if (typeof appState !== "undefined" && appState.activeTab === "dpd") {
            appState.dpd.searchTerm = selection;
          }
          const searchBox = document.getElementById("search-box");
          if (searchBox) {
            searchBox.value = selection;
            performSearch();
          }
        }
      }

      lastTap = currentTime;
    });
  }

  if (historyPane) {
    historyPane.addEventListener("touchend", function (event) {
      const currentTime = new Date().getTime();
      const tapLength = currentTime - lastTap;

      // Detect double-tap
      if (tapLength < doubleTapDelay && tapLength > 0) {
        // Prevent default behavior (like zooming)
        event.preventDefault();

        // Get the selection and process it
        const selection = window.getSelection().toString();
        if (selection.trim() !== "") {
          // Update appState before calling performSearch to prevent flashing
          if (typeof appState !== "undefined" && appState.activeTab === "dpd") {
            appState.dpd.searchTerm = selection;
          }
          const searchBox = document.getElementById("search-box");
          if (searchBox) {
            searchBox.value = selection;
            performSearch();
          }
        }
      }

      lastTap = currentTime;
    });
  }

  // Add touch listener for BD results area
  const bdResults = document.getElementById("bd-results");
  if (bdResults) {
    bdResults.addEventListener("touchend", function (event) {
      const currentTime = new Date().getTime();
      const tapLength = currentTime - lastTap;

      // Detect double-tap
      if (tapLength < doubleTapDelay && tapLength > 0) {
        // Prevent default behavior (like zooming)
        event.preventDefault();

        // Get the selection and process it
        const selection = window.getSelection().toString();
        if (selection.trim() !== "") {
          // Switch to BD tab if not already active
          if (typeof appState !== "undefined" && appState.activeTab !== "bd") {
            switchTab("bd");
          }

          // Set the selected text in the first BD search box
          const bdSearchBox1 = document.getElementById("bd-search-box-1");
          if (bdSearchBox1) {
            bdSearchBox1.value = selection;
            // Update appState
            if (typeof appState !== "undefined") {
              appState.bd.searchTerm1 = selection;
            }
            // Trigger BD search
            performSearch();
          }
        }
      }

      lastTap = currentTime;
    });
  }
});

// Helper function to wrap apostrophes in span elements for hiding
function wrapApostrophesInHTML(html) {
  // Create a temporary div to manipulate the HTML
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;

  // Get all text nodes in the element
  const walker = document.createTreeWalker(
    tempDiv,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  const textNodes = [];
  let node;

  // Collect all text nodes first
  while ((node = walker.nextNode())) {
    // Only process text nodes that contain apostrophes
    if (node.nodeValue.includes("'")) {
      textNodes.push(node);
    }
  }

  // Process each text node
  textNodes.forEach((textNode) => {
    const text = textNode.nodeValue;
    // Skip if text doesn't contain apostrophes
    if (!text.includes("'")) return;

    // Create a fragment to hold the new nodes
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    let match;

    // Find all apostrophes using regex
    const regex = /'/g;
    let matchIndex;

    // Process each apostrophe
    while ((match = regex.exec(text)) !== null) {
      matchIndex = match.index;

      // Add text before the apostrophe
      if (matchIndex > lastIndex) {
        fragment.appendChild(
          document.createTextNode(text.substring(lastIndex, matchIndex))
        );
      }

      // Add the apostrophe wrapped in a span
      const span = document.createElement("span");
      span.className = "apostrophe";
      span.textContent = "'";
      fragment.appendChild(span);

      lastIndex = matchIndex + 1;
    }

    // Add any remaining text after the last apostrophe
    if (lastIndex < text.length) {
      fragment.appendChild(document.createTextNode(text.substring(lastIndex)));
    }

    // Replace the text node with our new fragment
    textNode.parentNode.replaceChild(fragment, textNode);
  });

  // Return the modified HTML
  return tempDiv.innerHTML;
}

// Function to update the history panel
function updateHistoryPanel() {
  console.log("Updating history panel");
  const historyListPane = document.getElementById("history-list-pane");
  if (!historyListPane) {
    console.log("History list pane not found");
    return;
  }
  
  // Clear the current content
  historyListPane.innerHTML = "";
  
  // Create a list element
  const ul = document.createElement("ul");
  
  // Use the history panel entries array directly
  // Show latest searches at the top (they're already in the right order)
  appState.historyPanelEntries.forEach((searchTerm, index) => {
    const li = document.createElement("li");
    let displayText = searchTerm || "(empty)";
    
    li.textContent = displayText;
    li.style.cursor = "pointer";
    
    // Add click event to search for this history item
    li.addEventListener("click", () => {
      searchHistoryItem(searchTerm);
    });
    
    ul.appendChild(li);
  });
  
  // Add the list to the history panel
  historyListPane.appendChild(ul);
  
  console.log("History panel updated with", appState.historyPanelEntries.length, "items");
}

// Function to clear the history
function clearHistory() {
  console.log("Clearing history");
  // Clear the history array
  appState.history = [];
  appState.historyIndex = -1;
  
  // Clear the history panel entries
  appState.historyPanelEntries = [];
  
  // Remove history from LOCAL storage
  try {
    localStorage.removeItem("dpdFullHistory");
    localStorage.removeItem("dpdHistoryPanel");
  } catch (e) {
    console.log("Failed to remove history from LOCAL storage:", e);
  }
  
  // Update the history panel
  updateHistoryPanel();
  
  // Update the URL to remove query parameters
  window.history.pushState({ ...appState }, "", "/");
}

// Function to perform a search for a specific history item
function searchHistoryItem(searchTerm) {
  console.log("Searching for history item:", searchTerm);
  // Set the search term in the search box
  const searchBox = document.getElementById("search-box");
  if (searchBox) {
    searchBox.value = searchTerm;
  }
  
  // Update appState with the search term
  appState.dpd.searchTerm = searchTerm;
  
  // Perform the search
  performSearch();
}

// Function to restore a specific history state (deprecated)
function restoreHistoryState(index) {
  console.log("Restoring history state at index", index);
  if (index >= 0 && index < appState.history.length) {
    // Get the state from history
    const state = appState.history[index];
    
    // For DPD searches, perform a simple search
    if (state.activeTab === "dpd" && state.dpd.searchTerm) {
      searchHistoryItem(state.dpd.searchTerm);
    }
  }
}

// Expose performSearch to the global scope
window.performSearch = performSearch;
window.switchTab = switchTab;
window.updateHistoryPanel = updateHistoryPanel;
window.clearHistory = clearHistory;
window.searchHistoryItem = searchHistoryItem;
