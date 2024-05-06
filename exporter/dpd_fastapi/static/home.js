const c = console.log

//// elements

const docBody = document.body
const titleClear = document.getElementById("title-clear")
const mainPane = document.getElementById("main-pane");
const dpdPane = document.getElementById("dpd-pane");
const summaryResults = document.getElementById("summary-results");
const dpdResults = document.getElementById("dpd-results");
const historyPane = document.getElementById("history-pane");
const historyListPane = document.getElementById("history-list-pane");
const subTitle = document.getElementById("subtitle")
const searchBox = document.getElementById("search-box")
const entryBoxClass = document.getElementsByClassName("search-box")
const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const footerText = document.getElementById("footer");

const themeToggle = document.getElementById("theme-toggle");
const sansSerifToggle = document.getElementById("sans-serif-toggle");
const niggahitaToggle = document.getElementById("niggahita-toggle");
const grammarToggle = document.getElementById("grammar-toggle");
const exampleToggle = document.getElementById("example-toggle");
const summaryToggle = document.getElementById("summary-toggle");


//// load state

function loadToggleState(id) {
    var savedState = localStorage.getItem(id);
    if (savedState !== null) {
        document.getElementById(id).checked = JSON.parse(savedState);
    }
}

//// Page load

const startMessage = `
<p class="message">Search for Pāḷi or English words above using Unicode or Velthuis characters.</p>
<p class="message">Double click on any word to search for it.</p>
<p class="message">Adjust the settings to your preference.</p>
<p class="message">Hover over any element to get help.</p>
`

document.addEventListener("DOMContentLoaded", function() {
    applySavedTheme()
    populateHistoryBody()
    loadToggleState("theme-toggle");
    loadToggleState("sans-serif-toggle");
    loadToggleState("niggahita-toggle");
    loadToggleState("grammar-toggle");
    loadToggleState("example-toggle");
    loadToggleState("summary-toggle");
    toggleClearHistoryButton()
    swopSansSerif()
    if (dpdResults.innerHTML.trim() == "") {
        dpdResults.innerHTML = startMessage
    } 
});

//// listeners

//// trigger title clear - go home

titleClear.addEventListener("dblclick", function() {
	dpdPane.innerHTML = ""; 
});

//// double click to search 

dpdPane.addEventListener("dblclick", processSelection);
historyPane.addEventListener("dblclick", processSelection);

function processSelection() {
    var selection = window.getSelection().toString();
    searchBox.value = selection;
    if (selection.trim() !== "") {
        handleFormSubmit();
    }
};

//// enter or click button to search 

searchForm.addEventListener("submit", handleFormSubmit);
searchButton.addEventListener("submit", handleFormSubmit);

//// submit search

async function handleFormSubmit(event) {
    if (event) {
        event.preventDefault();
    }
    const searchQuery = searchBox.value;

    if (searchQuery.trim() !== "") {
        try {
            addToHistory(searchQuery)
            const response = await fetch(`/search_json?search=${encodeURIComponent(searchQuery)}`);
            const data = await response.json(); 

            //// add the summary_html
            if (data.summary_html.trim() != "") {
                summaryResults.innerHTML = "<h3>Summary</h3>"
                summaryResults.innerHTML += data.summary_html; 
                summaryResults.innerHTML += "<hr>"
            } else {
                summaryResults.innerHTML = ""
            }
            showHideSummery()

            
            //// add dpd_html
            const dpdDiv = document.createElement("div");
            dpdDiv.innerHTML += data.dpd_html;
            
            //// niggahita toggle
            if (niggahitaToggle.checked) {
                niggahitaUp(dpdDiv)
            }
    
            //// grammar button toggle
            if (grammarToggle.checked) {
                const grammarButtons = dpdDiv.querySelectorAll('[name="grammar-button"]');
                const grammarDivs = dpdDiv.querySelectorAll('[name="grammar-div"]');
                grammarButtons.forEach(button => {
                    button.classList.add("active");
                });
                grammarDivs.forEach(div => {
                    div.classList.remove("hidden");
                });
            };
    
            //// example button toggle
            if (exampleToggle.checked) {
                const exampleButtons = dpdDiv.querySelectorAll('[name="example-button"]');
                const exampleDivs = dpdDiv.querySelectorAll('[name="example-div"]');
                exampleButtons.forEach(button => {
                    button.classList.add("active");
                });
                exampleDivs.forEach(div => {
                    div.classList.remove("hidden");
                });
            };
    
            dpdResults.innerHTML = dpdDiv.innerHTML;
            
            populateHistoryBody();
            dpdPane.focus();
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
            dpdPane.scrollTo({
                top: 0,
                behavior: "smooth"
            });
            
            
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }
}

//// populate history

function addToHistory(word) {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    const index = historyList.indexOf(word);
    if (index !== -1) {
        historyList.splice(index, 1);
    }
    historyList.unshift(word);
    if (historyList.length > 50) {
        historyList.pop();
    }
    localStorage.setItem("history-list", JSON.stringify(historyList));
    toggleClearHistoryButton()
}

function populateHistoryBody() {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    let listElement = document.createElement("ul");
    listElement.id = "history-list";

    historyList.forEach(item => {
        let listItem = document.createElement("li");
        listItem.textContent = item;
        listElement.appendChild(listItem);
    });

    historyListPane.innerHTML = ""; 
    historyListPane.appendChild(listElement);
}

document.getElementById("clear-history-button").addEventListener("click", function() {
    localStorage.removeItem("history-list");
    document.getElementById("history-list").innerHTML = "";
    toggleClearHistoryButton()
});

function toggleClearHistoryButton() {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    let clearHistoryButton = document.getElementById("clear-history-button");

    if (historyList.length === 0) {
        clearHistoryButton.style.display = "none";
    } else {
        clearHistoryButton.style.display = "inline-block";
    }
}


//// save settings on toggle

themeToggle.addEventListener("change", saveToggleState);
sansSerifToggle.addEventListener("change", saveToggleState);
niggahitaToggle.addEventListener("change", saveToggleState);
grammarToggle.addEventListener("change", saveToggleState);
exampleToggle.addEventListener("change", saveToggleState);
summaryToggle.addEventListener("change", saveToggleState);

function saveToggleState(event) {
    localStorage.setItem(event.target.id, event.target.checked);
}

//// theme

function toggleTheme(event) {
    document.body.classList.toggle("dark-mode", event.target.checked);
    localStorage.setItem("theme", event.target.checked ? "dark" : "light");
}

//// Event listener for theme toggle
themeToggle.addEventListener("change", toggleTheme);

//// Function to apply the saved theme state
function applySavedTheme() {
    var savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
        document.body.classList.remove("dark-mode", "light-mode"); // Remove both classes
        document.body.classList.add(savedTheme + "-mode"); // Add the saved theme class
        themeToggle.checked = savedTheme === "dark"; // Sync toggle state
    }
}

