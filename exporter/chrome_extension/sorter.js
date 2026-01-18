// Robust Sorter for Chrome Extension
(function() {
    if (window.initSorterInitialized) return;
    window.initSorterInitialized = true;

    window.initSorter = function() {
        const tables = document.querySelectorAll('table.grammar_dict');
        tables.forEach(table => {
            if (!table.dataset.sorterActive) {
                initializeTable(table);
            }
        });
    };

    function initializeTable(table) {
        const tbody = table.querySelector('tbody');
        const headers = table.querySelectorAll('th');
        if (!tbody || !headers.length) return;

        table.dataset.sorterActive = "true";
        const originalRows = Array.from(tbody.querySelectorAll('tr'));

        const letterToNumber = {
            "√": "00", "a": "01", "ā": "02", "i": "03", "ī": "04", "u": "05", "ū": "06", "e": "07", "o": "08",
            "k": "09", "kh": "10", "g": "11", "gh": "12", "ṅ": "13", "c": "14", "ch": "15", "j": "16", "jh": "17", "ñ": "18",
            "ṭ": "19", "ṭh": "20", "ḍ": "21", "ḍh": "22", "ṇ": "23", "t": "24", "th": "25", "d": "26", "dh": "27", "n": "28",
            "p": "29", "ph": "30", "b": "31", "bh": "32", "m": "33", "y": "34", "r": "35", "l": "36", "v": "37", "s": "38",
            "h": "39", "ḷ": "40", "ṃ": "41"
        };

        const pattern = new RegExp("kh|gh|ch|jh|ṭh|ḍh|th|ph|" + Object.keys(letterToNumber).sort((a, b) => b.length - a.length).join("|"), "g");

        function paliSortKey(word) {
            if (!word) return "";
            return word.toLowerCase().replace(pattern, (match) => letterToNumber[match] || match);
        }

        function updateArrows(activeHeader, order) {
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
        }

        headers.forEach(header => {
            if (header.id === 'col5') return;
            header.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();

                let order = header.dataset.order || '';
                let nextOrder = (order === '') ? 'asc' : (order === 'asc' ? 'desc' : '');

                let rowsToSort = (nextOrder === '') ? [...originalRows] : Array.from(tbody.querySelectorAll('tr'));
                
                if (nextOrder !== '') {
                    const colIndex = header.cellIndex;
                    const isPaliCol = (header.id === 'col1' || header.id === 'col6');
                    rowsToSort.sort((a, b) => {
                        let aVal = a.cells[colIndex] ? a.cells[colIndex].textContent.trim() : "";
                        let bVal = b.cells[colIndex] ? b.cells[colIndex].textContent.trim() : "";
                        if (isPaliCol) { aVal = paliSortKey(aVal); bVal = paliSortKey(bVal); }
                        return nextOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    });
                }

                tbody.innerHTML = '';
                rowsToSort.forEach(row => tbody.appendChild(row));
                headers.forEach(h => h.dataset.order = '');
                header.dataset.order = nextOrder;
                updateArrows(header, nextOrder);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.initSorter);
    } else {
        window.initSorter();
    }

    // Dynamic listener for clicks - identical to webapp
    document.addEventListener('click', function() {
        setTimeout(window.initSorter, 100);
    }, true);

})();