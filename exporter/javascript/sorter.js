function sortTable(colIndex) {
    const table = document.querySelector('.grammar_dict');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aValue = a.cells[colIndex].textContent.toLowerCase();
        const bValue = b.cells[colIndex].textContent.toLowerCase();
        return aValue > bValue ? 1 : -1;
    });

    tbody.innerHTML = '';
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}