function playAudio(headword, buttonElement) {
    let gender = "male";
    try {
        const audioToggle = localStorage.getItem("audio-toggle");
        if (audioToggle === "true") {
            gender = "female";
        }
    } catch (e) {
    }

    // Single source of truth for audio requests
    // Using a fresh timestamp to force bypass of any cached errors
    const url = '/audio/' + encodeURIComponent(headword) + '?gender=' + gender + '&v=' + Date.now();
    console.log("DPD_AUDIO_REQUEST:", url);
    var audio = new Audio(url);
    
    // Explicitly set handlers to see if we can catch the exact moment of failure
    audio.onerror = function() {
        console.error("DPD_AUDIO_ERROR_LOAD:", audio.error);
    };

    audio.play().then(() => {
        console.log("DPD_AUDIO_PLAY_STARTED");
    }).catch(function (error) {
        console.error("DPD_AUDIO_ERROR_PLAY:", error.name, error.message);
    });
}

// Minimal click handler for other buttons
document.addEventListener("click", function (event) {
    var target = event.target.closest(".button");
    if (target && target.getAttribute("data-target")) {
        button_click(target);
        event.preventDefault();
    }
});

function button_click(el) {
    const target_id = el.getAttribute("data-target");
    var target = document.getElementById(target_id);
    if (target) {
        target.classList.toggle("hidden");
        el.classList.toggle("active");
    }
}