function openTab(evt, tabName) {
    var i, tabcontent, tablinks;

    // Hide all tab content
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
        tabcontent[i].classList.remove("active");
    }

    // Remove the active class from all tab links
    tablinks = document.getElementsByClassName("tab-link");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "flex"; // Ensure flex display for scrollable content
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.className += " active";

    // Update URL based on tab
    if (tabName === 'dpd-tab') {
        const searchBox = document.getElementById("search-box");
        const searchQuery = searchBox.value;
        const url = `/?q=${encodeURIComponent(searchQuery)}`;
        history.pushState({ q: searchQuery }, "", url);
    } else if (tabName === 'bold-def-tab') {
        const searchBox1 = document.getElementById("bd-search-box-1");
        const searchBox2 = document.getElementById("bd-search-box-2");
        const searchOption = document.querySelector('input[name="option"]:checked').value;
        const searchQuery1 = searchBox1.value;
        const searchQuery2 = searchBox2.value;
        const url = `/bd?search_1=${encodeURIComponent(searchQuery1)}&search_2=${encodeURIComponent(searchQuery2)}&option=${searchOption}`;
        history.pushState({ search_1: searchQuery1, search_2: searchQuery2, option: searchOption }, "", url);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var tabcontent = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabcontent.length; i++) {
        if (!tabcontent[i].classList.contains("active")) {
            tabcontent[i].style.display = "none";
        }
    }
});
