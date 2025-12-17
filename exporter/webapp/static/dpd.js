
//// listen for button clicks

document.addEventListener("click", function (event) {
    var target = event.target;
    const classNames = ["button"]
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
            var allButtons = document.querySelectorAll('.button');
            allButtons.forEach(function (button) {
                if (button !== el) {
                    button.classList.remove("active");
                }
            });

            var allContentAreas = document.querySelectorAll('.content');
            allContentAreas.forEach(function (contentArea) {
                if (contentArea !== target && !contentArea.classList.contains("summary")) {
                    contentArea.classList.add("hidden");
                }
            });

            if (!target.classList.contains('summary')) {
                target.classList.toggle("hidden");
            }
        } else {
            target.classList.toggle("hidden");
        }

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

function playAudio(headword, buttonElement) {
    let gender = "male";
    try {
        const audioToggle = localStorage.getItem("audio-toggle");
        if (audioToggle === "true") {
            gender = "female";
        }
    } catch (e) {
        console.log("LocalStorage is not available.");
    }

    var audio = new Audio('/audio/' + headword + '?gender=' + gender);

    audio.addEventListener("error", function () {
        if (buttonElement) {
            // Change icon to cross
            buttonElement.innerHTML = `
                <svg viewBox="0 0 24 24" width="16px" height="16px" fill="currentColor" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            `;
            // Disable button
            buttonElement.classList.add("disabled");
            buttonElement.style.pointerEvents = "none";
            buttonElement.title = "Audio not found";
            buttonElement.removeAttribute("onclick");
        }
    });

    audio.play().catch(function (error) {
        // This catch block handles cases where play() Promise rejects 
        // (e.g. user interaction policy, or source error which might also trigger the error event)
        console.log("Audio play failed: ", error);
        // The error listener above usually catches the 404, but we can double check here or just rely on the listener.
    });
}
