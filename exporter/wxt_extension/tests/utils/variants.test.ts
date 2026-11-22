import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { toggleVariants } from '@/utils/variants';

// The variants block of /search_json?q=aṭṭhikatvā&fold=1 from the webapp:
// 20 data rows in 4 sources, the shortest list that folds.
const FIXTURE = readFileSync(
  resolve(__dirname, '../fixtures/variants_folded.html'),
  'utf-8',
);

function dataRows(): HTMLTableRowElement[] {
  return [...document.querySelectorAll<HTMLTableRowElement>('table.variants tr')].filter(
    (row) => row.querySelector('td:not([colspan])'),
  );
}

function visibleDataRows(): number {
  return dataRows().filter((row) => !row.classList.contains('hidden')).length;
}

function button(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('button.variants-more')!;
}

beforeEach(() => {
  document.body.innerHTML = `<div id="panel-content">${FIXTURE}</div>`;
});

describe('toggleVariants', () => {
  it('starts folded to the first 10 of 20 rows', () => {
    expect(dataRows()).toHaveLength(20);
    expect(visibleDataRows()).toBe(10);
    expect(button().textContent).toBe('show all 20 variants');
    expect(button().getAttribute('aria-expanded')).toBe('false');
  });

  it('shows every row, and the separators after the fold, on the first click', () => {
    toggleVariants(button());
    expect(visibleDataRows()).toBe(20);
    expect(document.querySelectorAll('table.variants tr.hidden')).toHaveLength(0);
    expect(button().textContent).toBe('show fewer');
    expect(button().getAttribute('aria-expanded')).toBe('true');
  });

  it('folds again on the second click', () => {
    toggleVariants(button());
    expect(visibleDataRows()).toBe(20);
    toggleVariants(button());
    expect(visibleDataRows()).toBe(10);
    expect(document.querySelectorAll('table.variants tr.hidden')).toHaveLength(12);
    expect(button().textContent).toBe('show all 20 variants');
    expect(button().getAttribute('aria-expanded')).toBe('false');
  });
});
