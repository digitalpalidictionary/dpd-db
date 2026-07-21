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
import { cleanWord } from '@/utils/utils';

const params = new URLSearchParams(location.search);
const initialQuery = params.get('q') || '';
const sourceTab = params.get('tab') || ''; // the tab this popout was detached from
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

const panel = new DictionaryPanel();
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
const unminimize = () => panelEl?.classList.remove('dpd-minimized');
if (panelEl) {
  new MutationObserver(unminimize).observe(panelEl, {
    attributes: true,
    attributeFilter: ['class'],
  });
  unminimize();
}

applyTheme(themeKey);

// Route the panel's search box and the initial query through the background fetch.
(window as any).handleSelectedWord = async (raw: string) => {
  const q = cleanWord(raw);
  if (!q) return;
  panel.setSearchValue(q);
  panel.setText('Loading...');
  try {
    const r: any = await browser.runtime.sendMessage({
      action: 'fetchData',
      endpoint: '/search_json?q=' + encodeURIComponent(q),
    });
    if (r?.success && r.data && (r.data.summary_html || r.data.dpd_html)) {
      panel.setText('Result for ' + q);
      panel.setContent((r.data.summary_html || '') + '<hr class="dpd">' + (r.data.dpd_html || ''));
    } else {
      panel.setText('No results for ' + q);
    }
  } catch (e: any) {
    panel.setText('Error: ' + (e?.message ?? String(e)));
  }
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

if (initialQuery) (window as any).handleSelectedWord(initialQuery);

// Words selected on the originating page (while popped out) are forwarded here.
// popoutSearch is a broadcast, so ignore selections from any tab other than our own
// (prevents crosstalk when two tabs are popped out at once).
browser.runtime.onMessage.addListener((msg: any) => {
  if (msg && typeof msg === 'object' && msg.action === 'popoutSearch') {
    if (sourceTab && msg.tab != null && String(msg.tab) !== sourceTab) return;
    (window as any).handleSelectedWord(msg.q);
  }
});
