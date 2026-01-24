window.expandSelectionToWord = function() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  
  // If the selection already spans across multiple nodes (like in the panel), 
  // trust it and don't try to expand/modify it.
  if (range.startContainer !== range.endContainer) return;

  const node = range.startContainer;
  if (node.nodeType !== Node.TEXT_NODE) return;

  const text = node.nodeValue;
  let start = range.startOffset;
  let end = range.endOffset;
  
  // Characters to stop on. Apostrophes and quotes are excluded so they are selected.
  const stopChars = /[ \t\n\r\.\,\;\:\!\?\(\)\[\]\{\}\\\/\*\&\%\$\#\@\+\=\<\>]/;
  const isStop = (char) => !char || stopChars.test(char);

  while (start > 0 && !isStop(text[start - 1])) start--;
  while (end < text.length && !isStop(text[end])) end++;

  // Only update if the expansion actually found more text
  if (start !== range.startOffset || end !== range.endOffset) {
    const newRange = document.createRange();
    newRange.setStart(node, start);
    newRange.setEnd(node, end);
    selection.removeAllRanges();
    selection.addRange(newRange);
  }
};

window.getSelectedWord = function() {
  window.expandSelectionToWord();
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text === '⇅' || text === '▲' || text === '▼') return null;
  if (text.split(/\s+/).length === 1) return text;
  return null;
};

let dragStartX = 0;
let dragStartY = 0;

window.handleMouseDown = function(e) {
  dragStartX = e.clientX;
  dragStartY = e.clientY;
};

window.handleMouseUp = function(e) {
  // Ignore clicks inside the dictionary panel or header
  if (e.target.closest('#dict-panel-25445')) return;

  const dx = Math.abs(e.clientX - dragStartX);
  const dy = Math.abs(e.clientY - dragStartY);
  
  // If moved more than 5px, it's likely a drag selection
  // or if there is a substantial selection that was manually created
  if (dx > 5 || dy > 5) {
    const selection = window.getSelection().toString().trim();
    if (selection && selection.length > 0) {
      // Small delay to ensure we don't conflict with double-click expansion
      setTimeout(() => {
        const finalSelection = window.getSelection().toString().trim();
        if (finalSelection && typeof handleSelectedWord === 'function') {
          handleSelectedWord(finalSelection);
        }
      }, 10);
    }
  }
};

window.handleDblClick = function(e) {
  if (e.target.closest('#dict-panel-25445')) return;
  
  const word = window.getSelectedWord();
  if (word && typeof handleSelectedWord === 'function') {
    handleSelectedWord(word);
  }
};

window.addListenersToTextElements = function() {
  document.body.removeEventListener("dblclick", window.handleDblClick);
  document.body.removeEventListener("mousedown", window.handleMouseDown);
  document.body.removeEventListener("mouseup", window.handleMouseUp);
  
  document.body.addEventListener("dblclick", window.handleDblClick);
  document.body.addEventListener("mousedown", window.handleMouseDown);
  document.body.addEventListener("mouseup", window.handleMouseUp);
};

window.removeListenersFromTextElements = function() {
  document.body.removeEventListener("dblclick", window.handleDblClick);
  document.body.removeEventListener("mousedown", window.handleMouseDown);
  document.body.removeEventListener("mouseup", window.handleMouseUp);
};
