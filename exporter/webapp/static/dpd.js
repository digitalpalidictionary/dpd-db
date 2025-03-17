
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
    let oneButtonToggleEnabled = false;
    try {
        oneButtonToggleEnabled = localStorage.getItem("one-button-toggle") === "true";
    } catch (e) {
        console.log("LocalStorage is not available.");
    }
    const target_id = el.getAttribute("data-target");
    var target = document.getElementById(target_id);
    
    if (target) {
        if (target.textContent.includes("loading...")) {
            loadData()
        };

        //// only open one button at a time

        if (oneButtonToggleEnabled) {
            var allButtons = document.querySelectorAll('.button, .root_button');
            allButtons.forEach(function(button) {
                if (button!== el) { // Exclude the target button
                    button.classList.remove("active");
                }
            });

            var allContentAreas = document.querySelectorAll('.content, .root_content');
            allContentAreas.forEach(function(contentArea) {
                if (contentArea!== target &&!contentArea.classList.contains("summary")) {
                    contentArea.classList.add("hidden");
                }
            });
        }

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



