// Use window object to prevent SyntaxError on re-injection
window.THEMES = window.THEMES || {
  default: {
    name: "Default",
    bg: "hsl(198, 100%, 95%)",
    text: "hsl(198, 100%, 5%)",
    primary: "hsl(198, 100%, 50%)",
    border: "hsla(0, 0%, 50%, 0.25)"
  },
  dpr: {
    name: "Digital Pāli Reader",
    bg: "#FFFFDD",
    text: "hsl(198, 100%, 5%)",
    primary: "hsl(198, 100%, 50%)",
    border: "hsla(0, 0%, 50%, 0.25)",
    font: '"Noto Sans", sans-serif',
    bgImage: "dpr_imgbk.png"
  },
  suttacentral: {
    name: "SuttaCentral",
    bg: "#fff8f3", 
    text: "rgb(32, 27, 19)",
    primary: "#c68b05",
    accent: "#c68b05",
    border: "#e0e0e0",
    font: '"Skolar Sans PE Variable", sans-serif'
  }
};

window.detectTheme = window.detectTheme || function() {
  const url = window.location.href;
  if (url.includes("digitalpalireader.online")) return "dpr";
  if (url.includes("suttacentral.net")) return "suttacentral";
  return "auto"; 
};

window.extractColors = window.extractColors || function() {
  const bodyStyle = window.getComputedStyle(document.body);
  let bgColor = bodyStyle.backgroundColor;
  let el = document.body;
  while (bgColor === "rgba(0, 0, 0, 0)" || bgColor === "transparent") {
    if (!el.parentElement) { bgColor = "#ffffff"; break; }
    el = el.parentElement;
    bgColor = window.getComputedStyle(el).backgroundColor;
  }
  const link = document.querySelector('a');
  const primaryColor = link ? window.getComputedStyle(link).color : "hsl(198, 100%, 50%)";
  return {
    name: "Extracted",
    bg: bgColor, text: bodyStyle.color,
    primary: primaryColor, border: "hsla(0, 0%, 50%, 0.25)",
    font: bodyStyle.fontFamily
  };
};

window.applyTheme = window.applyTheme || function(themeKey) {
  let theme = window.THEMES[themeKey];
  if (themeKey === "auto") {
    const detected = window.detectTheme();
    theme = detected !== "auto" ? window.THEMES[detected] : window.extractColors();
  }
  if (!theme) theme = window.THEMES.default;

  const panelEl = document.getElementById("dict-panel-25445");
  if (panelEl) {
    panelEl.style.setProperty("--dpd-bg", theme.bg);
    panelEl.style.setProperty("--light", theme.bg);
    panelEl.style.setProperty("--dpd-text", theme.text);
    panelEl.style.setProperty("--dark", theme.text);
    panelEl.style.setProperty("--dpd-primary", theme.primary);
    panelEl.style.setProperty("--primary", theme.primary);
    panelEl.style.setProperty("--primary-alt", theme.primary);
    panelEl.style.setProperty("--primary-text", theme.primary);
    panelEl.style.setProperty("--dpd-border", theme.border);
    panelEl.style.setProperty("--gray", "#808080");
    panelEl.style.setProperty("--gray-light", "#808080");

    panelEl.style.setProperty("--dpd-accent", theme.accent || theme.primary);
    panelEl.style.setProperty("--dpd-bg-image", theme.bgImage ? `url(${chrome.runtime.getURL("images/" + theme.bgImage)})` : "none");
    
    panelEl.style.fontFamily = theme.font || '"Inter", "sans-serif"';
    if (!panelEl.style.fontSize) {
      panelEl.style.fontSize = window.getComputedStyle(document.body).fontSize;
    }

    panelEl.classList.remove("dpd-theme-suttacentral");
    panelEl.classList.remove("dpd-theme-dpr");
    if (themeKey === "suttacentral" || (themeKey === "auto" && window.detectTheme() === "suttacentral")) {
      panelEl.classList.add("dpd-theme-suttacentral");
      panelEl.style.setProperty("--dpd-header-text", "rgb(124, 118, 111)");
    } else if (themeKey === "dpr" || (themeKey === "auto" && window.detectTheme() === "dpr")) {
      panelEl.classList.add("dpd-theme-dpr");
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    } else {
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    }
  }
};
