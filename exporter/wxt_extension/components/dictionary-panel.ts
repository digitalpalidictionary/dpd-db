import { Settings } from '../types/extension';
import { browser } from 'wxt/browser';
import { getAudioUrl } from '../utils/api';

// Define helper functions first
export function wrapApostrophesInHTML(html: string): string {
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;
  const walker = document.createTreeWalker(
    tempDiv,
    NodeFilter.SHOW_TEXT,
    null
  );
  const textNodes: Node[] = [];
  let node: Node | null;
  while ((node = walker.nextNode())) {
    if (node.nodeValue && node.nodeValue.includes("'")) textNodes.push(node);
  }
  textNodes.forEach((textNode) => {
    const text = textNode.nodeValue;
    if (!text || !text.includes("'")) return;
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    const regex = /'/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex)
        fragment.appendChild(
          document.createTextNode(text.substring(lastIndex, match.index)),
        );
      const span = document.createElement("span");
      span.className = "apostrophe";
      span.textContent = "'";
      fragment.appendChild(span);
      lastIndex = match.index + 1;
    }
    if (lastIndex < text.length)
      fragment.appendChild(
        document.createTextNode(text.substring(lastIndex)),
      );
    textNode.parentNode?.replaceChild(fragment, textNode);
  });
  return tempDiv.innerHTML;
}

export function niggahitaUp(): void {
  var dpdPane = document.querySelector(".dpd-content");
  if (!dpdPane) return;

  const walker = document.createTreeWalker(
    dpdPane,
    NodeFilter.SHOW_TEXT,
    null
  );
  let node: Node | null;
  while ((node = walker.nextNode())) {
    if (node.nodeValue) {
        node.nodeValue = node.nodeValue.replace(/ṃ/g, "ṁ");
    }
  }
}

export function niggahitaDown(): void {
  var dpdPane = document.querySelector(".dpd-content");
  if (!dpdPane) return;

  const walker = document.createTreeWalker(
    dpdPane,
    NodeFilter.SHOW_TEXT,
    null
  );
  let node: Node | null;
  while ((node = walker.nextNode())) {
    if (node.nodeValue) {
        node.nodeValue = node.nodeValue.replace(/ṁ/g, "ṃ");
    }
  }
}

export class DictionaryPanel {
  content!: HTMLDivElement;
  textNode!: HTMLDivElement;
  searchInput!: HTMLInputElement;
  searchBtn!: HTMLButtonElement | null;
  backBtn!: HTMLButtonElement;
  forwardBtn!: HTMLButtonElement;
  isResizing: boolean = false;

  history: { html: string; query: string }[] = [];
  historyIndex: number = -1;
  maxHistory: number = 50;

  settings: Settings = {
    fontSize: 16,
    niggahita: true,
    grammar: false,
    example: false,
    oneButton: true,
    summary: true,
    sandhi: true,
    audio: false,
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

    // Add feedback footer
    const footer = this._createFooter();
    panelEl.appendChild(footer);

    document.body.appendChild(panelEl);

    this._setupEvents();
    this._setupResize(handle);
    this._loadInitialSettings();
    this._updateNavigationButtons();
  }