//// toggle sans / serif

sansSerifToggle.addEventListener("change", function() {
    swopSansSerif()
});

function swopSansSerif() {
    const serifFonts = '"Noto Serif", "Dejavu Serif", "Garamond", "Georgia", "serif"';
    const sansFonts = '"Roboto", "Dejavu Sans", "Noto Sans", "Helvetica", "Verdana", "sans-serif"';
    if (sansSerifToggle.checked) {
        document.body.style.fontFamily = serifFonts;
        searchBox.style.fontFamily = serifFonts
        searchButton.style.fontFamily = serifFonts
    } else {
        document.body.style.fontFamily = sansFonts;
        searchBox.style.fontFamily = sansFonts
        searchButton.style.fontFamily = sansFonts
    }

} 


//// niggahita

function niggahitaUp(element) {
    element.innerHTML = element.innerHTML.replace(/ṃ/g, "ṁ");
}

function niggahitaDown(element) {
    element.innerHTML = element.innerHTML.replace(/ṁ/g, "ṃ");
}

niggahitaToggle.addEventListener("change", function() {
    if (this.checked) {
        niggahitaUp(dpdPane);
        niggahitaUp(historyPane);
    } else {
        niggahitaDown(dpdPane);
        niggahitaDown(historyPane);

    }
});

//// grammar button closed / open

grammarToggle.addEventListener("change", function() {
    const grammarButtons = document.getElementsByName("grammar-button");
    const grammarDivs = document.getElementsByName("grammar-div");
    if (this.checked) {
        grammarButtons.forEach(button => {
            button.classList.add("active");
        });
        grammarDivs.forEach(div => {
            div.classList.remove("hidden");
        });
    } else {
        grammarButtons.forEach(button => {
            button.classList.remove("active");
        });
        grammarDivs.forEach(div => {
            div.classList.add("hidden");
        });
    }
});

//// examples button toggle
exampleToggle.addEventListener("change", function() {
    const exampleButtons = document.getElementsByName("example-button");
    const exampleDivs = document.getElementsByName("example-div");
    if (this.checked) {
        exampleButtons.forEach(button => {
            button.classList.add("active");
        });
        exampleDivs.forEach(div => {
            div.classList.remove("hidden");
        });
    } else {
        exampleButtons.forEach(button => {
            button.classList.remove("active");
        });
        exampleDivs.forEach(div => {
            div.classList.add("hidden");
        });
    }
});

//// summary 

summaryToggle.addEventListener("change", function() {
    showHideSummery()
});

function showHideSummery() {
    if (summaryToggle.checked) {
        summaryResults.style.display = "block";
    } else {
        summaryResults.style.display = "none";
    }
}

//// text to unicode

searchBox.addEventListener("input", function() {
    let textInput = searchBox.value;
    let convertedText = uniCoder(textInput);
    searchBox.value = convertedText;
});

function uniCoder(textInput) {
	if (!textInput || textInput == "") return textInput
	return textInput
        .replace(/aa/g, "ā")
        .replace(/ii/g, "ī")
        .replace(/uu/g, "ū")
        .replace(/\.t/g, "ṭ")
        .replace(/\.d/g, "ḍ")
        .replace(/\"n/g, "ṅ")
        .replace(/\"n/g, "ṅ")
        .replace(/\.n/g, "ṇ")
        .replace(/\.m/g, "ṃ")
        .replace(/\~n/g, "ñ")
        .replace(/\.l/g, "ḷ")
        .replace(/\.h/g, "ḥ")
        .toLowerCase()
};