class DictionaryPanel {
  content;
  textNode;
  searchInput;
  isResizing = false;
  audioVoice = "male";

  constructor() {
    const panel = document.createElement("div");
    panel.id = "dict-panel-25445";

    const header = this._createHeader();
    header.className = "dpd-header";

    this.textNode = document.createElement("div");
    this.textNode.className = "dpd-status-text";
    this.textNode.textContent = "Click on a word on the page to see its definition";
    header.appendChild(this.textNode);

    this.content = document.createElement("div");
    this.content.className = "dpd-content";

    // Resize Handle
    const handle = document.createElement("div");
    handle.className = "dpd-resize-handle";
    panel.appendChild(handle);

    panel.appendChild(header);
    panel.appendChild(this.content);

    document.body.appendChild(panel);

    this._setupEvents();
    this._setupResize(handle);
    this._loadInitialSettings();
  }

  _loadInitialSettings() {
    chrome.storage.local.get([
      "settingsFontSize",
      "settingsNiggahita",
      "settingsGrammar",
      "settingsExample",
      "settingsSummary",
      "settingsSandhi",
      "settingsAudio"
    ], (result) => {
      if (result.settingsFontSize !== undefined) {
        document.getElementById("dict-panel-25445").style.fontSize = `${result.settingsFontSize}px`;
      }
      if (result.settingsAudio !== undefined) {
        this.audioVoice = result.settingsAudio ? "female" : "male";
      }
    });
  }

  setText(text) {
    this.textNode.textContent = text;
    this.textNode.style.display = "block";
  }

  setContent(html) {
    this.textNode.style.display = "none";

    // Split content into summary and main parts
    const parts = html.split("<hr>");
    if (parts.length === 2) {
      // Content has both summary and main html
      const summaryHtml = parts[0];
      const mainHtml = parts[1];

      this.content.innerHTML = `
        <div class="summary-results">${summaryHtml}</div>
        <div class="dpd-results">${mainHtml}</div>
      `;
    } else {
      // Content is just main html or just summary
      this.content.innerHTML = `
        <div class="dpd-results">${html}</div>
      `;
    }

    if (window.initSorter) {
      window.initSorter();
    }
    this._applySettingsToContent();
  }

  _applySettingsToContent() {
    chrome.storage.local.get([
      "settingsNiggahita",
      "settingsGrammar",
      "settingsExample",
      "settingsSummary",
      "settingsSandhi"
    ], (result) => {
      if (result.settingsNiggahita !== undefined) {
        this._applyNiggahita(result.settingsNiggahita);
      }
      if (result.settingsGrammar !== undefined) {
        this._applyGrammarToggle(result.settingsGrammar);
      }
      if (result.settingsExample !== undefined) {
        this._applyExampleToggle(result.settingsExample);
      }
      if (result.settingsSummary !== undefined) {
        this._applySummaryToggle(result.settingsSummary);
      }
      if (result.settingsSandhi !== undefined) {
        this._applySandhiToggle(result.settingsSandhi);
      }
    });
  }

  setSearchValue(value) {
    if (this.searchInput) {
      this.searchInput.value = value;
    }
  }

  _setupResize(handle) {
    handle.addEventListener("mousedown", (e) => {
      this.isResizing = true;
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
    });

    document.addEventListener("mousemove", (e) => {
      if (!this.isResizing) return;
      
      const width = window.innerWidth - e.clientX;
      const minWidth = 200;
      const maxWidth = window.innerWidth * 0.8;
      
      if (width > minWidth && width < maxWidth) {
        document.documentElement.style.setProperty("--dpd-panel-width", `${width}px`);
      }
    });

    document.addEventListener("mouseup", () => {
      if (this.isResizing) {
        this.isResizing = false;
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
      }
    });
  }

