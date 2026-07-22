import { browser } from 'wxt/browser';
import { cleanWord } from '@/utils/utils';
import type { DictionaryPanel } from '@/components/dictionary-panel';

// Monotonic per-context search counter. Each searchWord call takes the next
// number; a response only renders if it is still the newest, so a slow earlier
// lookup can't overwrite a newer one when words are clicked in quick succession.
// (content script and popout are separate JS contexts, each with their own count.)
let searchGeneration = 0;

// Single source of truth for a dictionary lookup, shared by the in-page content
// script and the popout window so their success/empty/error and offline/GoldenDict
// behaviour can't drift apart. Callers pass the raw selected/typed word and the
// panel to render into (null when there is no panel to update).
export async function searchWord(rawWord: string, panel: DictionaryPanel | null): Promise<void> {
  const q = cleanWord(rawWord);
  if (!q) return;

  // "Use GoldenDict" preference: always hand off to GoldenDict, never fetch.
  if (panel?.settings?.goldenDict) {
    panel.openInGoldenDict(q);
    return;
  }

  const generation = ++searchGeneration;
  const isStale = () => generation !== searchGeneration;

  panel?.setSearchValue(q);
  panel?.setText('Loading...');

  // Offline: GoldenDict fallback instead of a doomed network call.
  if (!navigator.onLine) {
    panel?.openInGoldenDict(q);
    return;
  }

  try {
    const response: any = await browser.runtime.sendMessage({
      action: 'fetchData',
      endpoint: '/search_json?q=' + encodeURIComponent(q),
    });
    if (isStale()) return; // a newer search started while this was in flight
    if (response?.success) {
      const data = response.data;
      if (!data || (!data.summary_html && !data.dpd_html)) {
        panel?.setText('No results for ' + q);
      } else {
        panel?.setText('Result for ' + q);
        panel?.setContent((data.summary_html || '') + '<hr class="dpd">' + (data.dpd_html || ''));
      }
    } else {
      // API error (now includes non-OK HTTP status, see background fetchData).
      panel?.openInGoldenDict(q);
    }
  } catch {
    if (isStale()) return;
    panel?.openInGoldenDict(q);
  }
}
