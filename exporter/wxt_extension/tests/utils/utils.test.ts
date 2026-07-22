import { describe, it, expect } from 'vitest';
import { cleanWord } from '@/utils/utils';

describe('cleanWord', () => {
  it('lowercases and trims', () => {
    expect(cleanWord('  Buddha  ')).toBe('buddha');
    expect(cleanWord('Ṭhānaṁ')).toBe('ṭhānaṁ');
  });

  it('strips punctuation and digits, keeps Pāḷi letters', () => {
    expect(cleanWord('dhamma.')).toBe('dhamma');
    expect(cleanWord('(dhamma)')).toBe('dhamma');
    expect(cleanWord('dhamma123')).toBe('dhamma');
    expect(cleanWord('“jhānan”ti')).toBe('jhānanti');
  });

  it('collapses the double-click doubling artifact (even length, halves equal)', () => {
    expect(cleanWord('dhammadhamma')).toBe('dhamma');
    expect(cleanWord('BuddhaBuddha')).toBe('buddha');
  });

  it('does not collapse when the halves differ or it contains a space', () => {
    expect(cleanWord('dhammabuddha')).toBe('dhammabuddha');
    expect(cleanWord('sabbe dhamma')).toBe('sabbe dhamma');
  });

  it('treats an em-dash as a word boundary, not a joinable char', () => {
    // Regression: "upakkileso’ti—iti" was glued into "upakkilesotiiti".
    expect(cleanWord('upakkileso’ti—iti')).toBe('upakkilesoti iti');
    expect(cleanWord('word — word')).toBe('word word');
  });

  it('does not collapse short even words below the length threshold', () => {
    expect(cleanWord('koko')).toBe('koko'); // length 4 < 6
  });
});
