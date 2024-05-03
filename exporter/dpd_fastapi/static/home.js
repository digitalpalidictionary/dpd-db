// document.getElementById('theme-toggle').addEventListener('change', function() {
//     var element = document.body;
//     element.classList.toggle("dark-mode");
//     // Save the current theme state
//     localStorage.setItem('theme', element.classList.contains('dark-mode') ? 'dark' : 'light');
// });

// // Function to apply the saved theme state
// function applySavedTheme() {
//     var savedTheme = localStorage.getItem('theme');
//     if (savedTheme) {
//         document.body.classList.remove('dark-mode', 'light-mode'); // Remove both classes
//         document.body.classList.add(savedTheme + '-mode'); // Add the saved theme class
//     }
// }

document.getElementById('theme-toggle').addEventListener('change', saveToggleState);
document.getElementById('sans-serif-toggle').addEventListener('change', saveToggleState);
document.getElementById('niggahita-toggle').addEventListener('change', saveToggleState);
document.getElementById('grammar-toggle').addEventListener('change', saveToggleState);
document.getElementById('example-toggle').addEventListener('change', saveToggleState);
document.getElementById('summary-toggle').addEventListener('change', saveToggleState);

function saveToggleState(event) {
    localStorage.setItem(event.target.id, event.target.checked);
}




