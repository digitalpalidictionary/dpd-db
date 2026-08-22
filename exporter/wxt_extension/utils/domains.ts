export const AUTO_DOMAINS = [
  "suttacentral.net",
  "suttacentral.express",
  "suttacentral.now",
  "digitalpalireader.online",
  "thebuddhaswords.net",
  "tipitaka.org",
  "tipitaka.lk",
  "open.tipitaka.lk",
  "tipitaka.paauksociety.org",
  "s.4nt.org",
];

export const EXCLUDE_DOMAINS = [
  "discourse.suttacentral.net",
];

export function isAutoDomain(hostname: string): boolean {
  return AUTO_DOMAINS.some((d) => hostname === d || hostname.endsWith('.' + d));
}

export function isExcludedDomain(hostname: string): boolean {
  return EXCLUDE_DOMAINS.some((d) => hostname === d || hostname.endsWith('.' + d));
}

// True for the built-in sites that run without the user enabling anything.
// They are managed by the toolbar icon, never listed as user-added sites.
export function isDefaultOnDomain(hostname: string): boolean {
  return !isExcludedDomain(hostname) && isAutoDomain(hostname);
}

// Per-site on/off state is keyed by hostname alone, so user-typed input must be
// reduced to a bare hostname before it can address the same entry a toolbar
// click writes. Accepts a full URL, a host:port, or a bare name.
// Returns null for anything that does not yield a usable hostname.
export function normalizeHostname(input: string): string | null {
  const trimmed = input.trim().toLowerCase();
  if (!trimmed) return null;

  const hasScheme = /^[a-z][a-z0-9+.-]*:\/\//.test(trimmed);
  let hostname: string;
  try {
    hostname = new URL(hasScheme ? trimmed : `http://${trimmed}`).hostname;
  } catch {
    return null;
  }

  // A scheme without an authority (file:///path) parses but yields no host.
  if (!hostname) return null;

  // The URL parser percent-encodes rather than rejecting some junk, so check the
  // result is plausible. Brackets and colons allow IPv6 literals through, and
  // underscores are accepted because browsers report them in location.hostname
  // for intranet and container hosts.
  if (!/^[a-z0-9._\-[\]:]+$/.test(hostname)) return null;

  // A fully-qualified trailing dot survives URL parsing but never appears in
  // window.location.hostname, so keeping it would store an entry that can never
  // match the site it was meant for.
  return hostname.endsWith('.') ? hostname.slice(0, -1) || null : hostname;
}
