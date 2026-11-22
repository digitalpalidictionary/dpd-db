// The server folds a long variants table when the search asks for fold=1.
// This is the same toggle as the website's dpd.js, for the panel's own click handler.
export function toggleVariants(button: Element): void {
  const table = button.closest('.dpd')?.querySelector('table.variants');
  if (!table) return;
  const expand = button.getAttribute('aria-expanded') !== 'true';
  table.querySelectorAll('.variant-more').forEach((row) => {
    row.classList.toggle('hidden', !expand);
  });
  button.setAttribute('aria-expanded', expand ? 'true' : 'false');
  button.textContent = expand
    ? button.getAttribute('data-less')
    : button.getAttribute('data-more');
  if (!expand) {
    button.scrollIntoView({ block: 'nearest' });
  }
}
