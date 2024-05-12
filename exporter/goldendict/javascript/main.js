const c = console.log

// Add event listener to the document to handle button clicks
document.addEventListener('click', function(event) {
    var target = event.target;
    // Check if the clicked element has the class 'button'
    if (target.classList.contains('button')) {
        // Call button_click function passing the clicked element
        button_click(target);
        // Prevent default action (e.g., following the link)
        event.preventDefault();
    }
});


// Function to handle button clicks
function button_click(el) {
    const target_id = el.getAttribute('data-target');
    var target = document.getElementById(target_id);
    if (target) {
        target.classList.toggle('hidden');
        if (el.classList.contains('close')) {
            var target_control = document.querySelector('a.button[data-target="' + target_id + '"]');
            if (target_control) {
                target_control.classList.toggle('active');
            }
        } else {
            el.classList.toggle('active');
        }
    }
}


//// load the data

document.addEventListener('DOMContentLoaded', function() {
    var metaTags = document.querySelectorAll('meta[data_key]');
    var metaArray = Array.from(metaTags);
    metaArray.forEach(function(tag) {
        var dataKey = tag.getAttribute('data_key');
        var data = window[dataKey];
        loadButtonContent(data)
    });
});



function loadButtonContent(data) {

    //// family root

    if (data.family_root && family_root_json[data.family_root]) {
        const familyRootHtml = makeFamilyRootHtml(data);
        const familyRootElement = document.getElementById(`family_root_${data.lemma}`)
        familyRootElement.innerHTML = familyRootHtml
    };

    //// family compounds
    if (data.family_compounds && typeof family_compound_json !== "undefined") {
        const familyCompoundHtml = makeFamilyCompoundHtml(data)
        const familyCompoundElement = document.getElementById(`family_compound_${data.lemma}`)
        familyCompoundElement.innerHTML = familyCompoundHtml
    };

    //// family idioms

    if (data.family_idioms && typeof family_idiom_json !== "undefined") {
        const familyIdiomHtml = makeFamilyIdioms(data)
        const familyIdiomElement = document.getElementById(`family_idiom_${data.lemma}`)
        familyIdiomElement.innerHTML = familyIdiomHtml
    };

    //// family sets

    if (data.family_sets && typeof family_set_json !== "undefined") {
        const familySetHtml = makeFamilySets(data)
        const familySetElement = document.getElementById(`family_set_${data.lemma}`)
        familySetElement.innerHTML = familySetHtml
    };

    /// family word

    if (data.family_word && family_word_json[data.family_word]) {
        const familyWordHtml = makeFamilyWordHtml(data);
        const familyWordElement = document.getElementById(`family_word_${data.lemma}`)
        familyWordElement.innerHTML = familyWordHtml
    };

    //// feedback

    const feedbackHTML = makeFeedback(data);
    const feedbackElement = document.getElementById(`feedback_${data.lemma}`)
    feedbackElement.innerHTML = feedbackHTML
    
    /// what other repeated features can be templated?

};



