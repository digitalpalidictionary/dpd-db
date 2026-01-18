function getSelectedWord() {
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (text && text.split(/\s+/).length === 1) {
    return text;
  }
  return null;
}

// Add listener to all elements that contain text
function addListenersToTextElements() {
  document.body.addEventListener("mouseup", (e) => {
    // If click was on a button, dropdown, or search input, do nothing
    if (e.target.closest('.button') || 
        e.target.closest('.theme-selector-btn') || 
        e.target.closest('.dpd-dropdown') ||
        e.target.closest('.dpd-search-box')) {
      return;
    }

    const word = getSelectedWord();
    if (word) {
      handleSelectedWord(word);
      // Clear selection so clicking elsewhere doesn't re-trigger the same word
      window.getSelection().removeAllRanges();
    }
  });
}
