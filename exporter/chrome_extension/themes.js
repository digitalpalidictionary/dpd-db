const THEMES = {
  default: {
    name: "Default",
    bg: "hsl(198, 100%, 95%)",
    text: "hsl(198, 100%, 5%)",
    primary: "hsl(198, 100%, 50%)",
    border: "hsla(0, 0%, 50%, 0.25)"
  },
  dpr: {
    name: "Digital Pāli Reader",
    bg: "#f8f9fa",
    text: "#212529",
    primary: "#8b0000",
    border: "#dee2e6"
  },
  suttacentral: {
    name: "SuttaCentral",
    bg: "#fff8f3", 
    text: "rgb(32, 27, 19)",
    primary: "#c68b05", /* SC Orange for buttons */
    accent: "#c68b05",
    border: "#e0e0e0",
    font: '"Skolar Sans PE Variable", sans-serif'
  }
};

function detectTheme() {
  const url = window.location.href;
  if (url.includes("digitalpalireader.online")) {
    return "dpr";
  }
  if (url.includes("suttacentral.net")) {
    return "suttacentral";
  }
  return "auto"; // Default to auto detection or default theme
}

function extractColors() {
  const bodyStyle = window.getComputedStyle(document.body);
  let bgColor = bodyStyle.backgroundColor;
  let textColor = bodyStyle.color;
  const fontFamily = bodyStyle.fontFamily;

  // If background is transparent, try to find the actual background color
  let el = document.body;
  while (bgColor === "rgba(0, 0, 0, 0)" || bgColor === "transparent") {
    if (!el.parentElement) {
      bgColor = "#ffffff";
      break;
    }
    el = el.parentElement;
    bgColor = window.getComputedStyle(el).backgroundColor;
  }

  // Simple heuristic for primary color: look for links or prominent headers
  const link = document.querySelector('a');
  const primaryColor = link ? window.getComputedStyle(link).color : "hsl(198, 100%, 50%)";

  return {
    name: "Extracted",
    bg: bgColor,
    text: textColor,
    primary: primaryColor,
    border: "hsla(0, 0%, 50%, 0.25)",
    font: fontFamily
  };
}

function applyTheme(themeKey) {
  let theme = THEMES[themeKey];
  
  if (themeKey === "auto") {
    const detected = detectTheme();
    if (detected !== "auto") {
      theme = THEMES[detected];
    } else {
      // Fallback for unknown sites: Dynamic extraction
      theme = extractColors();
    }
  }

  if (!theme) theme = THEMES.default;

  const panel = document.getElementById("dict-panel-25445");
  if (panel) {
    // Apply CSS Variables for both the panel and the injected DPD content
    panel.style.setProperty("--dpd-bg", theme.bg);
    panel.style.setProperty("--light", theme.bg);
    
    panel.style.setProperty("--dpd-text", theme.text);
    panel.style.setProperty("--dark", theme.text);
    
    panel.style.setProperty("--dpd-primary", theme.primary);
    panel.style.setProperty("--primary", theme.primary);
    panel.style.setProperty("--primary-alt", theme.primary);
    
    panel.style.setProperty("--dpd-border", theme.border);

    // Accent handling
    if (theme.accent) {
      panel.style.setProperty("--dpd-accent", theme.accent);
      panel.style.setProperty("--primary-text", theme.accent);
    } else {
      panel.style.setProperty("--dpd-accent", theme.primary);
    }
    
    // Apply Font Family
    if (theme.font) {
      panel.style.fontFamily = theme.font;
    } else {
      panel.style.fontFamily = '"Inter", "sans-serif"';
    }

    // Dynamic Font Size
    const bodyFontSize = window.getComputedStyle(document.body).fontSize;
    panel.style.fontSize = bodyFontSize;

    // Apply Theme Class for specific overrides
    panel.className = ""; // Reset classes
    if (themeKey === "suttacentral" || (themeKey === "auto" && detectTheme() === "suttacentral")) {
      panel.classList.add("dpd-theme-suttacentral");
      panel.style.setProperty("--dpd-header-text", "rgb(124, 118, 111)");
    } else {
      panel.style.setProperty("--dpd-header-text", theme.text);
    }
  }
}
