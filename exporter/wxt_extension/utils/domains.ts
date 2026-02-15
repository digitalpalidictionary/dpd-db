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
