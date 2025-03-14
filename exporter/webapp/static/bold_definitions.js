// elements

const bdTitleClear = document.getElementById("bd-title-clear");
const bdSearchBox1 = document.getElementById("bd-search-box-1");
const bdSearchBox2 = document.getElementById("bd-search-box-2");
const bdSearchForm = document.getElementById('bd-search-form');
const bdSearchButton = document.getElementById("bd-search-button");
const bdResults = document.getElementById("bd-results");
const bdFooterText = document.querySelector("#bold-def-tab .footer-pane");
const bdSearchOptions = document.getElementsByName("option");
const bdStartsWithButton = document.getElementById("option1");

/*
function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split('&');

    for (var i = 0; i < vars.length; i++) {
      var pair = vars[i].split('=');

      if (pair[0] === variable) {
        return decodeURIComponent(pair[1].replace(/\+/g, '%20'));
      }
    }
}
*/

/*
function applyUrlQuery() {
    const search1 = getQueryVariable('search_1');
    const search2 = getQueryVariable('search_2');
    const option = getQueryVariable('option');

    if (search1) {
        bdSearchBox1.value = search1;
    }
    if (search2) {
        bdSearchBox2.value = search2;
    }
    if (option) {
        for (const bdSearchOption of bdSearchOptions) {
            if (bdSearchOption.value === option) {
                bdSearchOption.checked = true;
                break;
            }
        }
    }
}
*/

const bdRegexButton = document.getElementById("option2");
const bdFuzzyButton = document.getElementById("option3");

/////////// listeners

const bdClearButton = document.querySelector(".bd-search-option-clear");

function clearBdResults() {
    bdResults.innerHTML = '';
    bdSearchBox1.value = '';
    bdSearchBox2.value = '';
    history.pushState({}, "", "/");
}

bdClearButton.addEventListener('click', clearBdResults);

// trigger search

bdSearchBox1.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        handleBdFormSubmit(event);
    }
});

bdSearchBox2.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        handleBdFormSubmit(event);
    }
});

bdSearchButton.addEventListener('click', handleBdFormSubmit);

// trigger search by click

document.addEventListener('DOMContentLoaded', function () {
    // applyUrlQuery();
    // handleBdFormSubmit()

    document.body.addEventListener('dblclick', function () {
        var selection = window.getSelection().toString().toLowerCase();
        bdSearchBox1.value = selection.slice(0, -1);
        bdSearchBox2.value = "";
        handleBdFormSubmit();
    });
});

// text to unicode

bdSearchBox1.addEventListener("input", function () {
    let textInput = bdSearchBox1.value;
    let convertedText = uniCoder(textInput);
    bdSearchBox1.value = convertedText;
});

bdSearchBox2.addEventListener("input", function () {
    let textInput = bdSearchBox2.value;
    let convertedText = uniCoder(textInput);
    bdSearchBox2.value = convertedText;
});

function uniCoder(textInput) {
    if (!textInput || textInput == "") return textInput
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
        .replace(/\.h/g, "ḥ")
};

// contextual help listeners

bdSearchBox1.addEventListener("mouseenter", function () {
    hoverHelp("searchBox1")
})
bdSearchBox1.addEventListener("mouseleave", function () {
    hoverHelp("default")
})
bdSearchBox2.addEventListener("mouseenter", function () {
    hoverHelp("searchBox2")
})
bdSearchBox2.addEventListener("mouseleave", function () {
    hoverHelp("default")
})

document.querySelector('label[for="option1"]').addEventListener("mouseenter", function () {
    hoverHelp("startsWithButton")
})
document.querySelector('label[for="option1"]').addEventListener("mouseleave", function () {
    hoverHelp("default")
})

document.querySelector('label[for="option2"]').addEventListener("mouseenter", function () {
    hoverHelp("regexButton")
})
document.querySelector('label[for="option2"]').addEventListener("mouseleave", function () {
    hoverHelp("default")
})

document.querySelector('label[for="option3"]').addEventListener("mouseenter", function () {
    hoverHelp("fuzzyButton")
})
document.querySelector('label[for="option3"]').addEventListener("mouseleave", function () {
    hoverHelp("default")
})

bdClearButton.addEventListener("mouseenter", function () {
    hoverHelp("clearButton")
})
bdClearButton.addEventListener("mouseleave", function () {
    hoverHelp("default")
})

// contextual help

function hoverHelp(event) {
    if (event == "searchBox1") {
        bdFooterText.innerHTML = "What is the defined Pāḷi term you are looking for?"
    }
    else if (event == "searchBox2") {
        bdFooterText.innerHTML = "Use this box to search within results."
    }
    else if (event == "startsWithButton") {
        bdFooterText.innerHTML = "Search for definitions <b>starting</b> with the term."
    }
    else if (event == "regexButton") {
        bdFooterText.innerHTML = "This is the <b>normal</b> mode. You can also use <b>regular expressions</b> for very precise searches."
    }
    else if (event == "fuzzyButton") {
        bdFooterText.innerHTML = "<b>Fuzzy</b> search ignores all diacritics and double consonants. It's useful if you don't know the exact spelling."
    }
    else if (event == "clearButton") {
        bdFooterText.innerHTML = "Start again with a calm and <b>clear</b> interface."
    }
    else {
        bdFooterText.innerHTML = 'For detailed information on this feature, please visit the <a href="https://digitalpalidictionary.github.io/dpdict_bd.html" target="_blank">DPD docs website.'
    }
}

async function handleBdFormSubmit(event) {
    if (event) {
        event.preventDefault();
    }
    const searchQuery1 = bdSearchBox1.value;
    const searchQuery2 = bdSearchBox2.value;
    let selectedOption = "regex"; // Default option
    for (const option of bdSearchOptions) {
        if (option.checked) {
            selectedOption = option.value;
            break;
        }
    }
    const searchUrl = '/bd_search';
    if (searchQuery1.trim() !== "" || searchQuery2.trim() !== "") {
        try {
            const response = await fetch(`${searchUrl}?q1=${encodeURIComponent(searchQuery1)}&q2=${encodeURIComponent(searchQuery2)}&option=${selectedOption}`);
            const data = await response.text();
            // Process the response data and update the DOM as needed
            bdResults.innerHTML = data;
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }
    // history.pushState({ search_1: searchQuery1, search_2: searchQuery2, option: selectedOption }, "", url);
}
