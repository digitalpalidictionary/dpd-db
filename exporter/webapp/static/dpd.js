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
    var audio = new Audio('/audio/' + encodeURIComponent(headword) + '?gender=' + gender + '&v=' + Date.now());
    
    // Explicitly set handlers to see if we can catch the exact moment of failure
    audio.onerror = function() {
        console.error("Audio failed to load:", audio.error);
    };

    audio.play().catch(function (error) {
        console.error("Audio playback error:", error);
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