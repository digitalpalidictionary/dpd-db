let c = console.log

// elements

const titleClear = document.getElementById("title-clear")
const subTitle = document.getElementById("subtitle")
const searchBox1 = document.getElementById("search-box1")
const searchBox2 = document.getElementById("search-box2")
const searchForm = document.getElementById('search-form');
const footerText = document.getElementById("footer")

/////////// listeners

// trigger title clear - go home
titleClear.addEventListener('click', function() {
	window.location.href = '/';
});

// trigger search

searchBox1.addEventListener('keydown', function(event) {
	if (event.key === 'Enter') {
		searchForm.submit();
	}
});

searchBox2.addEventListener('keydown', function(event) {
	if (event.key === 'Enter') {
		searchForm.submit();
	}
});

// trigger search by click

document.addEventListener('DOMContentLoaded', function() {
	document.body.addEventListener('dblclick', function() {
	var selection = window.getSelection().toString().toLowerCase();
	searchBox1.value = selection.slice(0, -1);
	searchBox2.value = "";
	searchForm.submit()
	});
});

// show hide sidebar

document.getElementById("showSidebar").addEventListener("click", function() {
    var content = document.getElementById("sidebar");
    if (content.style.display === "none") {
        content.style.display = "block";
    } else {
        content.style.display = "none";
    }
});

// text to unicode


function uniCoder(textInput) {
	if (!textInput || textInput == '') return textInput
	
	textInput = textInput.replace(/aa/g, 'ā').replace(/ii/g, 'ī').replace(/uu/g, 'ū').replace(/\.t/g, 'ṭ').replace(/\.d/g, 'ḍ').replace(/\"n/g, 'ṅ').replace(/\'n/g, 'ṅ').replace(/\.n/g, 'ṇ').replace(/\.m/g, 'ṃ').replace(/\~n/g, 'ñ').replace(/\.l/g, 'ḷ').replace(/\.h/g, 'ḥ').toLowerCase()
	c(textInput)
	return textInput
}


// contextual help listeners

searchBox1.addEventListener("mouseenter", function() {
	hoverHelp("searchBox1")
})
searchBox1.addEventListener("mouseleave", function () {
	hoverHelp("default")
})
searchBox2.addEventListener("mouseenter", function () {
	hoverHelp("searchBox2")
})
searchBox2.addEventListener("mouseleave", function () {
	hoverHelp("default")
})


// contextual help

function hoverHelp(event) {
	if (event == "searchBox1") {
		footerText.innerHTML = "What is the defined Pāḷi term you are looking for?"
	}
	else if (event == "searchBox2") {
		footerText.innerHTML = "Use this box to search within results."
	}
	else if (event == "startsWithButton") {
		footerText.innerHTML = "Search for definitions starting with the term."
	}
	else {
		footerText.innerHTML = '<a href="https://digitalpalidictionary.github.io/" target="_blank">Built for DPD'
	}
}

