window.expandSelectionToWord = function() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  
  // If the selection already spans across multiple nodes (like in the panel), 
  // trust it and don't try to expand/modify it.
  if (range.startContainer !== range.endContainer) return;

  const initialNode = range.startContainer;
  if (initialNode.nodeType !== Node.TEXT_NODE) return;

  // Characters to stop on.
  const stopChars = /[ \t\n\r\.\,\;\:\!\?\(\)\[\]\{\}\\\/\*\&\%\$\#\@\+\=\<\>\♦]/;
  const isStop = (char) => !char || stopChars.test(char);

  let startNode = initialNode;
  let startOffset = range.startOffset;
  let endNode = initialNode;
  let endOffset = range.endOffset;

  // Helper to find the next/previous text node in the document order
  const getNextTextNode = (node, forward) => {
    let current = node;
    while (current) {
      // Move to sibling or parent's sibling
      let next = forward ? current.nextSibling : current.previousSibling;
      if (!next) {
        current = current.parentElement;
        // Don't cross out of a block element
        if (current && window.getComputedStyle(current).display !== 'inline') return null;
        continue;
      }
      current = next;

      // If we hit a block element, stop
      if (current.nodeType === Node.ELEMENT_NODE && window.getComputedStyle(current).display !== 'inline') {
        return null;
      }

      // If it's a text node, return it
      if (current.nodeType === Node.TEXT_NODE) return current;

      // If it's an inline element, go inside it
      if (current.nodeType === Node.ELEMENT_NODE) {
        const walker = document.createTreeWalker(current, NodeFilter.SHOW_TEXT, null, false);
        const textNode = forward ? walker.firstChild() : walker.lastChild();
        if (textNode) return textNode;
      }
    }
    return null;
  };

  // Expand backwards
  while (true) {
    const text = startNode.nodeValue;
    while (startOffset > 0 && !isStop(text[startOffset - 1])) {
      startOffset--;
    }
    
    if (startOffset === 0) {
      const prev = getNextTextNode(startNode, false);
      if (prev && prev.nodeValue.length > 0 && !isStop(prev.nodeValue[prev.nodeValue.length - 1])) {
        startNode = prev;
        startOffset = prev.nodeValue.length;
        continue;
      }
    }
    break;
  }

  // Expand forwards
  while (true) {
    const text = endNode.nodeValue;
    while (endOffset < text.length && !isStop(text[endOffset])) {
      endOffset++;
    }

    if (endOffset === text.length) {
      const next = getNextTextNode(endNode, true);
      if (next && next.nodeValue.length > 0 && !isStop(next.nodeValue[0])) {
        endNode = next;
        endOffset = 0;
        continue;
      }
    }
    break;
  }

  // Update selection
  try {
    selection.setBaseAndExtent(startNode, startOffset, endNode, endOffset);
  } catch (e) {
    console.error("[DPD] Expansion error:", e);
  }
};

window.getSelectedWord = function() {
  window.expandSelectionToWord();
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text === '⇅' || text === '▲' || text === '▼') return null;
  return text;
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
