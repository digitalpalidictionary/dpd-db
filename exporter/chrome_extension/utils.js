window.expandSelectionToWord = function() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  const node = range.startContainer;
  if (node.nodeType !== Node.TEXT_NODE) return;

  const text = node.textContent;
  let start = range.startOffset;
  let end = range.endOffset;
  const stopChars = /[ \t\n\r\.\,\;\:\!\?\(\)\[\]\{\}]/;

  while (start > 0 && !stopChars.test(text[start - 1])) start--;
  while (end < text.length && !stopChars.test(text[end])) end++;

  const newRange = document.createRange();
  newRange.setStart(node, start);
  newRange.setEnd(node, end);
  selection.removeAllRanges();
  selection.addRange(newRange);
};

window.getSelectedWord = function() {
  window.expandSelectionToWord();
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text === '⇅' || text === '▲' || text === '▼') return null;
  if (text.split(/\s+/).length === 1) return text;
  return null;
};

window.handleDblClick = function(e) {
  if (e.target.closest('.dpd-button') || 
      e.target.closest('.theme-selector-btn') || 
      e.target.closest('.dpd-dropdown') ||
      e.target.closest('.dpd-search-box') ||
      e.target.closest('.dpd-header')) {
    return;
  }
  const word = window.getSelectedWord();
  if (word && typeof handleSelectedWord === 'function') {
    handleSelectedWord(word);
  }
};

window.addListenersToTextElements = function() {
  document.body.removeEventListener("dblclick", window.handleDblClick);
  document.body.addEventListener("dblclick", window.handleDblClick);
};

window.removeListenersFromTextElements = function() {
  document.body.removeEventListener("dblclick", window.handleDblClick);
};
