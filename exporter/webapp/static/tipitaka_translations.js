// Tipiṭaka Translations Search Logic

const ttSearchBox = document.getElementById("tt-search-box");
const ttLangSelect = document.getElementById("tt-lang-select");
const ttBookSelect = document.getElementById("tt-book-select");
const ttSearchButton = document.getElementById("tt-search-button");
const ttClearButton = document.getElementById("tt-clear-button");
const ttFilterBox = document.getElementById("tt-filter-box");
const ttFilterMode = document.getElementById("tt-filter-mode");
const ttResults = document.getElementById("tt-results");

// Event Listeners
if (ttSearchButton) {
    ttSearchButton.addEventListener("click", function (e) {
        e.preventDefault();
        performTTSearch();
    });
}

if (ttClearButton) {
    ttClearButton.addEventListener("click", function (e) {
        e.preventDefault();
        clearTTSearch();
    });
}

if (ttSearchBox) {
    ttSearchBox.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            performTTSearch();
        }
    });
}

if (ttFilterBox) {
    ttFilterBox.addEventListener("input", function (e) {
        filterTTResults(e.target.value);
    });
}

if (ttFilterMode) {
    ttFilterMode.addEventListener("change", function () {
        filterTTResults(ttFilterBox.value);
    });
}

// Double-click to search in DPD tab
if (ttResults) {
    ttResults.addEventListener("dblclick", function () {
        const selection = window.getSelection().toString();
        if (selection.trim() !== "") {
            // Switch to DPD tab
            if (typeof appState !== "undefined") {
                appState.activeTab = "dpd";
                appState.dpd.searchTerm = selection;
            }

            // Update search box
            const searchBox = document.getElementById("search-box");
            if (searchBox) {
                searchBox.value = selection;
            }

            // Perform search and render
            if (typeof window.performSearch === "function") {
                window.performSearch();
            }
        }
    });
}

// Use the global uniCoder function from home.js for Velthuis conversion
if (ttSearchBox) {
    ttSearchBox.addEventListener("input", function () {
        let textInput = ttSearchBox.value;
        let convertedText = window.uniCoder(textInput);
        ttSearchBox.value = convertedText;
    });
}

if (ttFilterBox) {
    ttFilterBox.addEventListener("input", function () {
        let textInput = ttFilterBox.value;
        let convertedText = window.uniCoder(textInput);
        ttFilterBox.value = convertedText;
        filterTTResults(convertedText);
    });
}


async function performTTSearch(addHistory = true) {
    const buttonId = "tt-search-button";
    if (typeof window.showLoading === "function") {
        window.showLoading(buttonId);
    }

    // Try to get values from DOM elements first, fallback to appState
    const q = ttSearchBox ? ttSearchBox.value.trim() : (appState?.tt?.searchTerm || "");
    const lang = ttLangSelect ? ttLangSelect.value : (appState?.tt?.language || "Pāḷi");
    const book = ttBookSelect ? ttBookSelect.value : (appState?.tt?.book || "all");

    if (!q) {
        // Show error or just return
        return;
    }

    // Update appState
    if (typeof appState !== "undefined") {
        appState.tt.searchTerm = q;
        appState.tt.language = lang;
        appState.tt.book = book;

        // Sync search term to other tabs
        appState.dpd.searchTerm = q;
        appState.bd.searchTerm1 = q;
    }

    // Show loading state
    if (ttResults) {
        ttResults.innerHTML = '<div class="spinner"></div>';
    }

    try {
        const response = await fetch(`/tt_search?q=${encodeURIComponent(q)}&book=${encodeURIComponent(book)}&lang=${encodeURIComponent(lang)}`);
        const data = await response.json();

        let html = "";
        if (data.results.length === 0) {
            html = "<div class='tt-no-results'>No results found.</div>";
        } else {
            const totalCount = data.total;
            const limit = 100; // This should match backend limit if any, or just be display limit
            let countMessage = `Found ${totalCount} results`;
            if (totalCount > limit) {
                countMessage += `, displaying the first ${limit}`;
            }
            countMessage += ".";

            html += `<div class='tt-count'>${countMessage}</div>`;

            data.results.forEach(item => {
                let paliText = item.pali.toLowerCase();
                let engTrans = item.eng;

                // Highlight search term
                if (q) {
                    // Try to use as regex first, fall back to escaped literal if invalid
                    let regex;
                    try {
                        regex = new RegExp(`(${q})`, "gi");
                        // Test if it's valid by running it once
                        regex.test("");
                        regex.lastIndex = 0; // Reset after test
                    } catch (e) {
                        // Invalid regex, escape it as literal string
                        regex = new RegExp(`(${q.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')})`, "gi");
                    }

                    if (lang === "Pāḷi") {
                        paliText = paliText.replace(regex, "<span class='hi'>$1</span>");
                    } else {
                        engTrans = engTrans.replace(regex, "<span class='hi'>$1</span>");
                    }
                }

                html += `
                <div class="tt-item">
                    <div class="tt-pali">
                        ${item.id}. ${paliText}
                    </div>
                    <div class="tt-eng">
                        ${engTrans}
                    </div>
                    <div class="tt-meta">
                        Book: ${item.book}, Table: ${item.table}
                    </div>
                </div>
                `;
            });
        }

        if (ttResults) {
            ttResults.innerHTML = html;
        }

        // Update appState results
        if (typeof appState !== "undefined") {
            appState.tt.resultsHTML = html;

            if (addHistory) {
                addToHistory();
            }
        }

        // Save original HTML for filtering
        if (ttResults) {
            const items = ttResults.querySelectorAll(".tt-item");
            items.forEach(item => {
                item.dataset.originalHtml = item.innerHTML;
            });
        }

        // Store total count for filtering
        if (ttResults) {
            const countDiv = ttResults.querySelector(".tt-count");
            if (countDiv) {
                ttResults.dataset.originalCountText = countDiv.textContent;
                ttResults.dataset.totalCount = data.total;
            }
        }

    } catch (error) {
        console.error("Error fetching TT results:", error);
        if (ttResults) {
            ttResults.innerHTML = "<div class='error'>Error fetching results.</div>";
        }
    } finally {
        if (typeof window.hideLoading === "function") {
            window.hideLoading(buttonId);
        }
    }
}

