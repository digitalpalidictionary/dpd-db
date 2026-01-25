export function initSorter(root: HTMLElement | Document = document): void {
  const tables = root.querySelectorAll('table.grammar_dict:not(.sorter-initialized)');
  tables.forEach((table) => {
    initializeTable(table as HTMLTableElement);
  });
}

function initializeTable(table: HTMLTableElement): void {
  const tbody = table.querySelector('tbody');
  const headers = table.querySelectorAll('th');
  if (!tbody || !headers.length) return;

  table.classList.add('sorter-initialized');

  // Store original order for Reset state
  const originalRows = Array.from(tbody.querySelectorAll('tr'));

  const letterToNumber: { [key: string]: string } = {
    "√": "00", "a": "01", "ā": "02", "i": "03", "ī": "04", "u": "05", "ū": "06", "e": "07", "o": "08",
    "k": "09", "kh": "10", "g": "11", "gh": "12", "ṅ": "13", "c": "14", "ch": "15", "j": "16", "jh": "17", "ñ": "18",
    "ṭ": "19", "ṭh": "20", "ḍ": "21", "ḍh": "22", "ṇ": "23", "t": "24", "th": "25", "d": "26", "dh": "27", "n": "28",
    "p": "29", "ph": "30", "b": "31", "bh": "32", "m": "33", "y": "34", "r": "35", "l": "36", "v": "37", "s": "38",
    "h": "39", "ḷ": "40", "ṃ": "41"
  };

  const pattern = new RegExp("kh|gh|ch|jh|ṭh|ḍh|th|ph|" + Object.keys(letterToNumber).sort((a, b) => b.length - a.length).join("|"), "g");

  function paliSortKey(word: string): string {
    if (!word) return "";
    return word.toLowerCase().replace(pattern, (match) => {
      return letterToNumber[match] || match;
    });
  }

  function updateArrows(activeHeader: HTMLElement, order: string): void {
    headers.forEach(h => {
      if (h.id === 'col5') return;
      let text = h.textContent?.replace(/[⇅▲▼]/g, '').trim() || '';
      if (h === activeHeader) {
        if (order === 'asc') text += ' ▲';
        else if (order === 'desc') text += ' ▼';
        else text += ' ⇅';
      } else {
        text += ' ⇅';
      }
      h.textContent = text;
    });
  }

  headers.forEach(header => {
    if (header.id === 'col5') return;

    header.addEventListener('click', (event: Event) => {
      let order = header.dataset.order || '';
      let nextOrder = '';

      if (order === '') nextOrder = 'asc';
      else if (order === 'asc') nextOrder = 'desc';
      else nextOrder = '';

      let rowsToSort: HTMLTableRowElement[] = [];
      if (nextOrder === '') {
        rowsToSort = [...originalRows];
      } else {
        rowsToSort = Array.from(tbody!.querySelectorAll('tr'));
        const colIndex = (header as HTMLTableCellElement).cellIndex;
        const isPaliCol = (header.id === 'col1' || header.id === 'col6');

        rowsToSort.sort((a, b) => {
          let aCell = a.cells[colIndex];
          let bCell = b.cells[colIndex];
          let aVal = aCell ? aCell.textContent?.trim() || "" : "";
          let bVal = bCell ? bCell.textContent?.trim() || "" : "";

          if (isPaliCol) {
            aVal = paliSortKey(aVal);
            bVal = paliSortKey(bVal);
          }

          let cmp = aVal.localeCompare(bVal);
          return nextOrder === 'asc' ? cmp : -cmp;
        });
      }

      tbody!.innerHTML = '';
      rowsToSort.forEach(row => tbody!.appendChild(row));

      headers.forEach(h => h.dataset.order = '');
      header.dataset.order = nextOrder;
      updateArrows(header, nextOrder);
      event.stopPropagation();
    });
  });
}

// Export for legacy
if (typeof window !== 'undefined') {
  (window as any).initSorter = initSorter;
}
