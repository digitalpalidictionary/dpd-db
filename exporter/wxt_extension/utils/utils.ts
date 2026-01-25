import { MessageRequest } from '../types/extension';

export function expandSelectionToWord(): void {
  const selection = window.getSelection();
  if (!selection || !selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  
  // If the selection already spans across multiple nodes, trust it.
  if (range.startContainer !== range.endContainer) return;

  const initialNode = range.startContainer;
  if (initialNode.nodeType !== Node.TEXT_NODE) return;

  // Characters to stop on.
  const stopChars = /[ \t\n\r\.\,\;\:\!\?\(\)\[\]\{\}\\\/\*\&\%\$\#\@\+\=\<\>\♦]/;
  const isStop = (char: string) => !char || stopChars.test(char);

  let startNode: Node | null = initialNode;
  let startOffset = range.startOffset;
  let endNode: Node | null = initialNode;
  let endOffset = range.endOffset;

  // Helper to find the next/previous text node in the document order
  const getNextTextNode = (node: Node, forward: boolean): Node | null => {
    let current: Node | null = node;
    while (current) {
      // Move to sibling or parent's sibling
      let next: Node | null = forward ? current.nextSibling : current.previousSibling;
      if (!next) {
        current = current.parentElement;
        // Don't cross out of a block element
        if (current && window.getComputedStyle(current as Element).display !== 'inline') return null;
        continue;
      }
      current = next;

      // If we hit a block element, stop
      if (current.nodeType === Node.ELEMENT_NODE && window.getComputedStyle(current as Element).display !== 'inline') {
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
  while (startNode && startNode.nodeValue) {
    const text = startNode.nodeValue;
    while (startOffset > 0 && !isStop(text[startOffset - 1])) {
      startOffset--;
    }
    
    if (startOffset === 0) {
      const prev = getNextTextNode(startNode, false);
      if (prev && prev.nodeValue && prev.nodeValue.length > 0 && !isStop(prev.nodeValue[prev.nodeValue.length - 1])) {
        startNode = prev;
        startOffset = prev.nodeValue.length;
        continue;
      }
    }
    break;
  }

  // Expand forwards
  while (endNode && endNode.nodeValue) {
    const text = endNode.nodeValue;
    while (endOffset < text.length && !isStop(text[endOffset])) {
      endOffset++;
    }

    if (endOffset === text.length) {
      const next = getNextTextNode(endNode, true);
      if (next && next.nodeValue && next.nodeValue.length > 0 && !isStop(next.nodeValue[0])) {
        endNode = next;
        endOffset = 0;
        continue;
      }
    }
    break;
  }

  // Update selection
  try {
    if (startNode && endNode) {
      selection.setBaseAndExtent(startNode, startOffset, endNode, endOffset);
    }
  } catch (e) {
    console.error("[DPD] Expansion error:", e);
  }
}

export function getSelectedWord(): string | null {
  expandSelectionToWord();
  const selection = window.getSelection();
  const text = selection ? selection.toString().trim() : '';
  if (!text || text === '⇅' || text === '▲' || text === '▼') return null;
  return text;
}

let dragStartX = 0;
let dragStartY = 0;

export function handleMouseDown(e: MouseEvent): void {
  dragStartX = e.clientX;
  dragStartY = e.clientY;
}

export function handleMouseUp(e: MouseEvent): void {
  const target = e.target as Element;
  // Ignore clicks on inputs or buttons
  if (target.tagName === 'INPUT' || target.tagName === 'BUTTON' || target.closest('button')) return;

  const dx = Math.abs(e.clientX - dragStartX);
  const dy = Math.abs(e.clientY - dragStartY);
  
  // If moved more than 5px, it's likely a drag selection
  if (dx > 5 || dy > 5) {
    const selection = window.getSelection()?.toString().trim();
    if (selection && selection.length > 0) {
      setTimeout(() => {
        const finalSelection = window.getSelection()?.toString().trim();
        if (finalSelection && typeof window.handleSelectedWord === 'function') {
          window.handleSelectedWord(finalSelection);
        }
      }, 10);
    }
  }
}

export function handleDblClick(e: MouseEvent): void {
  const target = e.target as Element;
  // Ignore clicks on inputs or buttons
  if (target.tagName === 'INPUT' || target.tagName === 'BUTTON' || target.closest('button')) return;
  
  const word = getSelectedWord();
  if (word && typeof window.handleSelectedWord === 'function') {
    window.handleSelectedWord(word);
  }
}

export function addListenersToTextElements(): void {
  document.body.removeEventListener("dblclick", handleDblClick);
  document.body.removeEventListener("mousedown", handleMouseDown);
  document.body.removeEventListener("mouseup", handleMouseUp);
  
  document.body.addEventListener("dblclick", handleDblClick);
  document.body.addEventListener("mousedown", handleMouseDown);
  document.body.addEventListener("mouseup", handleMouseUp);
}

export function removeListenersFromTextElements(): void {
  document.body.removeEventListener("dblclick", handleDblClick);
  document.body.removeEventListener("mousedown", handleMouseDown);
  document.body.removeEventListener("mouseup", handleMouseUp);
}

// Attach to window for legacy compatibility if needed, 
// though we should prefer importing these functions directly.
if (typeof window !== 'undefined') {
  window.expandSelectionToWord = expandSelectionToWord;
  window.getSelectedWord = getSelectedWord;
  window.handleMouseDown = handleMouseDown;
  window.handleMouseUp = handleMouseUp;
  window.handleDblClick = handleDblClick;
  window.addListenersToTextElements = addListenersToTextElements;
  window.removeListenersFromTextElements = removeListenersFromTextElements;
}
