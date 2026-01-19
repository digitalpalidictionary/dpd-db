if (typeof DictionaryPanel === 'undefined') {
  window.DictionaryPanel = class {
    content;
    textNode;
    searchInput;
    isResizing = false;

    settings = {
      fontSize: 16,
      niggahita: true,
      grammar: false,
      example: false,
      oneButton: true,
      summary: true,
      sandhi: true,
      audio: false
    };

    constructor() {
      const panelEl = document.createElement("div");
      panelEl.id = "dict-panel-25445";

      const header = this._createHeader();
      header.className = "dpd-header";

      this.textNode = document.createElement("div");
      this.textNode.className = "dpd-status-text";
      this.textNode.style.display = "none";
      header.appendChild(this.textNode);

      this.content = document.createElement("div");
      this.content.className = "dpd-content";

      const handle = document.createElement("div");
      handle.className = "dpd-resize-handle";
      panelEl.appendChild(handle);
      panelEl.appendChild(header);
      panelEl.appendChild(this.content);

      document.body.appendChild(panelEl);

      this._setupEvents();
      this._setupResize(handle);
      this._loadInitialSettings();
    }

    async _loadInitialSettings() {
      const result = await chrome.storage.local.get([
        "settingsFontSize", "settingsNiggahita", "settingsGrammar",
        "settingsExample", "settingsSummary", "settingsSandhi",
        "settingsOneButton", "settingsAudio"
      ]);

      if (result.settingsFontSize !== undefined) this.settings.fontSize = result.settingsFontSize;
      
      // DOMAIN AWARE DEFAULTS for Niggahita
      if (result.settingsNiggahita !== undefined) {
        this.settings.niggahita = result.settingsNiggahita;
      } else {
        const domain = window.location.hostname;
        if (domain.includes("digitalpalireader")) {
          this.settings.niggahita = false; // Default OFF for DPR (ṃ)
        } else if (domain.includes("suttacentral")) {
          this.settings.niggahita = true; // Default ON for SC (ṁ)
        } else if (domain.includes("tipitaka.org")) {
          this.settings.niggahita = false; // Default OFF for VRI (ṃ)
        }
      }

      if (result.settingsGrammar !== undefined) this.settings.grammar = result.settingsGrammar;
      if (result.settingsExample !== undefined) this.settings.example = result.settingsExample;
      if (result.settingsSummary !== undefined) this.settings.summary = result.settingsSummary;
      if (result.settingsSandhi !== undefined) this.settings.sandhi = result.settingsSandhi;
      if (result.settingsOneButton !== undefined) this.settings.oneButton = result.settingsOneButton;
      if (result.settingsAudio !== undefined) this.settings.audio = result.settingsAudio;

      this._applySettings();
    }

    _applySettings() {
      const panelEl = document.getElementById("dict-panel-25445");
      if (!panelEl) return;

      panelEl.style.fontSize = this.settings.fontSize + "px";

      // DETERMINISTIC CSS TOGGLES via Class
      panelEl.classList.toggle("dpd-hide-summary", !this.settings.summary);
      panelEl.classList.toggle("dpd-hide-sandhi", !this.settings.sandhi);

      this._applyContentSettings();
    }

    _applyContentSettings() {
      if (!this.content) return;

      // Niggahita replacement
      if (this.settings.niggahita) { niggahitaUp(); } else { niggahitaDown(); }

      // Initial State only for Grammar/Example (allows manual override later)
      const grammarButtons = this.content.querySelectorAll('[name="grammar-button"]');
      const grammarDivs = this.content.querySelectorAll('[name="grammar-div"]');
      grammarButtons.forEach(btn => btn.classList.toggle("active", this.settings.grammar));
      grammarDivs.forEach(div => div.classList.toggle("hidden", !this.settings.grammar));

      const exampleButtons = this.content.querySelectorAll('[name="example-button"]');
      const exampleDivs = this.content.querySelectorAll('[name="example-div"]');
      exampleButtons.forEach(btn => btn.classList.toggle("active", this.settings.example));
      exampleDivs.forEach(div => div.classList.toggle("hidden", !this.settings.example));
    }

    _saveSetting(key, value) {
      this.settings[key] = value;
      const storageKey = "settings" + key.charAt(0).toUpperCase() + key.slice(1);
      chrome.storage.local.set({ [storageKey]: value });
      this._applySettings();
    }

    setText(text) {
      this.textNode.textContent = text;
      this.textNode.style.display = "block";
      this.textNode.classList.toggle("loading", text.includes("..."));
      this.textNode.style.color = "var(--dpd-primary)";
    }

    setContent(html) {
      this.textNode.style.display = "none";
      this.textNode.classList.remove("loading");

      const processedHtml = wrapApostrophesInHTML(html);
      const parts = processedHtml.split("<hr>");

      if (parts.length >= 2) {
        this.content.innerHTML = `
          <div class="summary-results">${parts[0]}<hr></div>
          <div id="dpd-results" class="dpd-results">${parts.slice(1).join("<hr>")}</div>
        `;
      } else {
        this.content.innerHTML = `
          <div class="summary-results" style="display: none;"></div>
          <div id="dpd-results" class="dpd-results">${processedHtml}</div>
        `;
      }

      this.content.scrollTop = 0;
      this._applyContentSettings();
      this._initGrammarSorter();
    }

    setSearchValue(value) {
      if (this.searchInput) this.searchInput.value = value;
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
        if (width > 200 && width < window.innerWidth * 0.8) {
          document.documentElement.style.setProperty("--dpd-panel-width", width + "px");
        }
      });
      document.addEventListener("mouseup", () => {
        this.isResizing = false;
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
      });
    }

    _setupEvents() {
      this.content.addEventListener("click", (event) => {
        const button = event.target.closest(".button");
        if (button && button.hasAttribute("data-target")) {
          event.preventDefault();
          const targetId = button.getAttribute("data-target");
          const target = this.content.querySelector("#" + CSS.escape(targetId));

          if (target) {
            if (this.settings.oneButton) {
              const allButtons = this.content.querySelectorAll('.button');
              allButtons.forEach(btn => { if (btn !== button && btn.getAttribute("data-target")) btn.classList.remove("active"); });
              const allContentAreas = this.content.querySelectorAll('.content');
              allContentAreas.forEach(area => { if (area !== target && !area.classList.contains("summary")) area.classList.add("hidden"); });
            }
            target.classList.toggle("hidden");
            button.classList.toggle("active");
          }
          return;
        }

        const playBtn = event.target.closest(".button.play");
        if (playBtn) {
          event.preventDefault();
          const headword = playBtn.getAttribute("data-headword");
          if (headword) this._playAudio(headword);
          return;
        }
      });
    }

    _playAudio(headword) {
      const gender = this.settings.audio ? "female" : "male";
      const url = "https://www.dpdict.net/audio/" + encodeURIComponent(headword) + "?gender=" + gender;
      const audio = new Audio(url);
      audio.play().catch(err => console.error("Audio playback error:", err));
    }

    _initGrammarSorter() {
      const tables = this.content.querySelectorAll('table.grammar_dict:not(.sorter-initialized)');
      tables.forEach(table => {
        const tbody = table.querySelector('tbody');
        const headers = table.querySelectorAll('th');
        if (!tbody || !headers.length) return;

        table.classList.add('sorter-initialized');
        const originalRows = Array.from(tbody.querySelectorAll('tr'));

        const letterToNumber = {
          "√": "00", "a": "01", "ā": "02", "i": "03", "ī": "04", "u": "05", "ū": "06", "e": "07", "o": "08",
          "k": "09", "kh": "10", "g": "11", "gh": "12", "ṅ": "13", "c": "14", "ch": "15", "j": "16", "jh": "17", "ñ": "18",
          "ṭ": "19", "ṭh": "20", "ḍ": "21", "ḍh": "22", "ṇ": "23", "t": "24", "th": "25", "d": "26", "dh": "27", "n": "28",
          "p": "29", "ph": "30", "b": "31", "bh": "32", "m": "33", "y": "34", "r": "35", "l": "36", "v": "37", "s": "38",
          "h": "39", "ḷ": "40", "ṃ": "41"
        };

        const pattern = new RegExp("kh|gh|ch|jh|ṭh|ḍh|th|ph|" + Object.keys(letterToNumber).sort((a, b) => b.length - a.length).join("|"), "g");

        const paliSortKey = (word) => {
          if (!word) return "";
          return word.toLowerCase().replace(pattern, (match) => letterToNumber[match] || match);
        };

        const updateArrows = (activeHeader, order) => {
          headers.forEach(h => {
            if (h.id === 'col5') return;
            let text = h.textContent.replace(/[⇅▲▼]/g, '').trim();
            if (h === activeHeader) {
              if (order === 'asc') text += ' ▲';
              else if (order === 'desc') text += ' ▼';
              else text += ' ⇅';
            } else {
              text += ' ⇅';
            }
            h.textContent = text;
          });
        };

        headers.forEach(header => {
          if (header.id === 'col5') return;

          header.style.cursor = 'pointer';
          header.addEventListener('click', (event) => {
            event.stopPropagation();
            let order = header.dataset.order || '';
            let nextOrder = '';

            if (order === '') nextOrder = 'asc';
            else if (order === 'asc') nextOrder = 'desc';
            else nextOrder = '';

            let rowsToSort = [];
            if (nextOrder === '') {
              rowsToSort = [...originalRows];
            } else {
              rowsToSort = Array.from(tbody.querySelectorAll('tr'));
              const colIndex = header.cellIndex;
              const isPaliCol = (header.id === 'col1' || header.id === 'col6');

              rowsToSort.sort((a, b) => {
                let aVal = a.cells[colIndex] ? a.cells[colIndex].textContent.trim() : "";
                let bVal = b.cells[colIndex] ? b.cells[colIndex].textContent.trim() : "";
                if (isPaliCol) {
                  aVal = paliSortKey(aVal);
                  bVal = paliSortKey(bVal);
                }
                let cmp = aVal.localeCompare(bVal);
                return nextOrder === 'asc' ? cmp : -cmp;
              });
            }

            tbody.innerHTML = '';
            rowsToSort.forEach(row => tbody.appendChild(row));
            headers.forEach(h => h.dataset.order = '');
            header.dataset.order = nextOrder;
            updateArrows(header, nextOrder);
          });
        });
      });
    }

    _createHeader() {
      const header = document.createElement("div");
      header.style.padding = "4px 8px";
      header.style.position = "relative";

      const topRow = document.createElement("div");
      topRow.style.display = "flex"; topRow.style.alignItems = "center";
      topRow.style.justifyContent = "space-between"; topRow.style.width = "100%";

      const logoGroup = document.createElement("div");
      logoGroup.style.display = "flex"; logoGroup.style.alignItems = "center";

      const logo = document.createElement("img");
      logo.src = chrome.runtime.getURL("images/dpd-logo.svg");
      logo.style.height = "20px"; logo.style.width = "20px";

      const title = document.createElement("h3");
      title.className = "dpd-title";
      title.style.margin = "0 5px"; 
      title.style.fontSize = "var(--dpd-title-size, 100%)";
      title.style.padding = "var(--dpd-title-padding, 0px)";
      title.style.fontFamily = "inherit";
      title.textContent = "Digital Pāḷi Dictionary";

      logoGroup.appendChild(logo); logoGroup.appendChild(title);

      const buttonGroup = document.createElement("div");
      buttonGroup.style.display = "flex"; buttonGroup.style.alignItems = "center"; buttonGroup.style.gap = "4px";

      const themeBtn = document.createElement("button");
      themeBtn.className = "theme-selector-btn";
      themeBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4c-.83 0-1.5-.67-1.5-1.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>`;
      themeBtn.style.background = "none"; themeBtn.style.border = "none"; themeBtn.style.cursor = "pointer"; themeBtn.style.color = "inherit";
      themeBtn.onclick = () => this._toggleThemeDropdown();

      const settingsBtn = document.createElement("button");
      settingsBtn.className = "settings-selector-btn";
      settingsBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>`;
      settingsBtn.style.background = "none"; settingsBtn.style.border = "none"; settingsBtn.style.cursor = "pointer"; settingsBtn.style.color = "inherit";
      settingsBtn.onclick = () => this._toggleSettingsDropdown();

      buttonGroup.appendChild(themeBtn); buttonGroup.appendChild(settingsBtn);
      topRow.appendChild(logoGroup); topRow.appendChild(buttonGroup);

      const searchRow = document.createElement("div");
      searchRow.className = "dpd-search-box";
      searchRow.style.display = "flex"; searchRow.style.marginTop = "4px"; searchRow.style.width = "100%"; searchRow.style.gap = "4px";

      const input = document.createElement("input");
      this.searchInput = input; input.type = "text"; input.placeholder = "Search..."; input.style.flex = "1";
      input.style.fontSize = "inherit"; input.style.fontFamily = "inherit"; input.style.padding = "2px 6px"; input.style.border = "1px solid var(--dpd-border)";
      input.style.borderRadius = "3px"; input.style.background = "var(--dpd-bg)"; input.style.color = "var(--dpd-text)";

      const searchBtn = document.createElement("button");
      searchBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
      searchBtn.style.background = "var(--dpd-primary)"; searchBtn.style.color = "#ffffff"; searchBtn.style.border = "none";
      searchBtn.style.borderRadius = "3px"; searchBtn.style.padding = "2px 8px"; searchBtn.style.cursor = "pointer";

      var performSearch = () => { var q = input.value.trim(); if (q) handleSelectedWord(q); };
      searchBtn.onclick = performSearch;
      input.onkeydown = (e) => { e.stopPropagation(); if (e.key === "Enter") performSearch(); };
      input.onkeyup = (e) => e.stopPropagation();
      input.onkeypress = (e) => e.stopPropagation();

      searchRow.appendChild(input); searchRow.appendChild(searchBtn);

      const stickyMsg = document.createElement("div");
      stickyMsg.style.fontSize = "0.7rem"; stickyMsg.style.textAlign = "center";
      stickyMsg.style.marginTop = "2px"; stickyMsg.style.opacity = "0.8";
      stickyMsg.textContent = "double-click any word on the webpage to search";

      header.appendChild(topRow); header.appendChild(searchRow); header.appendChild(stickyMsg);
      return header;
    }

    _toggleThemeDropdown() {
      var dropdown = document.getElementById("dpd-theme-dropdown");
      if (dropdown) { dropdown.remove(); return; }
      dropdown = document.createElement("div");
      dropdown.id = "dpd-theme-dropdown"; dropdown.className = "dpd-dropdown";
      dropdown.style.position = "absolute"; dropdown.style.top = "30px"; dropdown.style.right = "10px";
      dropdown.style.background = "var(--dpd-bg)"; dropdown.style.border = "1px solid var(--dpd-border)";
      dropdown.style.borderRadius = "4px"; dropdown.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
      dropdown.style.zIndex = "2147483647"; dropdown.style.width = "180px";

      [{ key: "auto", name: "Auto (Detect)" }, { key: "default", name: "DPD Light" }, { key: "dpr", name: "Digital Pāli Reader" }, { key: "suttacentral", name: "SuttaCentral" }, { key: "vri", name: "VRI (tipitaka.org)" }]
        .forEach(opt => {
          var item = document.createElement("div"); item.className = "dpd-dropdown-item"; item.textContent = opt.name;
          item.style.padding = "8px 12px"; item.style.cursor = "pointer"; item.style.fontSize = "0.85rem";
          item.style.borderBottom = "1px solid var(--dpd-border)";
          item.onmouseover = () => item.style.background = "var(--dpd-border)";
          item.onmouseout = () => item.style.background = "none";
          item.onclick = () => { this._setTheme(opt.key); dropdown.remove(); };
          dropdown.appendChild(item);
        });
      document.getElementById("dict-panel-25445").appendChild(dropdown);
      var closeDropdown = (e) => { if (!dropdown.contains(e.target)) { dropdown.remove(); document.removeEventListener("click", closeDropdown); } };
      setTimeout(() => document.addEventListener("click", closeDropdown), 0);
    }

    _toggleSettingsDropdown() {
      var dropdown = document.getElementById("dpd-settings-dropdown");
      if (dropdown) { dropdown.remove(); return; }
      dropdown = document.createElement("div");
      dropdown.id = "dpd-settings-dropdown"; dropdown.className = "dpd-dropdown";
      dropdown.style.position = "absolute"; dropdown.style.top = "30px"; dropdown.style.right = "10px";
      dropdown.style.background = "var(--dpd-bg)"; dropdown.style.border = "1px solid var(--dpd-border)";
      dropdown.style.borderRadius = "4px"; dropdown.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
      dropdown.style.zIndex = "2147483647"; dropdown.style.width = "220px"; dropdown.style.maxHeight = "400px"; dropdown.style.overflowY = "auto";

      dropdown.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px; border-bottom: 1px solid var(--dpd-border);">
          <h3 style="margin: 0; font-size: 0.85rem;">Settings</h3>
        </div>
        <div id="settings-content" style="padding: 8px;">
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Font Size</span>
            <div style="display: flex; align-items: center; gap: 4px;">
              <button id="settings-font-size-down" style="padding: 2px 6px; background: var(--dpd-border); border: none; cursor: pointer; color: inherit;">-</button>
              <span id="settings-font-size-display" style="font-size: 0.8rem; min-width: 30px; text-align: center;">${this.settings.fontSize}px</span>
              <button id="settings-font-size-up" style="padding: 2px 6px; background: var(--dpd-border); border: none; cursor: pointer; color: inherit;">+</button>
            </div>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Niggahīta ṃ / ṁ</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-niggahita-toggle" ${this.settings.niggahita ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Grammar Closed / Open</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-grammar-toggle" ${this.settings.grammar ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Example Closed / Open</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-example-toggle" ${this.settings.example ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">One Button at a Time</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-onebutton-toggle" ${this.settings.oneButton ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Summary Hide / Show</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-summary-toggle" ${this.settings.summary ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Sandhi ' Hide / Show</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-sandhi-toggle" ${this.settings.sandhi ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0;">
            <span style="font-size: 0.8rem;">Audio Male / Female</span>
            <label class="dpd-switch"><input type="checkbox" id="settings-audio-toggle" ${this.settings.audio ? "checked" : ""}><span class="dpd-slider dpd-round"></span></label>
          </div>
        </div>
      `;

      document.getElementById("dict-panel-25445").appendChild(dropdown);
      this._setupSettingsEventListeners();
      var closeDropdown = (e) => { if (!dropdown.contains(e.target)) { dropdown.remove(); document.removeEventListener("click", closeDropdown); } };
      setTimeout(() => document.addEventListener("click", closeDropdown), 0);
    }

    _setupSettingsEventListeners() {
      var fontSizeDown = document.getElementById("settings-font-size-down");
      var fontSizeUp = document.getElementById("settings-font-size-up");
      var fontSizeDisplay = document.getElementById("settings-font-size-display");

      fontSizeDown.onclick = () => { if (this.settings.fontSize > 12) { this.settings.fontSize--; fontSizeDisplay.textContent = this.settings.fontSize + "px"; this._applySettings(); this._saveSetting("fontSize", this.settings.fontSize); } };
      fontSizeUp.onclick = () => { if (this.settings.fontSize < 24) { this.settings.fontSize++; fontSizeDisplay.textContent = this.settings.fontSize + "px"; this._applySettings(); this._saveSetting("fontSize", this.settings.fontSize); } };

      document.getElementById("settings-niggahita-toggle").onchange = (e) => this._saveSetting("niggahita", e.target.checked);
      document.getElementById("settings-grammar-toggle").onchange = (e) => this._saveSetting("grammar", e.target.checked);
      document.getElementById("settings-example-toggle").onchange = (e) => this._saveSetting("example", e.target.checked);
      document.getElementById("settings-onebutton-toggle").onchange = (e) => this._saveSetting("oneButton", e.target.checked);
      document.getElementById("settings-summary-toggle").onchange = (e) => this._saveSetting("summary", e.target.checked);
      document.getElementById("settings-sandhi-toggle").onchange = (e) => this._saveSetting("sandhi", e.target.checked);
      document.getElementById("settings-audio-toggle").onchange = (e) => this._saveSetting("audio", e.target.checked);
    }

    async _setTheme(themeKey) {
      var domain = window.location.hostname;
      await chrome.storage.local.set({ ["theme_" + domain]: themeKey });
      window.applyTheme(themeKey);
    }

    destroy() { document.getElementById("dict-panel-25445")?.remove(); }
  };
}

if (typeof wrapApostrophesInHTML === 'undefined') {
  window.wrapApostrophesInHTML = function (html) {
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = html;
    const walker = document.createTreeWalker(tempDiv, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) { if (node.nodeValue.includes("'")) textNodes.push(node); }
    textNodes.forEach((textNode) => {
      const text = textNode.nodeValue;
      if (!text.includes("'")) return;
      const fragment = document.createDocumentFragment();
      let lastIndex = 0;
      const regex = /'/g;
      let match;
      while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) fragment.appendChild(document.createTextNode(text.substring(lastIndex, match.index)));
        const span = document.createElement("span");
        span.className = "apostrophe"; span.textContent = "'";
        fragment.appendChild(span);
        lastIndex = match.index + 1;
      }
      if (lastIndex < text.length) fragment.appendChild(document.createTextNode(text.substring(lastIndex)));
      textNode.parentNode.replaceChild(fragment, textNode);
    });
    return tempDiv.innerHTML;
  };
}

if (typeof niggahitaUp === 'undefined') {
  window.niggahitaUp = function () {
    var dpdPane = document.querySelector(".dpd-content");
    if (!dpdPane) return;
    dpdPane.innerHTML = dpdPane.innerHTML.replace(/ṃ/g, "ṁ");
  };
}

if (typeof niggahitaDown === 'undefined') {
  window.niggahitaDown = function () {
    var dpdPane = document.querySelector(".dpd-content");
    if (!dpdPane) return;
    dpdPane.innerHTML = dpdPane.innerHTML.replace(/ṁ/g, "ṃ");
  };
}

window.panel = window.panel || null;