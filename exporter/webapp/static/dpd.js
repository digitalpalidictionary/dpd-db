function playAudio(headword) {
    if (!headword) return;
    
    let gender = "male";
    try {
        const audioToggle = localStorage.getItem("audio-toggle");
        if (audioToggle === "true") {
            gender = "female";
        }
    } catch (e) {}

    const url = '/audio/' + encodeURIComponent(headword) + '?gender=' + gender;
    var audio = new Audio(url);
    audio.play().catch(function (error) {
        console.error("Audio playback error:", error);
    });
}

// Attach to window so it's always accessible
window.playAudio = playAudio;

// Global delegated click listener
document.addEventListener("click", function (event) {
    var playButton = event.target.closest(".button.play");
    if (playButton) {
        var headword = playButton.getAttribute("data-headword");
        if (headword) {
            playAudio(headword);
            event.preventDefault();
            return false;
        }
    }

    var otherButton = event.target.closest(".button");
    if (otherButton && otherButton.getAttribute("data-target")) {
        const target_id = otherButton.getAttribute("data-target");
        var target = document.getElementById(target_id);
        if (target) {
            let oneButtonToggleEnabled = false;
            try {
                oneButtonToggleEnabled = localStorage.getItem("one-button-toggle") === "true";
            } catch (e) {
                console.log("LocalStorage is not available.");
            }

            if (oneButtonToggleEnabled) {
                var allButtons = document.querySelectorAll('.button');
                allButtons.forEach(function (button) {
                    if (button !== otherButton) {
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

            if (otherButton.classList.contains("close")) {
                var target_control = document.querySelector('a.button[data-target="' + target_id + '"]');
                if (target_control) {
                    target_control.classList.toggle("active");
                }
            } else {
                otherButton.classList.toggle("active");
            }
        }
        event.preventDefault();
    }
});