document.addEventListener('DOMContentLoaded', function() {
    const table = document.querySelector('table.grammar_dict');
    const tbody = table.querySelector('tbody');
    const headers = table.querySelectorAll('th');

    headers.forEach(header => {
        header.addEventListener('click', (event) => {
            const order = header.dataset.order === 'asc' ? 'desc' : 'asc';
            const colIndex = header.cellIndex;
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const aValue = a.cells[colIndex].textContent.toLowerCase();
                const bValue = b.cells[colIndex].textContent.toLowerCase();
                return aValue > bValue ? 1 : -1;
            });

            if (order === 'desc') {
                rows.reverse();
            }

            tbody.innerHTML = '';
            rows.forEach(row => {
                tbody.appendChild(row);
            });

            headers.forEach(header => {
                header.dataset.order = '';
            });

            header.dataset.order = order;

            // Stop further event propagation
            event.stopPropagation();
            event.preventDefault();
            return false;
        });
    });
});