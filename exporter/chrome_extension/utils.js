window.getSelectedWord = window.getSelectedWord || function() {
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (text === '⇅' || text === '▲' || text === '▼') return null;
  if (text && text.split(/\s+/).length === 1) return text;
  return null;
};

window.addListenersToTextElements = window.addListenersToTextElements || function() {
  // Use dblclick exclusively for lookup to avoid UI collisions
  document.body.addEventListener("dblclick", (e) => {
    // Ignore UI elements
     if (e.target.closest('.dpd-button') || 
        e.target.closest('.theme-selector-btn') || 
        e.target.closest('.dpd-dropdown') ||
        e.target.closest('.dpd-search-box')) {
      return;
    }

    const word = window.getSelectedWord();
    if (word) {
      handleSelectedWord(word);
      window.getSelection().removeAllRanges();
    }
  });
};