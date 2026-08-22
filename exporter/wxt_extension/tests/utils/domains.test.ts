import { describe, it, expect } from 'vitest';
import { isAutoDomain, isExcludedDomain, normalizeHostname } from '@/utils/domains';

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

describe('normalizeHostname', () => {
  it('strips scheme, port and path from a full URL', () => {
    expect(normalizeHostname('https://localhost:3000/foo')).toBe('localhost');
    expect(normalizeHostname('http://example.com/a/b?c=d')).toBe('example.com');
  });

  it('accepts a bare hostname', () => {
    expect(normalizeHostname('example.com')).toBe('example.com');
    expect(normalizeHostname('localhost')).toBe('localhost');
  });

  it('accepts host:port without a scheme', () => {
    expect(normalizeHostname('localhost:8080')).toBe('localhost');
    expect(normalizeHostname('example.com:8080')).toBe('example.com');
  });

  it('lowercases and trims', () => {
    expect(normalizeHostname('  LocalHost  ')).toBe('localhost');
    expect(normalizeHostname('EXAMPLE.COM')).toBe('example.com');
  });

  it('keeps localhost and 127.0.0.1 distinct', () => {
    // They resolve to the same machine but are separate storage keys, so the
    // helper must never fold one into the other.
    expect(normalizeHostname('127.0.0.1:8080')).toBe('127.0.0.1');
    expect(normalizeHostname('localhost')).not.toBe(normalizeHostname('127.0.0.1'));
  });

  it('drops a fully-qualified trailing dot', () => {
    // window.location.hostname never carries one, so keeping it would store an
    // entry that could never match.
    expect(normalizeHostname('example.com.')).toBe('example.com');
    expect(normalizeHostname('.')).toBeNull();
  });

  it('accepts underscores, which browsers report for intranet hosts', () => {
    expect(normalizeHostname('internal_wiki')).toBe('internal_wiki');
    expect(normalizeHostname('http://my_box:8080/x')).toBe('my_box');
  });

  it('rejects empty and whitespace-only input', () => {
    expect(normalizeHostname('')).toBeNull();
    expect(normalizeHostname('   ')).toBeNull();
  });

  it('rejects input with no usable host', () => {
    expect(normalizeHostname('not a hostname')).toBeNull();
    expect(normalizeHostname('file:///home/user/index.html')).toBeNull();
  });
});