  async _loadInitialSettings() {
    const result = await browser.storage.local.get([
      "settingsFontSize",
      "settingsNiggahita",
      "settingsGrammar",
      "settingsExample",
      "settingsSummary",
      "settingsSandhi",
      "settingsOneButton",
      "settingsAudio",
    ]) as { [key: string]: any };

    if (result.settingsFontSize !== undefined)
      this.settings.fontSize = result.settingsFontSize as number;

    // DOMAIN AWARE DEFAULTS for Niggahita
    if (result.settingsNiggahita !== undefined) {
      this.settings.niggahita = result.settingsNiggahita as boolean;
    } else {
      const domain = window.location.hostname;
      if (domain.includes("digitalpalireader")) {
        this.settings.niggahita = false; // Default OFF for DPR (ṃ)
      } else if (domain.includes("suttacentral")) {
        this.settings.niggahita = true; // Default ON for SC (ṁ)
      } else if (domain.includes("thebuddhaswords")) {
        this.settings.niggahita = true; // Default ON for TBW (ṁ)
      } else if (domain.includes("tipitaka.org")) {
        this.settings.niggahita = false; // Default OFF for VRI (ṃ)
      } else if (domain.includes("open.tipitaka.lk")) {
        this.settings.niggahita = false; // Default OFF for Tipitaka.lk (ṃ)
      }
    }

    if (result.settingsGrammar !== undefined)
      this.settings.grammar = result.settingsGrammar as boolean;
    if (result.settingsExample !== undefined)
      this.settings.example = result.settingsExample as boolean;
    if (result.settingsSummary !== undefined)
      this.settings.summary = result.settingsSummary as boolean;
    if (result.settingsSandhi !== undefined)
      this.settings.sandhi = result.settingsSandhi as boolean;
    if (result.settingsOneButton !== undefined)
      this.settings.oneButton = result.settingsOneButton as boolean;
    if (result.settingsAudio !== undefined)
      this.settings.audio = result.settingsAudio as boolean;

    this._applySettings();
  }

  _applySettings() {
    const panelEl = document.getElementById("dict-panel-25445");
    if (!panelEl) return;

    panelEl.style.fontSize = this.settings.fontSize + "px";

    // DETERMINISTIC CSS TOGGLES via Class
    panelEl.classList.toggle("dpd-hide-summary", !this.settings.summary);
    panelEl.classList.toggle("dpd-hide-sandhi", !this.settings.sandhi);

    this._updateNiggahita();
  }

  _updateNiggahita() {
    if (!this.content) return;
    if (this.settings.niggahita) {
      niggahitaUp();
    } else {
      niggahitaDown();
    }
  }

  _applySectionVisibility() {
    if (!this.content) return;

    // Initial State only for Grammar/Example (allows manual override later)
    const grammarButtons = this.content.querySelectorAll(
      '[name="grammar-button"]',
    );
    const grammarDivs = this.content.querySelectorAll('[name="grammar-div"]');
    grammarButtons.forEach((btn) =>
      btn.classList.toggle("active", this.settings.grammar),
    );
    grammarDivs.forEach((div) =>
      div.classList.toggle("hidden", !this.settings.grammar),
    );

    const exampleButtons = this.content.querySelectorAll(
      '[name="example-button"]',
    );
    const exampleDivs = this.content.querySelectorAll('[name="example-div"]');
    exampleButtons.forEach((btn) =>
      btn.classList.toggle("active", this.settings.example),
    );
    exampleDivs.forEach((div) =>
      div.classList.toggle("hidden", !this.settings.example),
    );
  }

  _saveSetting(key: keyof Settings, value: any) {
    (this.settings as any)[key] = value;
    const storageKey = "settings" + key.charAt(0).toUpperCase() + key.slice(1);
    browser.storage.local.set({ [storageKey]: value });
    this._applySettings();

    if (key === "grammar" || key === "example") {
      this._applySectionVisibility();
    }
  }

  setText(text: string) {
    this.textNode.textContent = text;
    this.textNode.style.display = "block";
    this.textNode.classList.toggle("loading", text.includes("..."));
    this.textNode.style.color = "var(--dpd-primary)";
    this.searchBtn?.classList.toggle("loading", text.includes("..."));
  }

