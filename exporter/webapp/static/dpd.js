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
            target.classList.toggle("hidden");
            otherButton.classList.toggle("active");
        }
        event.preventDefault();
    }
});