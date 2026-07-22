// The standalone popout window. It reuses the in-page DictionaryPanel component,
// routes search through the background `fetchData` message (exactly like the
// in-page panel), and offers a "pop in" button that returns the dictionary to the
// page. Selections made on the source page while popped out are forwarded here.
import '@/assets/styles/chrome-extension.css';
import '@/assets/styles/dpd-variables.css';
import '@/assets/styles/dpd.css';
import { browser } from 'wxt/browser';
import { DictionaryPanel } from '@/components/dictionary-panel';
import { applyTheme } from '@/utils/themes';
import { addListenersToTextElements } from '@/utils/utils';
import { searchWord } from '@/utils/search';

// Dropping a draggable (a link/button dragged from the source page, say) onto this
// window would otherwise trigger the browser's default "navigate to the dropped URL"
// behaviour — turning the popout into an ordinary https page, where the content script
// then runs and spawns its OWN in-page panel, leaving two DPDs and desynced state.
// Swallow drops that don't land on a text input (where inserting text is expected UX).
function isTextTarget(t: EventTarget | null): boolean {
  const el = t as HTMLElement | null;
  return !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || !!el.closest?.('.dpd-search-box'));
}
for (const type of ['dragover', 'drop'] as const) {
  window.addEventListener(type, (e) => { if (!isTextTarget(e.target)) e.preventDefault(); });
}

const params = new URLSearchParams(location.search);
const initialQuery = params.get('q') || '';
const sourceHost = params.get('host') || ''; // the site this popout serves
// The source page resolves its live theme to a concrete key (e.g. "s4nt_dark") and
// passes it here, so the popout reproduces it with applyTheme(key) — no DOM guessing.
// A bare "auto" (unrecognised source site) falls back to detecting the popout's own bg.
const themeKey = params.get('theme') || 'auto';

let myWinId: number | null = null;
browser.windows
  .getCurrent()
  .then((w) => {
    if (w?.id != null) myWinId = w.id;
  })
  .catch(() => {});

const panel = new DictionaryPanel({ neverMinimize: true });
(window as any).panel = panel;
const panelEl = document.getElementById('dict-panel-25445');

// In the popout the logo just opens the site; the "close via toolbar icon" hint
// doesn't apply here, so show line 1 only.
const logoTip = panelEl?.querySelector<HTMLElement>('.dpd-logo-link .dpd-tooltip-text');
if (logoTip) {
  logoTip.textContent = 'Click to open dpdict.net in a new tab';
  logoTip.style.left = '0';
  logoTip.style.transform = 'none';
}

// The popout should never show the minimized sliver, regardless of the saved setting.
// NOTE: the observer must (a) only act when the class is actually present and
// (b) disconnect while removing it. An unconditional classList.remove() rewrites the
// class attribute even when the token is absent, which queues another 'attributes'
// mutation and re-invokes this callback — an infinite microtask loop that froze the
// popout (it was tripped by applyTheme() toggling the "dark-mode" class).
if (panelEl) {
  const mo = new MutationObserver(() => {
    if (!panelEl.classList.contains('dpd-minimized')) return;
    mo.disconnect();
    panelEl.classList.remove('dpd-minimized');
    mo.observe(panelEl, { attributes: true, attributeFilter: ['class'] });
  });
  mo.observe(panelEl, { attributes: true, attributeFilter: ['class'] });
  panelEl.classList.remove('dpd-minimized');
}

applyTheme(themeKey);

// Route the panel's search box and the initial query through the shared search
// helper, so the popout gets the same offline / GoldenDict / error handling as the
// in-page panel instead of a bare "Error" / "No results".
(window as any).handleSelectedWord = async (raw: string) => {
  await searchWord(raw, panel);
};

// Replace the "pop out" affordance with a "pop in" button in this window.
function addPopInButton() {
  const group = panelEl?.querySelector('.dpd-action-group');
  if (!group || group.querySelector('#dpd-popin-btn')) return;
  const btn = document.createElement('button');
  btn.id = 'dpd-popin-btn';
  btn.type = 'button';
  btn.className = 'dpd-tooltip';
  btn.innerHTML =
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M22 3.41l-5.29 5.29L20 12h-8V4l3.29 3.29L20.59 2 22 3.41zM3.41 22l5.29-5.29L12 20v-8H4l3.29 3.29L2 20.59 3.41 22z"/></svg>';
  const tip = document.createElement('span');
  tip.className = 'dpd-tooltip-text';
  tip.textContent = 'Put the dictionary back into the page';
  btn.appendChild(tip);
  btn.addEventListener('click', () => {
    // Background falls back to the sender's window id if myWinId isn't known yet,
    // so there's no window.close() fallback that could race the pin flag.
    browser.runtime.sendMessage({ action: 'popIn', win: myWinId }).catch(() => {});
  });
  group.insertBefore(btn, group.firstChild);
}
addPopInButton();

// Make words in the popout's own results clickable: double-click / drag-select-to-
// search, routed through this window's handleSelectedWord (same wiring the in-page
// content script installs via init()). Without this the popout can only be driven
// from the search box or the source page, not by clicking words in its own entry.
// The flag tells handleMouseUp to allow drag-select search inside the panel here,
// where the whole result is the panel (in-page that guard is kept for copy).
(window as any).dpdIsPopout = true;
addListenersToTextElements();

if (initialQuery) (window as any).handleSelectedWord(initialQuery);

// Words selected on any tab of this site (while popped out) are forwarded here.
// popoutSearch is a broadcast, so ignore selections tagged with a different host
// (prevents crosstalk when two different sites are popped out at once).
browser.runtime.onMessage.addListener((msg: any) => {
  if (!msg || typeof msg !== 'object') return;
  // Both messages are host-scoped broadcasts. When this popout knows its site,
  // require a matching host — reject unscoped or other-site messages (a missing
  // host no longer slips through).
  if (sourceHost && msg.host !== sourceHost) return;
  if (msg.action === 'popoutSearch' && typeof msg.q === 'string') {
    (window as any).handleSelectedWord(msg.q);
  } else if (msg.action === 'popoutTheme' && typeof msg.theme === 'string') {
    // The source page's auto-theme resolved to a new key (host toggled dark/light).
    applyTheme(msg.theme);
  }
});
