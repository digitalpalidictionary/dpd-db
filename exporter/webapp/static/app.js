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
};

// Initialize the application
function initializeApp() {
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
      if (
        appState.bd.searchTerm1.trim() !== "" ||
        appState.bd.searchTerm2.trim() !== ""
      ) {
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
  if (bdResults) bdResults.innerHTML = appState.bd.resultsHTML;
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

  // Update the browser's URL
  updateURL();
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

// Expose performSearch to the global scope
window.performSearch = performSearch;
window.switchTab = switchTab;
