let c = console.log

function button_click(el) {
    const target_id=el.getAttribute('data-target');

    target = document.getElementById(target_id);
    target.classList.toggle('hidden');

    if (el.classList.contains('close')) {
        // close button should toggle active highlight on the button which controls the same target
        target_control = document.querySelector('a.button[data-target="'+target_id+'"]');
        target_control.classList.toggle('active');
    } else {
        // close button doesn't need active highlight
        el.classList.toggle('active');
    }
    // prevent default
    return false;
}



// elements

const titleClear = document.getElementById("title-clear")
const subTitle = document.getElementById("subtitle")
const searchBox = document.getElementById("search-box")
const searchForm = document.getElementById('search-form');
const footerText = document.getElementById("footer")
const mainPane = document.getElementById('main-pane');

/////////// listeners

// trigger title clear - go home
titleClear.addEventListener('click', function() {
	window.location.href = '/';
});

// trigger search

searchBox.addEventListener('keydown', function(event) {
	if (event.key === 'Enter') {
		searchForm.submit();
	}
});


// trigger search by click

mainPane.addEventListener("dblclick", function() {
    var selection = window.getSelection().toString();
	c(selection)
    searchBox.value = selection;
    searchForm.submit();
});


// text to unicode


function uniCoder(textInput) {
	if (!textInput || textInput == '') return textInput
	
	textInput = textInput.replace(/aa/g, 'ā').replace(/ii/g, 'ī').replace(/uu/g, 'ū').replace(/\.t/g, 'ṭ').replace(/\.d/g, 'ḍ').replace(/\"n/g, 'ṅ').replace(/\'n/g, 'ṅ').replace(/\.n/g, 'ṇ').replace(/\.m/g, 'ṃ').replace(/\~n/g, 'ñ').replace(/\.l/g, 'ḷ').replace(/\.h/g, 'ḥ').toLowerCase()
	c(textInput)
	return textInput
}


