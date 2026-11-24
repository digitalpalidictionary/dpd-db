/* Device filter for the Pāḷi Resources page.
 *
 * Progressive enhancement: without JavaScript every entry stays visible. With
 * it, a reader ticks the devices they own and only the entries that run on ALL
 * of those devices remain. A website (tagged "web") runs on every device, so
 * it satisfies any tick; the other tags are satisfied only by themselves.
 * Each entry's tags live in the `data-p` attribute of its `.res` div.
 * Ticking "Recommended" keeps only the entries that carry a `data-rec`
 * attribute, on top of whatever devices are ticked.
 * The selection lives in the URL as ?devices=linux,android so it can be linked.
 *
 * Material's instant navigation swaps pages without a full load, so the work
 * runs on every `document$` emission and bails out on pages without the panel.
 */

const DEVICES = {
  web: "Web",
  windows: "Windows",
  mac: "Mac",
  linux: "Linux",
  ios: "iPhone & iPad",
  android: "Android",
  rec: "Recommended",
};

// Material wraps the page in <div class="md-content"><article>; the headings
// and entries are children of the article, not of the div.
function pageContent(form) {
  return form.closest(".md-content__inner") ?? form.closest(".md-content");
}

function selectedDevices(form) {
  return Array.from(form.querySelectorAll("input[type=checkbox]:checked")).map(
    (input) => input.value,
  );
}

function platformBadges(tags) {
  const wrap = document.createElement("span");
  wrap.className = "res-p";
  for (const tag of tags) {
    const badge = document.createElement("span");
    badge.className = "res-p-badge";
    badge.textContent = DEVICES[tag] ?? tag;
    wrap.appendChild(badge);
  }
  return wrap;
}

function listOfNames(devices) {
  const names = devices.map((device) => DEVICES[device]);
  if (names.length <= 1) return names.join("");
  return names.slice(0, -1).join(", ") + " and " + names.at(-1);
}

// A section is an <h2> plus everything up to the next <h2>.
function sectionsOf(article) {
  const sections = [];
  let section = null;
  for (const node of Array.from(article.children)) {
    if (node.tagName === "H2") {
      section = { heading: node, nodes: [node] };
      sections.push(section);
    } else if (section) {
      section.nodes.push(node);
    }
  }
  return sections;
}

// true when the entry itself is made for every ticked device, rather than
// reaching them only through a website
function runsNatively(entry, platforms) {
  if (platforms.length === 0) return false;
  const tags = entry.dataset.p.split(/\s+/);
  return platforms.every((device) => tags.includes(device));
}

// List entries for the ticked devices first, each group in its authored order.
// Every entry keeps its own slot, so any paragraph between entries stays put.
function floatNative(article, platforms) {
  for (const section of sectionsOf(article)) {
    const entries = section.nodes.filter((node) => node.matches(".res"));
    if (entries.length < 2) continue;

    const sorted = entries.slice().sort((a, b) => {
      const rankA = runsNatively(a, platforms) ? 0 : 1;
      const rankB = runsNatively(b, platforms) ? 0 : 1;
      if (rankA !== rankB) return rankA - rankB;
      return Number(a.dataset.order) - Number(b.dataset.order);
    });
    if (sorted.every((entry, i) => entry === entries[i])) continue;

    const markers = entries.map((entry) => {
      const marker = document.createComment("");
      entry.parentNode.insertBefore(marker, entry);
      return marker;
    });
    sorted.forEach((entry, i) => {
      markers[i].parentNode.insertBefore(entry, markers[i]);
    });
    for (const marker of markers) marker.remove();
  }
}

function applyFilter(form) {
  const article = pageContent(form);
  const status = form.querySelector(".dpd-filter-status");
  const entries = Array.from(article.querySelectorAll(".res"));
  const devices = selectedDevices(form);
  const recommendedOnly = devices.includes("rec");
  const platforms = devices.filter((device) => device !== "rec");

  let shown = 0;
  for (const entry of entries) {
    const tags = entry.dataset.p.split(/\s+/);
    const isWebsite = tags.includes("web");
    const runsOnDevices = platforms.every(
      (device) => tags.includes(device) || isWebsite,
    );
    const matches = recommendedOnly
      ? runsOnDevices && entry.hasAttribute("data-rec")
      : runsOnDevices;
    entry.hidden = !matches;
    if (matches) shown += 1;
  }

  // Hide a section whose entries were all filtered out. Text outside any
  // section stays.
  floatNative(article, platforms);
  const tocLinks = Array.from(
    document.querySelectorAll(".md-sidebar--secondary a.md-nav__link"),
  );
  for (const section of sectionsOf(article)) {
    const sectionEntries = section.nodes.filter((node) =>
      node.matches(".res"),
    );
    const hide =
      sectionEntries.length > 0 && sectionEntries.every((e) => e.hidden);
    // only the heading and the text between entries; entries keep their own state
    for (const node of section.nodes) {
      if (!node.matches(".res")) node.hidden = hide;
    }
    // the page contents list on the right links to each section; its hrefs are
    // absolute, so compare the hash
    const id = section.nodes[0].id;
    const link = tocLinks.find((a) => a.hash === `#${id}`);
    if (link) link.closest("li").hidden = hide;
  }

  if (status) {
    // "work on Linux and Android and are recommended", "is recommended", …
    const singular = shown === 1;
    const need = [];
    if (platforms.length > 0) {
      need.push(`${singular ? "works" : "work"} on ${listOfNames(platforms)}`);
    }
    if (recommendedOnly) {
      need.push(`${singular ? "is" : "are"} recommended`);
    }
    const requirement = need.join(" and ");
    if (devices.length === 0) {
      status.textContent = `Showing all ${entries.length} resources.`;
    } else if (shown === 0) {
      status.textContent = `No resource ${requirement}. Tick fewer boxes.`;
    } else {
      status.textContent = `${shown} of ${entries.length} resources ${requirement}.`;
    }
  }

  return devices;
}

function writeUrl(devices) {
  const url = new URL(window.location.href);
  if (devices.length === 0) url.searchParams.delete("devices");
  else url.searchParams.set("devices", devices.join(","));
  window.history.replaceState(null, "", url);
}

function readUrl(form) {
  const raw = new URLSearchParams(window.location.search).get("devices");
  const wanted = raw ? raw.split(",") : [];
  for (const input of form.querySelectorAll("input[type=checkbox]")) {
    input.checked = wanted.includes(input.value);
  }
}

function init() {
  const form = document.querySelector("[data-dpd-filter]");
  if (!form || form.dataset.dpdReady) return;
  form.dataset.dpdReady = "1";

  const content = pageContent(form);
  Array.from(content.querySelectorAll(".res")).forEach((entry, i) => {
    entry.dataset.order ??= String(i);
  });

  for (const entry of content.querySelectorAll(".res")) {
    const lastParagraph = entry.querySelector("p:last-of-type");
    if (lastParagraph) {
      lastParagraph.appendChild(platformBadges(entry.dataset.p.split(/\s+/)));
    }
  }

  const onChange = () => writeUrl(applyFilter(form));
  form.addEventListener("change", onChange);
  const clear = form.querySelector("[data-dpd-clear]");
  if (clear) {
    clear.addEventListener("click", () => {
      for (const input of form.querySelectorAll("input[type=checkbox]")) {
        input.checked = false;
      }
      onChange();
    });
  }

  readUrl(form);
  applyFilter(form);
}

if (typeof document$ !== "undefined") {
  document$.subscribe(() => init());
} else {
  document.addEventListener("DOMContentLoaded", init);
}