// Expose performTTSearch globally so app.js can call it
window.performTTSearch = performTTSearch;

function clearTTSearch() {
    ttSearchBox.value = "";
    ttFilterBox.value = "";
    ttResults.innerHTML = "";

    if (typeof appState !== "undefined") {
        appState.tt.searchTerm = "";
        appState.tt.resultsHTML = "";
        // Maybe clear URL params too?
        updateURL();
    }
}

function filterTTResults(filterText) {
    if (!ttResults) return;

    const items = ttResults.querySelectorAll(".tt-item");
    const mode = ttFilterMode ? ttFilterMode.value : "with";
    let visibleCount = 0;

    // Try to create a regex, fall back to literal string if invalid
    let regex = null;
    let isRegex = false;
    if (filterText) {
        try {
            regex = new RegExp(filterText, "i"); // case-insensitive
            isRegex = true;
        } catch (e) {
            // Invalid regex, use literal string matching
            isRegex = false;
        }
    }

    items.forEach(item => {
        // Restore original HTML
        if (item.dataset.originalHtml) {
            item.innerHTML = item.dataset.originalHtml;
        }

        if (!filterText) {
            item.style.display = "";
            visibleCount++;
            return;
        }

        const textContent = item.textContent;
        let containsFilter = false;

        if (isRegex) {
            containsFilter = regex.test(textContent);
        } else {
            // Fallback to case-insensitive string matching
            containsFilter = textContent.toLowerCase().includes(filterText.toLowerCase());
        }

        // Show item based on mode
        let shouldShow = false;
        if (mode === "with") {
            shouldShow = containsFilter;
        } else if (mode === "without") {
            shouldShow = !containsFilter;
        }

        if (shouldShow) {
            item.style.display = "";
            visibleCount++;

            // Only highlight matches in "with" mode
            if (mode === "with") {
                if (isRegex) {
                    highlightTextNodesRegex(item, regex);
                } else {
                    highlightTextNodes(item, filterText.toLowerCase());
                }
            }
        } else {
            item.style.display = "none";
        }
    });

    // Update count message
    const countDiv = ttResults.querySelector(".tt-count");
    if (countDiv) {
        if (!filterText) {
            if (ttResults.dataset.originalCountText) {
                countDiv.textContent = ttResults.dataset.originalCountText;
            }
        } else {
            const total = ttResults.dataset.totalCount || items.length;
            countDiv.textContent = `Showing ${visibleCount} / ${total} results.`;
        }
    }
}

function highlightTextNodes(element, filter) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    const nodesToReplace = [];

    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node.parentNode.classList.contains("hi") || node.parentNode.tagName === "SCRIPT" || node.parentNode.tagName === "STYLE") {
            continue;
        }

        if (node.nodeValue.toLowerCase().includes(filter)) {
            nodesToReplace.push(node);
        }
    }

    nodesToReplace.forEach(node => {
        const span = document.createElement("span");
        const regex = new RegExp(`(${filter.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')})`, "gi");
        span.innerHTML = node.nodeValue.replace(regex, '<span class="hi-filter">$1</span>');
        node.parentNode.replaceChild(span, node);

        // Unwrap the outer span we just created, keeping the inner structure
        const parent = span.parentNode;
        while (span.firstChild) {
            parent.insertBefore(span.firstChild, span);
        }
        parent.removeChild(span);
    });
}

function highlightTextNodesRegex(element, regex) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    const nodesToReplace = [];

    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node.parentNode.classList.contains("hi") || node.parentNode.tagName === "SCRIPT" || node.parentNode.tagName === "STYLE") {
            continue;
        }

        if (regex.test(node.nodeValue)) {
            nodesToReplace.push(node);
        }
    }

    nodesToReplace.forEach(node => {
        const span = document.createElement("span");
        // Reset regex lastIndex for global flag
        regex.lastIndex = 0;
        span.innerHTML = node.nodeValue.replace(regex, '<span class="hi-filter">$&</span>');
        node.parentNode.replaceChild(span, node);

        // Unwrap the outer span we just created, keeping the inner structure
        const parent = span.parentNode;
        while (span.firstChild) {
            parent.insertBefore(span.firstChild, span);
        }
        parent.removeChild(span);
    });
}
