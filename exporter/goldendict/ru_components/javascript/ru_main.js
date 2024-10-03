
//// listen for button clicks

document.addEventListener("click", function(event) {
    var target = event.target;
    const classNames = ["button_ru", "root_button_ru"]
    if (classNames.some(className => target.classList.contains(className))) {
        button_click_ru(target);
        event.preventDefault();
    }
});

//// handle button clicks

function button_click_ru(el) {
    const target_id = el.getAttribute("data-target");
    var target = document.getElementById(target_id);

    if (target) {
        if (target.textContent.includes("loading...")) {
            loadData_ru()
        };

        target.classList.toggle("hidden");
        if (el.classList.contains("close_ru")) {
            var target_control = document.querySelector('a.button_ru[data-target="' + target_id + '"]');
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
    loadData_ru()
});

function loadData_ru() {
    var metaTags = document.querySelectorAll("meta[data_key]");
    var metaArray = Array.from(metaTags);
    metaArray.forEach(tag => {
        var dataKey = tag.getAttribute("data_key");
        var data = window[dataKey];
        if (dataKey.startsWith("data_ru_")) {
            loadButtonContent_ru(data)
        } else if (dataKey.startsWith("rootdata_ru_")) {
            loadRootButtonContent_ru(data)
        }
    });
};

//// load json data into buttons 

function loadButtonContent_ru(data) {

    const lemmaTag = data.lemma.replace(/ /g, "_").replace(".", "_") // a 1.1 > a_1_1
    
    //// feedback

    const feedbackHTML = makeFeedback_ru(data);
    const feedbackElement = document.getElementById(`feedback_ru_${lemmaTag}`)
    feedbackElement.innerHTML = feedbackHTML

    // frequency

    if (data.CstFreq != undefined) {
        const frequencyHTML = makeFrequency(data);
        const frequencyElement = document.getElementById(`frequency_ru_${lemmaTag}`)
        frequencyElement.innerHTML = frequencyElement.innerHTML.replace("frequency loading...", frequencyHTML)
    };

    //// family compounds

    if (
        data.family_compounds
        && data.family_compounds.length > 0
        && typeof ru_family_compound_json !== "undefined"
    ) {
        const familyCompoundHtml = makeFamilyCompoundHtml_ru(data)
        const familyCompoundElement = document.getElementById(`family_compound_ru_${lemmaTag}`)
        familyCompoundElement.innerHTML = familyCompoundHtml
    };

    //// family root

    if (data.family_root != ""
        && typeof ru_family_root_json !== "undefined"
    ) {
        const fr = ru_family_root_json[data.family_root];
        const familyRootHtml = makeFamilyRootHtml_ru(data, fr);
        const familyRootElement = document.getElementById(`family_root_ru_${lemmaTag}`);
        familyRootElement.innerHTML = familyRootHtml;
    };

    //// family idioms

    if (
        data.family_idioms
        && data.family_idioms.length > 0
        && typeof ru_family_idiom_json !== "undefined"
    ) {
        const familyIdiomHtml = makeFamilyIdioms_ru(data)
        const familyIdiomElement = document.getElementById(`family_idiom_ru_${lemmaTag}`)
        familyIdiomElement.innerHTML = familyIdiomHtml
    };

    //// family sets

    if (
        data.family_sets 
        && data.family_sets.length > 0
        && typeof ru_family_set_json !== "undefined"
    ) {
        const familySetHtml = makeFamilySets_ru(data)
        const familySetElement = document.getElementById(`family_set_ru_${lemmaTag}`)
        familySetElement.innerHTML = familySetHtml
    };

    //// family word

    if (
        data.family_word
        && typeof ru_family_word_json !== "undefined"
    ) {
        const familyWordHtml = makeFamilyWordHtml_ru(data);
        const familyWordElement = document.getElementById(`family_word_ru_${lemmaTag}`)
        familyWordElement.innerHTML = familyWordHtml
    };
};

//// load root dictionary button content

function loadRootButtonContent_ru(data) {
    const familyRootDivs = document.querySelectorAll('div[id^="family_root_ru_"]');
    var familyRootArray = Array.from(familyRootDivs);
    familyRootArray.forEach(item => {
        const key_id = item.id
        const key_clean = item.id.replace("family_root_ru_", "").replace(/_/g, " ")
        const fr = ru_family_root_json[key_clean]
        if (fr !==undefined ){
            const familyRootHtml = makeFamilyRootHtml_ru(data, fr, "root", link);
            const familyRootElement = document.getElementById(key_id)
            familyRootElement.innerHTML = familyRootHtml
        } else {
            console.log(`${key_clean} not found in family_root_json.js`)
        }

    })
};

function superScripter(text) {
    const regex = /\d/g;
    return text.replace(regex, match => `&hairsp;<sup>${match}</sup>`);
}