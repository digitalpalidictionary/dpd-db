import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { browser } from 'wxt/browser';
import { searchWord } from '@/utils/search';

// Minimal stand-in for the DictionaryPanel surface searchWord touches.
function makePanel(goldenDict = false) {
  return {
    settings: { goldenDict },
    openInGoldenDict: vi.fn(),
    setSearchValue: vi.fn(),
    setText: vi.fn(),
    setContent: vi.fn(),
  } as any;
}

function setOnline(online: boolean) {
  Object.defineProperty(navigator, 'onLine', { value: online, configurable: true });
}

let sendSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  sendSpy = vi.spyOn(browser.runtime, 'sendMessage');
  setOnline(true);
});

afterEach(() => {
  vi.restoreAllMocks();
  setOnline(true);
});

describe('searchWord', () => {
  it('honours the GoldenDict preference without fetching', async () => {
    const panel = makePanel(true);
    await searchWord('Dhamma', panel);
    expect(panel.openInGoldenDict).toHaveBeenCalledWith('dhamma');
    expect(sendSpy).not.toHaveBeenCalled();
  });

  it('falls back to GoldenDict when offline (no fetch)', async () => {
    setOnline(false);
    const panel = makePanel(false);
    await searchWord('dhamma', panel);
    expect(panel.setText).toHaveBeenCalledWith('Loading...');
    expect(panel.openInGoldenDict).toHaveBeenCalledWith('dhamma');
    expect(sendSpy).not.toHaveBeenCalled();
  });

  it('renders content on a successful lookup', async () => {
    sendSpy.mockResolvedValue({ success: true, data: { summary_html: '<b>s</b>', dpd_html: '<i>d</i>' } });
    const panel = makePanel(false);
    await searchWord('dhamma', panel);
    expect(panel.setText).toHaveBeenCalledWith('Result for dhamma');
    expect(panel.setContent).toHaveBeenCalledWith('<b>s</b><hr class="dpd"><i>d</i>');
  });

  it('shows "No results" on an empty 200 response', async () => {
    sendSpy.mockResolvedValue({ success: true, data: {} });
    const panel = makePanel(false);
    await searchWord('dhamma', panel);
    expect(panel.setText).toHaveBeenCalledWith('No results for dhamma');
    expect(panel.setContent).not.toHaveBeenCalled();
  });

  it('falls back to GoldenDict when the API reports failure (e.g. non-OK status)', async () => {
    sendSpy.mockResolvedValue({ success: false, error: 'HTTP 500' });
    const panel = makePanel(false);
    await searchWord('dhamma', panel);
    expect(panel.openInGoldenDict).toHaveBeenCalledWith('dhamma');
    expect(panel.setContent).not.toHaveBeenCalled();
  });

  it('drops a stale (earlier, slower) response so it cannot overwrite a newer one', async () => {
    let resolveA!: (v: unknown) => void;
    let resolveB!: (v: unknown) => void;
    sendSpy
      .mockImplementationOnce(() => new Promise((r) => { resolveA = r; }))
      .mockImplementationOnce(() => new Promise((r) => { resolveB = r; }));

    const panel = makePanel(false);
    const pA = searchWord('aaa', panel); // older
    const pB = searchWord('bbb', panel); // newer

    resolveB({ success: true, data: { dpd_html: 'B' } });
    await pB;
    resolveA({ success: true, data: { dpd_html: 'A' } }); // late — must be ignored
    await pA;

    const rendered = panel.setContent.mock.calls.map((c: unknown[]) => c[0]);
    expect(rendered).toContain('<hr class="dpd">B');
    expect(rendered).not.toContain('<hr class="dpd">A');
    expect(panel.setText).toHaveBeenLastCalledWith('Result for bbb');
  });
});
