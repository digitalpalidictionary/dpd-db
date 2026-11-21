// Database Query tab: filter headwords by their fields, show them in a table,
// keep presets and export the results.
(function () {
  const form = document.getElementById("dq-form");
  if (!form) return;

  const PRESETS_KEY = "dqPresets";
  const RESPONSIVE_KEY = "dqFetchAllFields";

  const filterList = document.getElementById("dq-filters");
  const filterTemplate = document.getElementById("dq-filter-template");
  const addFilterButton = document.getElementById("dq-add-filter");
  const maxFilters = Number(addFilterButton.dataset.max) || 10;
  const columnsButton = document.getElementById("dq-columns-btn");
  const columnsMenu = document.getElementById("dq-columns-menu");
  const columnsSearch = document.getElementById("dq-columns-search");
  const columnsText = document.getElementById("dq-columns-text");
  const limitInput = document.getElementById("dq-limit");
  const responsiveBox = document.getElementById("dq-responsive");
  const clearButton = document.getElementById("dq-clear-button");
  const presetSelect = document.getElementById("dq-preset-select");
  const presetName = document.getElementById("dq-preset-name");
  const exportTsvButton = document.getElementById("dq-export-tsv");
  const exportJsonButton = document.getElementById("dq-export-json");
  const results = document.getElementById("dq-results");

  const columnBoxes = Array.from(columnsMenu.querySelectorAll(".dq-column"));
  const allColumns = columnBoxes.map(box => box.value);
  const defaultColumns = columnBoxes.filter(box => box.defaultChecked).map(box => box.value);
  const maxLimit = Number(limitInput.max) || 100;

  // The last answer: { columns, rows, more, error }. Rows hold every column
  // that was fetched, in the order of `columns`.
  let lastResult = null;
  let latestRequest = 0;

  function readStorage(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function writeStorage(key, value) {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (e) {
      // Storage can be full or blocked; the tab still works without it.
      return false;
    }
  }

  // Filters

  function filterRows() {
    return Array.from(filterList.querySelectorAll(".dq-filter-row"));
  }

  function addFilter(filter = {}) {
    const row = filterTemplate.content.firstElementChild.cloneNode(true);
    row.querySelector(".dq-logic").value = filter.logic === "or" ? "or" : "and";
    row.querySelector(".dq-field").value = filter.field ?? "lemma_1";
    row.querySelector(".dq-search-type").value = filter.search || "contains";
    row.querySelector(".dq-value").value = filter.value ?? "";
    filterList.appendChild(row);
    updateFilterRows();
    return row;
  }

  // The first filter joins nothing, and the last one cannot be removed.
  // An "or" starts a new group, which is set apart from the one above.
  function updateFilterRows() {
    const rows = filterRows();
    rows.forEach((row, i) => {
      const logic = row.querySelector(".dq-logic");
      logic.hidden = i === 0;
      row.classList.toggle("dq-or", i > 0 && logic.value === "or");
      row.querySelector(".dq-remove").disabled = rows.length === 1;
    });
    // The server refuses more filters than this
    addFilterButton.disabled = rows.length >= maxFilters;
  }

  function setFilters(filters) {
    filterList.replaceChildren();
    (filters.length ? filters : [{}]).forEach(filter => addFilter(filter));
  }

  function readFilters() {
    return filterRows().map((row, i) => ({
      logic: i === 0 ? "and" : row.querySelector(".dq-logic").value,
      field: row.querySelector(".dq-field").value.trim(),
      search: row.querySelector(".dq-search-type").value,
      value: row.querySelector(".dq-value").value,
    }));
  }

  filterList.addEventListener("click", function (e) {
    const remove = e.target.closest(".dq-remove");
    if (!remove || remove.disabled) return;
    const row = remove.closest(".dq-filter-row");
    const rows = filterRows();
    const next = rows[rows.indexOf(row) + 1] || rows[rows.indexOf(row) - 1];
    row.remove();
    updateFilterRows();
    next?.querySelector(".dq-value").focus();
  });

  filterList.addEventListener("change", function (e) {
    if (e.target.classList.contains("dq-logic")) updateFilterRows();
  });

  filterList.addEventListener("input", function (e) {
    if (e.target.classList.contains("dq-field")) e.target.removeAttribute("aria-invalid");
  });

  addFilterButton.addEventListener("click", function () {
    addFilter({ field: "" }).querySelector(".dq-field").focus();
  });

  // Fields to show

  function selectedColumns() {
    return columnBoxes.filter(box => box.checked).map(box => box.value);
  }

  function setColumns(columns) {
    const wanted = new Set(columns.filter(column => allColumns.includes(column)));
    if (wanted.size === 0) defaultColumns.forEach(column => wanted.add(column));
    columnBoxes.forEach(box => { box.checked = wanted.has(box.value); });
    updateColumnsText();
  }

  function updateColumnsText() {
    const count = selectedColumns().length;
    columnsText.textContent = count === 1 ? "1 field" : `${count} fields`;
  }

  function openColumnsMenu(open) {
    columnsMenu.classList.toggle("show", open);
    columnsButton.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) columnsSearch.focus();
  }

  columnsButton.addEventListener("click", function () {
    openColumnsMenu(!columnsMenu.classList.contains("show"));
  });

  document.addEventListener("click", function (e) {
    if (!columnsMenu.contains(e.target) && !columnsButton.contains(e.target)) {
      openColumnsMenu(false);
    }
  });

  columnsMenu.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      openColumnsMenu(false);
      columnsButton.focus();
    } else if (e.key === "Enter" && e.target === columnsSearch) {
      // Enter picks the only field left, instead of sending the form
      e.preventDefault();
      const visible = columnBoxes.filter(box => !box.parentElement.hidden);
      if (visible.length === 1) {
        visible[0].checked = !visible[0].checked;
        visible[0].dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  });

  columnsSearch.addEventListener("input", function () {
    const term = columnsSearch.value.trim().toLowerCase();
    columnBoxes.forEach(box => {
      box.parentElement.hidden = term !== "" && !box.value.includes(term);
    });
  });

  columnsMenu.addEventListener("change", function (e) {
    if (!e.target.classList.contains("dq-column")) return;
    // At least one field is always shown
    if (selectedColumns().length === 0) e.target.checked = true;
    updateColumnsText();
    renderResults();
  });

  document.getElementById("dq-columns-default").addEventListener("click", function () {
    setColumns(defaultColumns);
    renderResults();
  });

  // Fetch all fields

  responsiveBox.checked = readStorage(RESPONSIVE_KEY) === "true";
  responsiveBox.addEventListener("change", function () {
    writeStorage(RESPONSIVE_KEY, responsiveBox.checked ? "true" : "false");
  });

  // Search

  function readLimit() {
    const limit = Math.round(Number(limitInput.value));
    if (!Number.isFinite(limit) || limit < 1) return maxLimit;
    return Math.min(limit, maxLimit);
  }

  function showMessage(text, isError) {
    const message = document.createElement("p");
    message.className = isError ? "error" : "message";
    if (isError) message.setAttribute("role", "alert");
    message.textContent = text;
    results.replaceChildren(message);
  }

  function performQuery() {
    const filters = readFilters();
    let invalid = null;
    filterRows().forEach((row, i) => {
      const field = row.querySelector(".dq-field");
      const bad = filters[i].value !== "" && !allColumns.includes(filters[i].field);
      if (bad) field.setAttribute("aria-invalid", "true");
      else field.removeAttribute("aria-invalid");
      if (bad && !invalid) invalid = field;
    });
    if (invalid) {
      // The old results are no longer on screen, so they must not export
      lastResult = null;
      updateExportButtons();
      showMessage(invalid.value.trim() === ""
        ? "Choose a field for each filter with a value."
        : `Unknown field: "${invalid.value.trim()}". Choose one from the list.`, true);
      invalid.focus();
      return;
    }

    const limit = readLimit();
    limitInput.value = limit;
    const params = new URLSearchParams();
    // An empty "or" row still starts a new group, as its dashed line shows,
    // so its "or" passes to the next filter that is sent
    let startsGroup = false;
    for (const filter of filters) {
      if (filter.value === "") {
        startsGroup = startsGroup || filter.logic === "or";
        continue;
      }
      params.append("field", filter.field);
      params.append("search", filter.search);
      params.append("value", filter.value);
      params.append("logic", startsGroup ? "or" : filter.logic);
      startsGroup = false;
    }
    params.set("columns", (responsiveBox.checked ? allColumns : selectedColumns()).join(","));
    params.set("limit", limit);

    const request = ++latestRequest;
    window.showLoading?.("dq-search-button");
    fetch(`/dq_search?${params}`)
      .then(response => response.json())
      .then(data => {
        if (request !== latestRequest) return;
        lastResult = {
          columns: data.columns || [],
          rows: data.rows || [],
          more: Boolean(data.more),
          error: data.error || "",
        };
        renderResults();
      })
      .catch(() => {
        if (request !== latestRequest) return;
        lastResult = null;
        updateExportButtons();
        showMessage("Error fetching results.", true);
      })
      .finally(() => {
        if (request === latestRequest) window.hideLoading?.("dq-search-button");
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    openColumnsMenu(false);
    performQuery();
  });

  clearButton.addEventListener("click", function () {
    latestRequest++;
    window.hideLoading?.("dq-search-button");
    lastResult = null;
    setFilters([]);
    results.replaceChildren();
    updateExportButtons();
    filterList.querySelector(".dq-value").focus();
  });

  // Results

  // The selected fields that the last search fetched, and those it did not
  function shownColumns() {
    const selected = selectedColumns();
    return {
      shown: selected.filter(column => lastResult.columns.includes(column)),
      missing: selected.filter(column => !lastResult.columns.includes(column)),
    };
  }

  // Rows of the shown fields only, in their order
  function shownRows(shown) {
    const index = shown.map(column => lastResult.columns.indexOf(column));
    return lastResult.rows.map(row => index.map(i => row[i]));
  }

  function renderResults() {
    updateExportButtons();
    if (!lastResult) return;
    if (lastResult.error) {
      showMessage(lastResult.error, true);
      return;
    }

    const { shown, missing } = shownColumns();
    const count = document.createElement("p");
    count.className = "tt-count";
    const total = lastResult.rows.length;
    count.textContent = lastResult.more
      ? `Showing the first ${total} results. There are more: add filters to narrow them down.`
      : `${total} result${total === 1 ? "" : "s"}`;
    const parts = [count];

    if (missing.length) {
      const note = document.createElement("p");
      note.className = "message";
      note.textContent = `Search again to show ${missing.join(", ")}.`;
      parts.push(note);
    }

    if (total && shown.length) {
      const table = document.createElement("table");
      table.className = "dq-table";
      const headRow = table.createTHead().insertRow();
      for (const column of shown) {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = column;
        headRow.appendChild(th);
      }
      const body = table.createTBody();
      for (const row of shownRows(shown)) {
        const tr = body.insertRow();
        // Text only: some fields hold HTML, which is shown as it is stored
        for (const value of row) tr.insertCell().textContent = String(value);
      }
      // It scrolls, so keyboard users can focus it to scroll with the arrow keys
      const wrapper = document.createElement("div");
      wrapper.className = "dq-table-wrap";
      wrapper.tabIndex = 0;
      wrapper.setAttribute("role", "region");
      wrapper.setAttribute("aria-label", "results table");
      wrapper.appendChild(table);
      parts.push(wrapper);
    }
    results.replaceChildren(...parts);
  }

  // Export

  function updateExportButtons() {
    const empty = !lastResult || lastResult.error !== "" || lastResult.rows.length === 0 ||
      shownColumns().shown.length === 0;
    exportTsvButton.disabled = empty;
    exportJsonButton.disabled = empty;
  }

  function download(fileName, type, text) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  // Quoted like a spreadsheet's tab-separated file when a value holds a tab,
  // a line break or a quote
  function tsvCell(value) {
    const text = String(value);
    return /[\t\r\n"]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  exportTsvButton.addEventListener("click", function () {
    const { shown } = shownColumns();
    const lines = [shown, ...shownRows(shown)].map(row => row.map(tsvCell).join("\t"));
    download("dpd_query.tsv", "text/tab-separated-values;charset=utf-8", lines.join("\n") + "\n");
  });

  exportJsonButton.addEventListener("click", function () {
    const { shown } = shownColumns();
    const objects = shownRows(shown).map(row =>
      Object.fromEntries(shown.map((column, i) => [column, row[i]])));
    download("dpd_query.json", "application/json", JSON.stringify(objects, null, 2) + "\n");
  });

  // Presets

  function loadPresets() {
    try {
      const presets = JSON.parse(readStorage(PRESETS_KEY));
      return presets && typeof presets === "object" && !Array.isArray(presets) ? presets : {};
    } catch (e) {
      return {};
    }
  }

  function updatePresetSelect(selected = "") {
    const names = Object.keys(loadPresets()).sort((a, b) => a.localeCompare(b));
    presetSelect.replaceChildren(presetSelect.options[0]);
    for (const name of names) presetSelect.add(new Option(name, name));
    presetSelect.value = names.includes(selected) ? selected : "";
  }

  function applyPreset(preset) {
    const filters = Array.isArray(preset.filters) ? preset.filters : [];
    setFilters(filters.filter(filter => filter && typeof filter === "object").map(filter => ({
      logic: String(filter.logic ?? "and"),
      field: String(filter.field ?? ""),
      search: ["contains", "starts_with", "ends_with", "regex"].includes(filter.search)
        ? filter.search : "contains",
      value: String(filter.value ?? ""),
    })));
    setColumns(Array.isArray(preset.columns) ? preset.columns : []);
    limitInput.value = Number.isFinite(Number(preset.limit)) ? preset.limit : maxLimit;
    limitInput.value = readLimit();
    if (typeof preset.fetchAllFields === "boolean") {
      responsiveBox.checked = preset.fetchAllFields;
      writeStorage(RESPONSIVE_KEY, preset.fetchAllFields ? "true" : "false");
    }
    renderResults();
  }

  presetSelect.addEventListener("change", function () {
    const preset = loadPresets()[presetSelect.value];
    if (preset) applyPreset(preset);
  });

  presetName.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    e.preventDefault();
    document.getElementById("dq-preset-save").click();
  });

  document.getElementById("dq-preset-save").addEventListener("click", function () {
    const name = presetName.value.trim() || presetSelect.value;
    if (!name) {
      presetName.focus();
      return;
    }
    const presets = loadPresets();
    presets[name] = {
      filters: readFilters(),
      columns: selectedColumns(),
      limit: readLimit(),
      fetchAllFields: responsiveBox.checked,
    };
    if (!writeStorage(PRESETS_KEY, JSON.stringify(presets))) {
      // Keep the name, so the user can try again once storage is allowed
      showMessage("The preset was not saved: this browser does not allow saving.", true);
      return;
    }
    presetName.value = "";
    updatePresetSelect(name);
  });

  document.getElementById("dq-preset-delete").addEventListener("click", function () {
    const name = presetSelect.value;
    if (!name) return;
    const presets = loadPresets();
    delete presets[name];
    writeStorage(PRESETS_KEY, JSON.stringify(presets));
    updatePresetSelect();
  });

  // Start with one filter and the default fields
  setFilters([]);
  updateColumnsText();
  updatePresetSelect();
})();