  setContent(html: string, isNavigation: boolean = false) {
    this.textNode.style.display = "none";
    this.textNode.classList.remove("loading");
    this.searchBtn?.classList.remove("loading");

    if (!isNavigation) {
      // Clear forward history and add new entry
      if (this.historyIndex < this.history.length - 1) {
        this.history = this.history.slice(0, this.historyIndex + 1);
      }
      this.history.push({ html, query: this.searchInput.value });
      if (this.history.length > this.maxHistory) {
        this.history.shift();
      } else {
        this.historyIndex++;
      }
      this._updateNavigationButtons();
    }

    const processedHtml = wrapApostrophesInHTML(html);
    const parts = processedHtml.split('<hr class="dpd">');

    if (parts.length >= 2) {
      this.content.innerHTML = `
          <div class="summary-results">${parts[0]}<hr class="dpd"></div>
          <div id="dpd-results" class="dpd-results">${parts.slice(1).join('<hr class="dpd">')}</div>
        `;
    } else {
      this.content.innerHTML = `
          <div class="summary-results" style="display: none;"></div>
          <div id="dpd-results" class="dpd-results">${processedHtml}</div>
        `;
    }

    this.content.scrollTop = 0;
    this._updateNiggahita();
    this._applySectionVisibility();
    this._initGrammarSorter();
  }

  _navigateHistory(direction: number) {
    const newIndex = this.historyIndex + direction;
    if (newIndex >= 0 && newIndex < this.history.length) {
      this.historyIndex = newIndex;
      const entry = this.history[this.historyIndex];
      this.setSearchValue(entry.query);
      this.setContent(entry.html, true);
      this._updateNavigationButtons();
    }
  }

  _updateNavigationButtons() {
    if (this.backBtn) {
      this.backBtn.disabled = this.historyIndex <= 0;
      this.backBtn.style.opacity = this.backBtn.disabled ? "0.3" : "1";
    }
    if (this.forwardBtn) {
      this.forwardBtn.disabled = this.historyIndex >= this.history.length - 1;
      this.forwardBtn.style.opacity = this.forwardBtn.disabled ? "0.3" : "1";
    }
  }

  setSearchValue(value: string) {
    if (this.searchInput) this.searchInput.value = value;
  }

