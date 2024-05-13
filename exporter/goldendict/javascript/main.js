
//// listen for button clicks

document.addEventListener("click", function(event) {
    var target = event.target;
    const classNames = ["button", "root_button"]
    if (classNames.some(className => target.classList.contains(className))) {
        button_click(target);
        event.preventDefault();
    }
});

//// handle button clicks

function button_click(el) {
    const target_id = el.getAttribute("data-target");
    var target = document.getElementById(target_id);
    if (target) {

        if (target.textContent.includes("loading...")) {
            loadData()
        };

        target.classList.toggle("hidden");
        if (el.classList.contains("close")) {
            var target_control = document.querySelector('a.button[data-target="' + target_id + '"]');
            if (target_control) {
                target_control.classList.toggle("active");
            }
        } else {
            el.classList.toggle("active");
        }
    }
}

//// get the data to load into buttons

document.addEventListener('DOMContentLoaded', function() {
    loadData()
});

function loadData() {
    var metaTags = document.querySelectorAll("meta[data_key]");
    var metaArray = Array.from(metaTags);
    metaArray.forEach(tag => {
        var dataKey = tag.getAttribute("data_key");
        var data = window[dataKey];
        if (dataKey.startsWith("data_")) {
            loadButtonContent(data)
        } else if (dataKey.startsWith("rootdata_")) {
            loadRootButtonContent(data)
        }
    });
};

//// load json data into buttons 

function loadButtonContent(data) {
    
    //// feedback

    const feedbackHTML = makeFeedback(data);
    const feedbackElement = document.getElementById(`feedback_${data.lemma}`)
    feedbackElement.innerHTML = feedbackHTML

    //// family compounds

    if (
        data.family_compounds
        && data.family_compounds.length > 0
        && typeof family_compound_json !== "undefined"
    ) {
        const familyCompoundHtml = makeFamilyCompoundHtml(data)
        const familyCompoundElement = document.getElementById(`family_compound_${data.lemma}`)
        familyCompoundElement.innerHTML = familyCompoundHtml
    };

    //// family root

    if (data.family_root != "") {
        const fr = family_root_json[data.family_root];
        const familyRootHtml = makeFamilyRootHtml(data, fr);
        const familyRootElement = document.getElementById(`family_root_${data.lemma}`);
        familyRootElement.innerHTML = familyRootHtml;
    };

    //// family idioms

    if (
        data.family_idioms
        && data.family_idioms.length > 0
        && typeof family_idiom_json !== "undefined"
    ) {
        const familyIdiomHtml = makeFamilyIdioms(data)
        const familyIdiomElement = document.getElementById(`family_idiom_${data.lemma}`)
        familyIdiomElement.innerHTML = familyIdiomHtml
    };

    //// family sets

    if (
        data.family_sets 
        && data.family_sets.length > 0
        && typeof family_set_json !== "undefined"
    ) {
        const familySetHtml = makeFamilySets(data)
        const familySetElement = document.getElementById(`family_set_${data.lemma}`)
        familySetElement.innerHTML = familySetHtml
    };

    //// family word

    if (
        data.family_word
        && family_word_json[data.family_word]
    ) {
        const familyWordHtml = makeFamilyWordHtml(data);
        const familyWordElement = document.getElementById(`family_word_${data.lemma}`)
        familyWordElement.innerHTML = familyWordHtml
    };
};

//// load root dictionary button content

function loadRootButtonContent(data) {
    const familyRootDivs = document.querySelectorAll('div[id^="family_root_"]');
    var familyRootArray = Array.from(familyRootDivs);
    familyRootArray.forEach(item => {
        const key_id = item.id
        const key_clean = item.id.replace("family_root_", "").replace(/_/g, " ")
        const fr = family_root_json[key_clean]
        const familyRootHtml = makeFamilyRootHtml(data, fr, "root");
        const familyRootElement = document.getElementById(key_id)
        familyRootElement.innerHTML = familyRootHtml
    })
};
