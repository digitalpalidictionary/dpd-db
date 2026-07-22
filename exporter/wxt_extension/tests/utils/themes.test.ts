import { describe, it, expect, afterEach } from 'vitest';
import { detectTheme } from '@/utils/themes';

function setUrl(url: string): void {
  // detectTheme reads window.location.href; a URL object satisfies that shape
  // without triggering jsdom's not-implemented navigation.
  Object.defineProperty(window, 'location', { value: new URL(url), configurable: true });
}

afterEach(() => {
  Object.defineProperty(window, 'location', {
    value: new URL('https://example.com/'),
    configurable: true,
  });
});

describe('detectTheme URL mapping', () => {
  it('maps hosts with a single deterministic theme', () => {
    setUrl('https://digitalpalireader.online/reader');
    expect(detectTheme()).toBe('dpr');

    setUrl('https://www.tipitaka.org/romn/');
    expect(detectTheme()).toBe('vri');

    setUrl('https://open.tipitaka.lk/1-1-0/sinh');
    expect(detectTheme()).toBe('tipitakalk');

    setUrl('https://tipitaka.paauksociety.org/book/1');
    expect(detectTheme()).toBe('paauksociety');
  });

  it('falls back to "auto" for an unknown host', () => {
    setUrl('https://example.com/page');
    expect(detectTheme()).toBe('auto');
  });

  it('maps dark-aware hosts to that host\'s theme family', () => {
    setUrl('https://suttacentral.net/mn1');
    expect(detectTheme()).toMatch(/^suttacentral/);

    setUrl('https://thebuddhaswords.net/mn/mn1.html');
    expect(detectTheme()).toMatch(/^tbw_/);

    setUrl('https://s.4nt.org/sn56.11');
    expect(detectTheme()).toMatch(/^s4nt_/);
  });
});
