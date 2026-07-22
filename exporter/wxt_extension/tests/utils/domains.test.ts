import { describe, it, expect } from 'vitest';
import { isAutoDomain, isExcludedDomain } from '@/utils/domains';

describe('isAutoDomain', () => {
  it('matches an exact auto-domain host', () => {
    expect(isAutoDomain('suttacentral.net')).toBe(true);
    expect(isAutoDomain('s.4nt.org')).toBe(true);
    expect(isAutoDomain('tipitaka.paauksociety.org')).toBe(true);
  });

  it('matches subdomains of an auto-domain', () => {
    expect(isAutoDomain('www.suttacentral.net')).toBe(true);
    expect(isAutoDomain('discourse.suttacentral.net')).toBe(true);
  });

  it('does not match unrelated hosts', () => {
    expect(isAutoDomain('example.com')).toBe(false);
    expect(isAutoDomain('notsuttacentral.net')).toBe(false); // not a real subdomain boundary
  });
});

describe('isExcludedDomain', () => {
  it('matches the excluded discourse host', () => {
    expect(isExcludedDomain('discourse.suttacentral.net')).toBe(true);
  });

  it('leaves other suttacentral hosts unexcluded', () => {
    expect(isExcludedDomain('suttacentral.net')).toBe(false);
    expect(isExcludedDomain('example.com')).toBe(false);
  });
});