  uniCoder(textInput: string): string {
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

  _setupResize(handle: HTMLDivElement) {
    handle.addEventListener("mousedown", (e) => {
      this.isResizing = true;
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
    });
    document.addEventListener("mousemove", (e) => {
      if (!this.isResizing) return;
      const width = window.innerWidth - e.clientX;
      if (width > 200 && width < window.innerWidth * 0.8) {
        document.documentElement.style.setProperty(
          "--dpd-panel-width",
          width + "px",
        );
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
      const target = event.target as Element;
      const button = target.closest(".dpd-button");
      if (button && button.hasAttribute("data-target")) {
        event.preventDefault();
        const targetId = button.getAttribute("data-target");
        if (targetId) {
            const targetEl = this.content.querySelector("#" + CSS.escape(targetId));

            if (targetEl) {
                if (this.settings.oneButton) {
                    const allButtons = this.content.querySelectorAll(".dpd-button");
                    allButtons.forEach((btn) => {
                    if (btn !== button && btn.getAttribute("data-target"))
                        btn.classList.remove("active");
                    });
                    const allContentAreas = this.content.querySelectorAll(".content");
                    allContentAreas.forEach((area) => {
                    if (area !== targetEl && !area.classList.contains("summary"))
                        area.classList.add("hidden");
                    });
                }
                targetEl.classList.toggle("hidden");
                button.classList.toggle("active");
            }
        }
        return;
      }

      const playBtn = target.closest(".dpd-button.play");
      if (playBtn) {
        event.preventDefault();
        const headword = playBtn.getAttribute("data-headword");
        const gender = playBtn.getAttribute("data-gender");
        if (headword) this._playAudio(headword, gender || null);
        return;
      }
    });
  }

  async _playAudio(headword: string, gender: string | null) {
    if (!gender || gender === "auto") {
      gender = this.settings.audio ? "female" : "male";
    }
    const url = await getAudioUrl(headword, gender);
    const audio = new Audio(url);
    audio.play().catch((err) => console.error("Audio playback error:", err));
  }

  _initGrammarSorter() {
    const tables = this.content.querySelectorAll<HTMLTableElement>(
      "table.grammar_dict:not(.sorter-initialized)",
    );
    tables.forEach((table) => {
      const tbody = table.querySelector("tbody");
      const headers = table.querySelectorAll("th");
      if (!tbody || !headers.length) return;

      table.classList.add("sorter-initialized");
      const originalRows = Array.from(tbody.querySelectorAll("tr"));

      const letterToNumber: { [key: string]: string } = {
        "√": "00",
        a: "01",
        ā: "02",
        i: "03",
        ī: "04",
        u: "05",
        ū: "06",
        e: "07",
        o: "08",
        k: "09",
        kh: "10",
        g: "11",
        gh: "12",
        ṅ: "13",
        c: "14",
        ch: "15",
        j: "16",
        jh: "17",
        ñ: "18",
        ṭ: "19",
        ṭh: "20",
        ḍ: "21",
        ḍh: "22",
        ṇ: "23",
        t: "24",
        th: "25",
        d: "26",
        dh: "27",
        n: "28",
        p: "29",
        ph: "30",
        b: "31",
        bh: "32",
        m: "33",
        y: "34",
        r: "35",
        l: "36",
        v: "37",
        s: "38",
        h: "39",
        ḷ: "40",
        ṃ: "41",
      };

      const pattern = new RegExp(
        "kh|gh|ch|jh|ṭh|ḍh|th|ph|" +
          Object.keys(letterToNumber)
            .sort((a, b) => b.length - a.length)
            .join("|"),
        "g",
      );

      const paliSortKey = (word: string) => {
        if (!word) return "";
        return word
          .toLowerCase()
          .replace(pattern, (match) => letterToNumber[match] || match);
      };

      const updateArrows = (activeHeader: HTMLElement, order: string) => {
        headers.forEach((h) => {
          if (h.id === "col5") return;
          let text = h.textContent?.replace(/[⇅▲▼]/g, "").trim() || "";
          if (h === activeHeader) {
            if (order === "asc") text += " ▲";
            else if (order === "desc") text += " ▼";
            else text += " ⇅";
          } else {
            text += " ⇅";
          }
          h.textContent = text;
        });
      };

      headers.forEach((header) => {
        if (header.id === "col5") return;

        header.style.cursor = "pointer";
        header.addEventListener("click", (event) => {
          event.stopPropagation();
          let order = header.dataset.order || "";
          let nextOrder = "";

          if (order === "") nextOrder = "asc";
          else if (order === "asc") nextOrder = "desc";
          else nextOrder = "";

          let rowsToSort: HTMLTableRowElement[] = [];
          if (nextOrder === "") {
            rowsToSort = [...originalRows];
          } else {
            rowsToSort = Array.from(tbody.querySelectorAll("tr"));
            const colIndex = (header as HTMLTableCellElement).cellIndex;
            const isPaliCol = header.id === "col1" || header.id === "col6";

            rowsToSort.sort((a, b) => {
              let aVal = a.cells[colIndex]
                ? a.cells[colIndex].textContent?.trim() || ""
                : "";
              let bVal = b.cells[colIndex]
                ? b.cells[colIndex].textContent?.trim() || ""
                : "";
              if (isPaliCol) {
                aVal = paliSortKey(aVal);
                bVal = paliSortKey(bVal);
              }
              let cmp = aVal.localeCompare(bVal);
              return nextOrder === "asc" ? cmp : -cmp;
            });
          }

          tbody.innerHTML = "";
          rowsToSort.forEach((row) => tbody.appendChild(row));
          headers.forEach((h) => (h.dataset.order = ""));
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
    topRow.style.display = "flex";
    topRow.style.alignItems = "center";
    topRow.style.justifyContent = "space-between";
    topRow.style.width = "100%";

    const logoGroup = document.createElement("a");
    logoGroup.href = "https://dpdict.net";
    logoGroup.target = "_blank";
    logoGroup.className = "dpd-tooltip";
    logoGroup.style.display = "flex";
    logoGroup.style.alignItems = "center";
    logoGroup.style.textDecoration = "none";
    logoGroup.style.color = "inherit";

    const logoTooltip = document.createElement("span");
    logoTooltip.className = "dpd-tooltip-text";
    logoTooltip.textContent = "DPD Website";
    logoGroup.appendChild(logoTooltip);

    const logo = document.createElement("img");
    logo.src = (browser.runtime as any).getURL("icons/dpd-logo.svg");
    logo.style.height = "20px";
    logo.style.width = "20px";

    const title = document.createElement("h3");
    title.className = "dpd-title";
    title.style.margin = "0 5px";
    title.style.fontSize = "var(--dpd-title-size, 100%)";
    title.style.padding = "var(--dpd-title-padding, 0px)";
    title.style.fontFamily = "inherit";
    title.textContent = "Digital Pāḷi Dictionary";

    logoGroup.appendChild(logo);
    logoGroup.appendChild(title);

    const buttonGroup = document.createElement("div");
    buttonGroup.style.display = "flex";
    buttonGroup.style.alignItems = "center";
    buttonGroup.style.gap = "4px";

    const navGroup = document.createElement("div");
    navGroup.style.display = "flex";
    navGroup.style.alignItems = "center";
    navGroup.style.gap = "8px";
    navGroup.style.margin = "0 10px";

    const backBtn = document.createElement("button");
    this.backBtn = backBtn;
    backBtn.className = "dpd-nav-btn";
    backBtn.style.background = "none";
    backBtn.style.border = "none";
    backBtn.style.cursor = "pointer";
    backBtn.style.color = "inherit";
    backBtn.style.display = "flex";
    backBtn.style.alignItems = "center";
    backBtn.style.fontSize = "0.75rem";
    backBtn.style.gap = "2px";
    backBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg><span>Back</span>`;
    backBtn.onclick = (e) => {
      e.stopPropagation();
      this._navigateHistory(-1);
    };

    const forwardBtn = document.createElement("button");
    this.forwardBtn = forwardBtn;
    forwardBtn.className = "dpd-nav-btn";
    forwardBtn.style.background = "none";
    forwardBtn.style.border = "none";
    forwardBtn.style.cursor = "pointer";
    forwardBtn.style.color = "inherit";
    forwardBtn.style.display = "flex";
    forwardBtn.style.alignItems = "center";
    forwardBtn.style.fontSize = "0.75rem";
    forwardBtn.style.gap = "2px";
    forwardBtn.innerHTML = `<span>Forward</span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>`;
    forwardBtn.onclick = (e) => {
      e.stopPropagation();
      this._navigateHistory(1);
    };

    navGroup.appendChild(backBtn);
    navGroup.appendChild(forwardBtn);

    const infoBtn = document.createElement("button");
    infoBtn.className = "info-btn dpd-tooltip";
    infoBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>`;
    const infoTooltip = document.createElement("span");
    infoTooltip.className = "dpd-tooltip-text";
    infoTooltip.textContent = "How to use";
    infoBtn.appendChild(infoTooltip);
    infoBtn.style.background = "none";
    infoBtn.style.border = "none";
    infoBtn.style.cursor = "pointer";
    infoBtn.style.color = "inherit";
    infoBtn.onclick = () => this._showInfo();

    const themeBtn = document.createElement("button");
    themeBtn.className = "theme-selector-btn dpd-tooltip";
    themeBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4c-.83 0-1.5-.67-1.5-1.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>`;
    const themeTooltip = document.createElement("span");
    themeTooltip.className = "dpd-tooltip-text";
    themeTooltip.textContent = "Change Theme";
    themeBtn.appendChild(themeTooltip);
    themeBtn.style.background = "none";
    themeBtn.style.border = "none";
    themeBtn.style.cursor = "pointer";
    themeBtn.style.color = "inherit";
    themeBtn.onclick = () => this._toggleThemeDropdown();

    const settingsBtn = document.createElement("button");
    settingsBtn.className = "settings-selector-btn dpd-tooltip";
    settingsBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>`;
    const settingsTooltip = document.createElement("span");
    settingsTooltip.className = "dpd-tooltip-text";
    settingsTooltip.textContent = "Settings";
    settingsBtn.appendChild(settingsTooltip);
    settingsBtn.style.background = "none";
    settingsBtn.style.border = "none";
    settingsBtn.style.cursor = "pointer";
    settingsBtn.style.color = "inherit";
    settingsBtn.onclick = () => this._toggleSettingsDropdown();

    buttonGroup.appendChild(infoBtn);
    buttonGroup.appendChild(themeBtn);
    buttonGroup.appendChild(settingsBtn);
    topRow.appendChild(logoGroup);
    topRow.appendChild(navGroup);
    topRow.appendChild(buttonGroup);

    const searchRow = document.createElement("div");
    searchRow.className = "dpd-search-box";
    searchRow.style.display = "flex";
    searchRow.style.marginTop = "4px";
    searchRow.style.width = "100%";
    searchRow.style.gap = "4px";

    const input = document.createElement("input");
    this.searchInput = input;
    input.type = "text";
    input.placeholder = "type Unicode or Velthuis text";
    input.style.flex = "1";
    input.style.fontSize = "inherit";
    input.style.fontFamily = "inherit";
    input.style.padding = "2px 6px";
    input.style.border = "1px solid var(--dpd-border)";
    input.style.borderRadius = "3px";
    input.style.background = "var(--dpd-bg)";
    input.style.color = "var(--dpd-text)";

    input.addEventListener("input", () => {
      input.value = this.uniCoder(input.value);
    });

    const searchBtn = document.createElement("button");
    searchBtn.className = "dpd-search-btn dpd-tooltip";
    searchBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
    const searchTooltip = document.createElement("span");
    searchTooltip.className = "dpd-tooltip-text";
    searchTooltip.textContent = "Search";
    searchBtn.appendChild(searchTooltip);
    searchBtn.style.background = "var(--dpd-primary)";
    searchBtn.style.color = "#ffffff";
    searchBtn.style.border = "none";
    searchBtn.style.borderRadius = "3px";
    searchBtn.style.padding = "2px 8px";
    searchBtn.style.cursor = "pointer";
    this.searchBtn = searchBtn;

    var performSearch = () => {
      var q = input.value.trim();
      if (q) {
        if (typeof (window as any).handleSelectedWord === "function") {
          (window as any).handleSelectedWord(q);
        } else {
          console.error("[DPD] handleSelectedWord not found");
        }
      }
    };
    searchBtn.onclick = performSearch;
    input.onkeydown = (e) => {
      e.stopPropagation();
      if (e.key === "Enter") performSearch();
    };
    input.onkeyup = (e) => e.stopPropagation();
    input.onkeypress = (e) => e.stopPropagation();

    searchRow.appendChild(input);
    searchRow.appendChild(searchBtn);

    const stickyMsg = document.createElement("div");
    stickyMsg.style.fontSize = "0.7rem";
    stickyMsg.style.textAlign = "center";
    stickyMsg.style.marginTop = "2px";
    stickyMsg.style.opacity = "0.8";
    stickyMsg.innerHTML =
      "double-click any word on the webpage or sidebar to search<br>or highlight any word on the webpage to search";

    header.appendChild(topRow);
    header.appendChild(searchRow);
    header.appendChild(stickyMsg);
    return header;
  }

  _createFooter() {
    const footer = document.createElement("p");
    footer.className = "dpd-footer";
    
    const version = browser.runtime.getManifest().version;
    const currentUrl = encodeURIComponent(window.location.href);
    const feedbackUrl = `https://docs.google.com/forms/d/e/1FAIpQLSePKf3i_M70mK6zi9YB2WL4VTLhg0AXOCelwSQlBVTr-tJRBA/viewform?usp=pp_url&entry.438735500=${currentUrl}&entry.1433863141=${version}`;
    
    footer.innerHTML = `Having a problem? Let us know about it <a href="${feedbackUrl}" target="_blank" rel="noopener noreferrer" class="dpd-link">here</a>`;
    
    return footer;
  }

  _showInfo() {
    const isFirefox = (import.meta as any).env.BROWSER === 'firefox';
    const pinImgName = isFirefox ? "pin_firefox.png" : "pin_extension.png";
    const pinImgUrl = (browser.runtime as any).getURL(pinImgName);
    
    const chromeInstructions = `
          <b>Pin the Extension:</b><br>
          1. Click the extensions icon (🧩) in Chrome.<br>
          2. Pin the DPD extension.<br>
          3. Click the DPD icon to toggle the extension on and off<br>
    `;
    
    const firefoxInstructions = `
          <b>Pin the Extension:</b><br>
          1. Click the extensions icon (🧩) in Firefox toolbar.<br>
          2. Click the gear icon next to DPD Dictionary.<br>
          3. Select "Pin to Toolbar".<br>
          4. Click the DPD icon to toggle the extension on and off<br>
    `;

    const html = `
      <div style="padding: 10px; line-height: 1.5;">
        <h3 style="margin-top: 0; color: var(--dpd-primary);">How to Use</h3>
        
        <div style="margin-bottom: 15px;">
          ${isFirefox ? firefoxInstructions : chromeInstructions}
          <img src="${pinImgUrl}" style="width: 100%; margin-top: 8px; border-radius: 4px; border: 1px solid var(--dpd-border);" onerror="this.style.display='none'">
        </div>

        <p style="margin-bottom: 12px !important;">
          <b>Internet Required:</b><br>
          An active internet connection is required to look up words.
        </p>

        <p style="margin-bottom: 12px !important;">
          <b>How to Search:</b><br>
          • <b>Double-click</b> any word on a webpage or within this sidebar.<br>
          • <b>Highlight/Select</b> any word or phrase on the webpage.
        </p>

        </div>
    `;
    this.setContent(html);
  }

  _toggleThemeDropdown() {
    var dropdown = document.getElementById("dpd-theme-dropdown");
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

    const options: { key: string; name: string }[] = [
      { key: "auto", name: "Auto (Detect)" },
      { key: "default", name: "DPD Light" },
      { key: "dpd_dark", name: "DPD Dark" },
      { key: "dpr", name: "Digital Pāli Reader" },
      { key: "suttacentral", name: "SuttaCentral Light" },
      { key: "suttacentral_dark", name: "SuttaCentral Dark" },
      { key: "tbw_light", name: "The Buddha's Words" },
      { key: "tbw_dark", name: "The Buddha's Words Dark" },
      { key: "vri", name: "VRI (tipitaka.org)" },
      { key: "tipitakalk", name: "Tipitaka.lk" },
    ];

    options.forEach((opt) => {
      var item = document.createElement("div");
      item.className = "dpd-dropdown-item";
      item.textContent = opt.name;
      item.style.padding = "8px 12px";
      item.style.cursor = "pointer";
      item.style.fontSize = "0.85rem";
      item.style.borderBottom = "1px solid var(--dpd-border)";
      item.onmouseover = () => (item.style.background = "var(--dpd-border)");
      item.onmouseout = () => (item.style.background = "none");
      item.onclick = () => {
        this._setTheme(opt.key);
        dropdown?.remove();
      };
      dropdown?.appendChild(item);
    });
    document.getElementById("dict-panel-25445")?.appendChild(dropdown);
    var closeDropdown = (e: MouseEvent) => {
      if (dropdown && !dropdown.contains(e.target as Node)) {
        dropdown.remove();
        document.removeEventListener("click", closeDropdown);
      }
    };
    setTimeout(() => document.addEventListener("click", closeDropdown), 0);
  }

  _toggleSettingsDropdown() {
    var dropdown = document.getElementById("dpd-settings-dropdown");
    if (dropdown) {
      dropdown.remove();
      return;
    }
    dropdown = document.createElement("div");
    dropdown.id = "dpd-settings-dropdown";
    dropdown.className = "dpd-dropdown";
    dropdown.style.position = "absolute";
    dropdown.style.top = "30px";
    dropdown.style.right = "10px";
    dropdown.style.background = "var(--dpd-bg)";
    dropdown.style.border = "1px solid var(--dpd-border)";
    dropdown.style.borderRadius = "4px";
    dropdown.style.boxShadow = "0 2px 10px rgba(0,0,0,0.1)";
    dropdown.style.zIndex = "2147483647";
    dropdown.style.width = "220px";
    dropdown.style.maxHeight = "400px";
    dropdown.style.overflowY = "auto";

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

    document.getElementById("dict-panel-25445")?.appendChild(dropdown);
    this._setupSettingsEventListeners();
    var closeDropdown = (e: MouseEvent) => {
      if (dropdown && !dropdown.contains(e.target as Node)) {
        dropdown.remove();
        document.removeEventListener("click", closeDropdown);
      }
    };
    setTimeout(() => document.addEventListener("click", closeDropdown), 0);
  }

  _setupSettingsEventListeners() {
    var fontSizeDown = document.getElementById("settings-font-size-down");
    var fontSizeUp = document.getElementById("settings-font-size-up");
    var fontSizeDisplay = document.getElementById("settings-font-size-display");

    if (fontSizeDown) fontSizeDown.onclick = () => {
      if (this.settings.fontSize > 12) {
        this.settings.fontSize--;
        if (fontSizeDisplay) fontSizeDisplay.textContent = this.settings.fontSize + "px";
        this._applySettings();
        this._saveSetting("fontSize", this.settings.fontSize);
      }
    };
    if (fontSizeUp) fontSizeUp.onclick = () => {
      if (this.settings.fontSize < 24) {
        this.settings.fontSize++;
        if (fontSizeDisplay) fontSizeDisplay.textContent = this.settings.fontSize + "px";
        this._applySettings();
        this._saveSetting("fontSize", this.settings.fontSize);
      }
    };

    const toggles = [
        "settings-niggahita-toggle",
        "settings-grammar-toggle",
        "settings-example-toggle",
        "settings-onebutton-toggle",
        "settings-summary-toggle",
        "settings-sandhi-toggle",
        "settings-audio-toggle"
    ];

    toggles.forEach(id => {
        const el = document.getElementById(id) as HTMLInputElement;
        if (el) {
            const key = id.replace("settings-", "").replace("-toggle", "");
            // map key to settings key (mostly same, except case?)
            // key is lowercase, settings keys are mostly lowercase except camelCase.
            // mapping:
            // niggahita -> niggahita
            // grammar -> grammar
            // example -> example
            // onebutton -> oneButton
            // summary -> summary
            // sandhi -> sandhi
            // audio -> audio
            
            let settingsKey = key;
            if (key === 'onebutton') settingsKey = 'oneButton';

            el.onchange = (e) => this._saveSetting(settingsKey as keyof Settings, (e.target as HTMLInputElement).checked);
        }
    });
  }

  async _setTheme(themeKey: string) {
    var domain = window.location.hostname;
    await browser.storage.local.set({ ["theme_" + domain]: themeKey });
    if (typeof window.applyTheme === 'function') {
        window.applyTheme(themeKey);
    }
  }

  destroy() {
    document.getElementById("dict-panel-25445")?.remove();
  }
};

// Attach to window for legacy compatibility
if (typeof window !== 'undefined') {
    window.DictionaryPanel = DictionaryPanel;
    window.wrapApostrophesInHTML = wrapApostrophesInHTML;
    window.niggahitaUp = niggahitaUp;
    window.niggahitaDown = niggahitaDown;
}
