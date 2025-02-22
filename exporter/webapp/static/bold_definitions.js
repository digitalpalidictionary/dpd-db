// elements

const bdTitleClear = document.getElementById("bd-title-clear");
const bdSearchBox1 = document.getElementById("bd-search-box-1");
const bdSearchBox2 = document.getElementById("bd-search-box-2");
const bdSearchForm = document.getElementById('bd-search-form');
const bdSearchButton = document.getElementById("bd-search-button");
const bdResults = document.getElementById("bd-results");
const bdFooterText = document.getElementById("bd-footer");
const bdSearchOptions = document.getElementsByName("option");

/////////// listeners

// trigger title clear - go home
bdTitleClear.addEventListener('click', function() {
	window.location.href = '/';
});

// trigger search

bdSearchBox1.addEventListener('keydown', function(event) {
	if (event.key === 'Enter') {
		handleBdFormSubmit(event);
	}
});

bdSearchBox2.addEventListener('keydown', function(event) {
	if (event.key === 'Enter') {
		handleBdFormSubmit(event);
	}
});

bdSearchButton.addEventListener('click', handleBdFormSubmit);

// trigger search by click

document.addEventListener('DOMContentLoaded', function() {
	document.body.addEventListener('dblclick', function() {
	var selection = window.getSelection().toString().toLowerCase();
	bdSearchBox1.value = selection.slice(0, -1);
	bdSearchBox2.value = "";
	handleBdFormSubmit();
	});
});

// text to unicode

function uniCoder(textInput) {
	if (!textInput || textInput == '') return textInput
	
	textInput = textInput.replace(/aa/g, 'ā').replace(/ii/g, 'ī').replace(/uu/g, 'ū').replace(/\.t/g, 'ṭ').replace(/\.d/g, 'ḍ').replace(/\"n/g, 'ṅ').replace(/\'n/g, 'ṅ').replace(/\.n/g, 'ṇ').replace(/\.m/g, 'ṃ').replace(/\~n/g, 'ñ').replace(/\.l/g, 'ḷ').replace(/\.h/g, 'ḥ').toLowerCase()
	c(textInput)
	return textInput
}

// contextual help listeners

// bdSearchBox1.addEventListener("mouseenter", function() {
// 	hoverHelp("searchBox1")
// })
// bdSearchBox1.addEventListener("mouseleave", function () {
// 	hoverHelp("default")
// })
// bdSearchBox2.addEventListener("mouseenter", function () {
// 	hoverHelp("searchBox2")
// })
// bdSearchBox2.addEventListener("mouseleave", function () {
// 	hoverHelp("default")
// })

// contextual help

// function hoverHelp(event) {
// 	if (event == "searchBox1") {
// 		footerText.innerHTML = "What is the defined Pāḷi term you are looking for?"
// 	}
// 	else if (event == "searchBox2") {
// 		footerText.innerHTML = "Use this box to search within results."
// 	}
// 	else if (event == "startsWithButton") {
// 		footerText.innerHTML = "Search for definitions starting with the term."
// 	}
// 	else {
// 		footerText.innerHTML = '<a href="https://digitalpalidictionary.github.io/" target="_blank">Built for DPD'
// 	}
// }

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
    if (searchQuery1.trim() !== "" || searchQuery2.trim() !== "") {
        try {
            const response = await fetch(`/bd_html?search_1=${encodeURIComponent(searchQuery1)}&search_2=${encodeURIComponent(searchQuery2)}&option=${encodeURIComponent(selectedOption)}`);
            const data = await response.text();
            // Process the response data and update the DOM as needed
            bdResults.innerHTML = data;
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }
}

