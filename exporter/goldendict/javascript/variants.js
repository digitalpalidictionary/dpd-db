// A long variants list starts folded (exporter/variants/variants_exporter.py);
// its button shows or hides the rest, as dpd.js does on the website.

// Every entry's header can load this file. A second listener would toggle each
// click twice and leave the list unchanged, so only the first load adds one.
if (typeof variants_listener_added === "undefined") {
    var variants_listener_added = true;

    document.addEventListener("click", function (event) {
        var moreButton = event.target.closest(".variants-more");
        if (!moreButton) {
            return;
        }
        var table = moreButton.closest(".dpd").querySelector("table.variants");
        var expand = moreButton.getAttribute("aria-expanded") !== "true";
        table.querySelectorAll(".variant-more").forEach(function (row) {
            row.classList.toggle("hidden", !expand);
        });
        moreButton.setAttribute("aria-expanded", expand ? "true" : "false");
        moreButton.textContent = expand
            ? moreButton.getAttribute("data-less")
            : moreButton.getAttribute("data-more");
        if (!expand) {
            moreButton.scrollIntoView({ block: "nearest" });
        }
    });
}