  _setupEvents() {
    this.content.addEventListener("click", (event) => {
      // Handle button toggles
      const button = event.target.closest(".button");
      if (button && button.hasAttribute("data-target")) {
        event.preventDefault();
        const targetId = button.getAttribute("data-target");
        const target = this.content.querySelector(`#${CSS.escape(targetId)}`);
        if (target) {
          target.classList.toggle("hidden");
          button.classList.toggle("active");
        }
        return;
      }

      // Handle audio play
      const playBtn = event.target.closest(".button.play");
      if (playBtn) {
        event.preventDefault();
        const headword = playBtn.getAttribute("data-headword");
        if (headword) {
          this._playAudio(headword);
        }
        return;
      }
    });
  }

  _playAudio(headword) {
    const url = `https://www.dpdict.net/audio/${encodeURIComponent(headword)}?gender=${this.audioVoice}`;
    const audio = new Audio(url);
    audio.play().catch(err => console.error("Audio playback error:", err));
  }

  _createHeader() {
    const header = document.createElement("div");
    header.style.padding = "4px 8px";
    header.style.position = "relative";

    const topRow = document.createElement("div");
    topRow.style.display = "flex";
    topRow.style["align-items"] = "center";
    topRow.style.justifyContent = "space-between";
    topRow.style.width = "100%";

    const logoGroup = document.createElement("div");
    logoGroup.style.display = "flex";
    logoGroup.style["align-items"] = "center";

    const logo = document.createElement("img");
    logo.src = chrome.runtime.getURL("images/dpd-logo.svg");
    logo.style.verticalAlign = "middle";
    logo.style.height = "20px";
    logo.style.width = "20px";

    const title = document.createElement("h3");
    title.style.margin = "0 5px";
    title.style.fontSize = "0.9rem";
    title.textContent = "Digital Pāḷi Dictionary";

    logoGroup.appendChild(logo);
    logoGroup.appendChild(title);

    // Theme and Settings Button Group
    const buttonGroup = document.createElement("div");
    buttonGroup.style.display = "flex";
    buttonGroup.style["align-items"] = "center";
    buttonGroup.style.gap = "4px";

    // Theme Selector
    const themeBtn = document.createElement("button");
    themeBtn.className = "theme-selector-btn";
    themeBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4c-.83 0-1.5-.67-1.5-1.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
      </svg>
    `;
    themeBtn.style.background = "none";
    themeBtn.style.border = "none";
    themeBtn.style.cursor = "pointer";
    themeBtn.style.color = "inherit";
    themeBtn.title = "Change Theme";

    themeBtn.onclick = (e) => {
      this._toggleThemeDropdown();
    };

    // Settings Cog Icon
    const settingsBtn = document.createElement("button");
    settingsBtn.className = "settings-selector-btn";
    settingsBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
      </svg>
    `;
    settingsBtn.style.background = "none";
    settingsBtn.style.border = "none";
    settingsBtn.style.cursor = "pointer";
    settingsBtn.style.color = "inherit";
    settingsBtn.title = "Settings";

    settingsBtn.onclick = (e) => {
      this._toggleSettingsDropdown();
    };

    buttonGroup.appendChild(themeBtn);
    buttonGroup.appendChild(settingsBtn);

    topRow.appendChild(logoGroup);
    topRow.appendChild(buttonGroup);

    // Search Row
    const searchRow = document.createElement("div");
    searchRow.className = "dpd-search-box";
    searchRow.style.display = "flex";
    searchRow.style.marginTop = "4px";
    searchRow.style.width = "100%";
    searchRow.style.gap = "4px";

    const input = document.createElement("input");
    this.searchInput = input;
    input.type = "text";
    input.placeholder = "Search...";
    input.style.flex = "1";
    input.style.fontSize = "0.85rem";
    input.style.padding = "2px 6px";
    input.style.border = "1px solid var(--dpd-border)";
    input.style.borderRadius = "3px";
    input.style.background = "var(--dpd-bg)";
    input.style.color = "var(--dpd-text)";

    const searchBtn = document.createElement("button");
    searchBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
    `;
    searchBtn.style.background = "var(--dpd-primary)";
    searchBtn.style.color = "#ffffff";
    searchBtn.style.border = "none";
    searchBtn.style.borderRadius = "3px";
    searchBtn.style.padding = "2px 8px";
    searchBtn.style.cursor = "pointer";

    const performSearch = () => {
      const q = input.value.trim();
      if (q) handleSelectedWord(q);
    };

    searchBtn.onclick = performSearch;
    input.onkeydown = (e) => {
      e.stopPropagation(); // Prevent host page from stealing focus
      if (e.key === "Enter") performSearch();
    };
    input.onkeyup = (e) => e.stopPropagation();
    input.onkeypress = (e) => e.stopPropagation();

    searchRow.appendChild(input);
    searchRow.appendChild(searchBtn);

    header.appendChild(topRow);
    header.appendChild(searchRow);

    return header;
  }

  _toggleThemeDropdown() {
    let dropdown = document.getElementById("dpd-theme-dropdown");
    if (dropdown) {
      dropdown.remove();
      return;
    }

    dropdown = document.createElement("div");
    dropdown.id = "dpd-theme-dropdown";
    dropdown.className = "dpd-dropdown";
    dropdown.style.position = "absolute";
    dropdown.style.top = "30px";
    dropdown.style.right = "10px";
    dropdown.style.background = "var(--dpd-bg)";
    dropdown.style.border = "1px solid var(--dpd-border)";
    dropdown.style.borderRadius = "4px";
    dropdown.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
    dropdown.style.zIndex = "2147483647";
    dropdown.style.width = "180px";

    const options = [
      { key: "auto", name: "Auto (Detect)" },
      { key: "default", name: "DPD Light" },
      { key: "dpr", name: "Digital Pāli Reader" },
      { key: "suttacentral", name: "SuttaCentral" }
    ];

    options.forEach(opt => {
      const item = document.createElement("div");
      item.className = "dpd-dropdown-item";
      item.textContent = opt.name;
      item.style.padding = "8px 12px";
      item.style.cursor = "pointer";
      item.style.fontSize = "0.85rem";
      item.style.borderBottom = "1px solid var(--dpd-border)";
      
      item.onmouseover = () => item.style.background = "var(--dpd-border)";
      item.onmouseout = () => item.style.background = "none";
      
      item.onclick = (e) => {
        this._setTheme(opt.key);
        dropdown.remove();
      };
      
      dropdown.appendChild(item);
    });

    document.getElementById("dict-panel-25445").appendChild(dropdown);
    
    // Close dropdown when clicking outside
    const closeDropdown = (e) => {
      if (!dropdown.contains(e.target)) {
        dropdown.remove();
        document.removeEventListener("click", closeDropdown);
      }
    };
    setTimeout(() => document.addEventListener("click", closeDropdown), 0);
  }

  async _toggleSettingsDropdown() {
    let dropdown = document.getElementById("dpd-settings-dropdown");
    if (dropdown) {
      dropdown.remove();
      return;
    }

    dropdown = document.createElement("div");
    dropdown.id = "dpd-settings-dropdown";
    dropdown.className = "dpd-dropdown";
    dropdown.style.position = "absolute";
    dropdown.style.top = "30px";
    dropdown.style.right = "30px";
    dropdown.style.background = "var(--dpd-bg)";
    dropdown.style.border = "1px solid var(--dpd-border)";
    dropdown.style.borderRadius = "4px";
    dropdown.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
    dropdown.style.zIndex = "2147483647";
    dropdown.style.width = "200px";
    dropdown.style.maxHeight = "400px";
    dropdown.style.overflowY = "auto";

    dropdown.innerHTML = `
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px; border-bottom: 1px solid var(--dpd-border);">
          <h3 style="margin: 0; font-size: 0.85rem;">Settings</h3>
          <button id="settings-collapse-toggle" style="background: none; border: none; cursor: pointer; color: inherit; padding: 0;">
            <span class="collapse-icon">▼</span>
          </button>
        </div>
        <div id="settings-content" style="padding: 8px;">
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Font Size</span>
          <div style="display: flex; align-items: center; gap: 4px;">
            <button id="settings-font-size-down" style="padding: 2px 6px; background: var(--dpd-border); border: none; cursor: pointer; color: inherit;">-</button>
            <span id="settings-font-size-display" style="font-size: 0.8rem; min-width: 30px; text-align: center;">16px</span>
            <button id="settings-font-size-up" style="padding: 2px 6px; background: var(--dpd-border); border: none; cursor: pointer; color: inherit;">+</button>
          </div>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Niggahīta ṃ / ṁ</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-niggahita-toggle" style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Grammar Closed / Open</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-grammar-toggle" style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Example Closed / Open</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-example-toggle" style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Summary Hide / Show</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-summary-toggle" checked style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Sandhi ' Hide / Show</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-sandhi-toggle" checked style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
          <span style="font-size: 0.8rem;">Audio Male / Female</span>
          <label class="dpd-switch" style="display: inline-block; width: 36px; height: 20px; position: relative;">
            <input type="checkbox" id="settings-audio-toggle" style="opacity: 0; width: 0; height: 0;">
            <span class="dpd-slider dpd-round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--dpd-border); transition: 0.4s;"></span>
          </label>
        </div>
        </div>
      </div>
    `;

    document.getElementById("dict-panel-25445").appendChild(dropdown);

    this._setupSettingsEventListeners();

    // Close dropdown when clicking outside
    const closeDropdown = (e) => {
      if (!dropdown.contains(e.target)) {
        dropdown.remove();
        document.removeEventListener("click", closeDropdown);
      }
    };
    setTimeout(() => document.addEventListener("click", closeDropdown), 0);
  }

  _setupSettingsEventListeners() {
    const collapseToggle = document.getElementById("settings-collapse-toggle");
    const settingsContent = document.getElementById("settings-content");

    // Load collapsed state
    chrome.storage.local.get(["settingsCollapsed"], (result) => {
      if (result.settingsCollapsed) {
        settingsContent.style.display = "none";
        collapseToggle.querySelector(".collapse-icon").textContent = "▶";
      }
    });

    // Collapse toggle functionality
    collapseToggle.onclick = () => {
      const isCollapsed = settingsContent.style.display === "none";
      settingsContent.style.display = isCollapsed ? "block" : "none";
      collapseToggle.querySelector(".collapse-icon").textContent = isCollapsed ? "▼" : "▶";
      chrome.storage.local.set({ settingsCollapsed: !isCollapsed });
    };

    const fontSizeDown = document.getElementById("settings-font-size-down");
    const fontSizeUp = document.getElementById("settings-font-size-up");
    const fontSizeDisplay = document.getElementById("settings-font-size-display");
    const niggahitaToggle = document.getElementById("settings-niggahita-toggle");
    const grammarToggle = document.getElementById("settings-grammar-toggle");
    const exampleToggle = document.getElementById("settings-example-toggle");
    const summaryToggle = document.getElementById("settings-summary-toggle");
    const sandhiToggle = document.getElementById("settings-sandhi-toggle");
    const audioToggle = document.getElementById("settings-audio-toggle");

    let fontSize = 16;

    chrome.storage.local.get(["settingsFontSize"], (result) => {
      if (result.settingsFontSize) {
        fontSize = result.settingsFontSize;
        fontSizeDisplay.textContent = `${fontSize}px`;
        document.getElementById("dict-panel-25445").style.fontSize = `${fontSize}px`;
      }
    });

    fontSizeDown.onclick = () => {
      if (fontSize > 12) {
        fontSize--;
        fontSizeDisplay.textContent = `${fontSize}px`;
        document.getElementById("dict-panel-25445").style.fontSize = `${fontSize}px`;
        chrome.storage.local.set({ settingsFontSize: fontSize });
      }
    };

    fontSizeUp.onclick = () => {
      if (fontSize < 24) {
        fontSize++;
        fontSizeDisplay.textContent = `${fontSize}px`;
        document.getElementById("dict-panel-25445").style.fontSize = `${fontSize}px`;
        chrome.storage.local.set({ settingsFontSize: fontSize });
      }
    };

    const setupToggle = (toggleElement, key, callback) => {
      chrome.storage.local.get([key], (result) => {
        if (result[key] !== undefined) {
          toggleElement.checked = result[key];
          if (callback) callback(result[key]);
        }
      });

      toggleElement.onchange = (e) => {
        const value = e.target.checked;
        chrome.storage.local.set({ [key]: value });
        if (callback) callback(value);
      };
    };

    setupToggle(sansSerifToggle, "settingsSansSerif", (value) => {
      this._applyFontFamily(value);
    });

    setupToggle(niggahitaToggle, "settingsNiggahita", (value) => {
      this._applyNiggahita(value);
    });

    setupToggle(grammarToggle, "settingsGrammar", (value) => {
      this._applyGrammarToggle(value);
    });

    setupToggle(exampleToggle, "settingsExample", (value) => {
      this._applyExampleToggle(value);
    });

    setupToggle(summaryToggle, "settingsSummary", (value) => {
      this._applySummaryToggle(value);
    });

    setupToggle(sandhiToggle, "settingsSandhi", (value) => {
      this._applySandhiToggle(value);
    });

    setupToggle(audioToggle, "settingsAudio", (value) => {
      this.audioVoice = value ? "female" : "male";
    });
  }

  _applyNiggahita(isNiggahitaUp) {
    const dpdPane = document.querySelector(".dpd-content");
    if (!dpdPane) return;
    
    if (isNiggahitaUp) {
      dpdPane.innerHTML = dpdPane.innerHTML.replace(/ṃ/g, "ṁ");
    } else {
      dpdPane.innerHTML = dpdPane.innerHTML.replace(/ṁ/g, "ṃ");
    }
  }

  _applyGrammarToggle(isOpen) {
    const panel = document.getElementById("dict-panel-25445");
    if (!panel) return;

    const grammarButtons = panel.querySelectorAll('[name="grammar-button"]');
    const grammarDivs = panel.querySelectorAll('[name="grammar-div"]');

    grammarButtons.forEach((button) => {
      if (isOpen) {
        button.classList.add("active");
      } else {
        button.classList.remove("active");
      }
    });

    grammarDivs.forEach((div) => {
      if (isOpen) {
        div.classList.remove("hidden");
      } else {
        div.classList.add("hidden");
      }
    });
  }

  _applyExampleToggle(isOpen) {
    const panel = document.getElementById("dict-panel-25445");
    if (!panel) return;

    const exampleButtons = panel.querySelectorAll('[name="example-button"]');
    const exampleDivs = panel.querySelectorAll('[name="example-div"]');

    exampleButtons.forEach((button) => {
      if (isOpen) {
        button.classList.add("active");
      } else {
        button.classList.remove("active");
      }
    });

    exampleDivs.forEach((div) => {
      if (isOpen) {
        div.classList.remove("hidden");
      } else {
        div.classList.add("hidden");
      }
    });
  }

  _applySummaryToggle(isShow) {
    const summaryResults = document.querySelector(".summary-results");
    if (!summaryResults) return;
    summaryResults.style.display = isShow ? "block" : "none";
  }

  _applySandhiToggle(isShow) {
    const dpdResults = document.querySelector(".dpd-results");
    if (!dpdResults) return;

    if (isShow) {
      dpdResults.classList.remove("hide-apostrophes");
      this._restoreApostrophes();
    } else {
      dpdResults.classList.add("hide-apostrophes");
      this._hideApostrophes();
    }
  }

  _hideApostrophes() {
    const dpdResults = document.querySelector(".dpd-results");
    if (!dpdResults) return;

    dpdResults.querySelectorAll(".sandhi").forEach(el => {
      el.dataset.originalText = el.innerHTML;
      el.innerHTML = el.innerHTML.replace(/'/g, "");
    });
  }

  _restoreApostrophes() {
    const dpdResults = document.querySelector(".dpd-results");
    if (!dpdResults) return;

    dpdResults.querySelectorAll(".sandhi").forEach(el => {
      if (el.dataset.originalText) {
        el.innerHTML = el.dataset.originalText;
        delete el.dataset.originalText;
      }
    });
  }

  async _setTheme(themeKey) {
    const domain = window.location.hostname;
    await chrome.storage.local.set({ [`theme_${domain}`]: themeKey });
    applyTheme(themeKey);
  }

  destroy() {
    document.getElementById("dict-panel-25445").remove();
  }
}

/**
 * @type {DictionaryPanel | null}
 */
let panel = null;
