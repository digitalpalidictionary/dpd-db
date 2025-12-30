
function playAudio(headword) {
    let gender = "male";
    try {
        const audioToggle = localStorage.getItem("audio-toggle");
        if (audioToggle === "true") {
            gender = "female";
        }
    } catch (e) {}

    // Use a fresh audio object and play immediately
    var audio = new Audio('/audio/' + encodeURIComponent(headword) + '?gender=' + gender);
    audio.play().catch(function (error) {
        console.error("Audio playback error:", error);
    });
}

// Global delegated click listener
// This handles clicks even on search results added later via innerHTML
document.addEventListener("click", function (event) {
    // Find if the clicked element or its parent is a play button
    var playButton = event.target.closest(".button.play");
    if (playButton) {
        // Extract the headword from a data attribute (which we will add to the HTML)
        var headword = playButton.getAttribute("data-headword");
        if (headword) {
            playAudio(headword);
            event.preventDefault();
            return false;
        }
    }

    // Existing handler for other buttons
    var otherButton = event.target.closest(".button");
    if (otherButton && otherButton.getAttribute("data-target")) {
        const target_id = otherButton.getAttribute("data-target");
        var target = document.getElementById(target_id);
        if (target) {
            target.classList.toggle("hidden");
            otherButton.classList.toggle("active");
        }
        event.preventDefault();
    }
});
