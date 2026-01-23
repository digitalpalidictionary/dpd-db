// Use window object to prevent SyntaxError on re-injection
window.parseColorToHSL = window.parseColorToHSL || function(colorStr) {
  const tempEl = document.createElement('div');
  tempEl.style.color = colorStr;
  document.body.appendChild(tempEl);
  const computed = window.getComputedStyle(tempEl).color;
  document.body.removeChild(tempEl);

  const rgbMatch = computed.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/);
  if (!rgbMatch) return { h: 198, s: 100, l: 50 };

  let r = parseInt(rgbMatch[1]) / 255;
  let g = parseInt(rgbMatch[2]) / 255;
  let b = parseInt(rgbMatch[3]) / 255;

  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }

  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
};

window.hslString = window.hslString || function(h, s, l, a = null) {
  return a !== null ? `hsla(${h}, ${s}%, ${l}%, ${a})` : `hsl(${h}, ${s}%, ${l}%)`;
};

window.adjustForButton = window.adjustForButton || function(hsl) {
  return window.hslString((hsl.h + 7) % 360, hsl.s, Math.max(0, hsl.l - 10));
};

window.adjustForText = window.adjustForText || function(hsl) {
  return window.hslString((hsl.h + 7) % 360, Math.max(0, hsl.s - 21), Math.max(0, hsl.l - 2));
};

window.adjustForLogo = window.adjustForLogo || function(targetHsl) {
  const originalHue = 198;
  const originalSat = 100;
  const originalLight = 50;

  let hueDiff = targetHsl.h - originalHue;
  if (hueDiff > 180) hueDiff -= 360;
  if (hueDiff < -180) hueDiff += 360;

  const satRatio = Math.max(0.3, Math.min(1.5, targetHsl.s / originalSat));
  const lightRatio = Math.max(0.5, Math.min(1.5, targetHsl.l / originalLight));

  return {
    hueRotate: hueDiff,
    saturate: satRatio,
    brightness: lightRatio
  };
};

window.getContrastText = window.getContrastText || function(colorInput) {
  console.log("[DPD] getContrastText INPUT:", colorInput, "type:", typeof colorInput);

  // Helper function to parse any color to RGB values
  const parseColorToRGB = (color) => {
    // Create a temporary element to get computed RGB values
    const tempEl = document.createElement('div');
    tempEl.style.color = color;
    document.body.appendChild(tempEl);
    const computed = window.getComputedStyle(tempEl).color;
    document.body.removeChild(tempEl);

    // Parse the computed color (should be in rgb() or rgba() format)
    const rgbMatch = computed.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/);
    if (rgbMatch) {
      return [
        parseInt(rgbMatch[1]),
        parseInt(rgbMatch[2]),
        parseInt(rgbMatch[3])
      ];
    }
    return [255, 255, 255]; // Default to white if parsing fails
  };

  // Convert any color input to RGB first
  const [r, g, b] = parseColorToRGB(colorInput);
  console.log("[DPD] Parsed RGB:", [r, g, b]);

  // Special case: if all RGB values are very low, return white text immediately
  // This handles cases like pure black (0,0,0) or near-black colors
  if (r < 30 && g < 30 && b < 30) {
    console.log("[DPD] Very dark color detected, returning white text");
    return '#ffffff';
  }

  // Calculate luminance using the standard formula
  const luminance = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);

  // For very dark colors, ensure we get light text
  // Use a lower threshold to ensure better contrast on dark backgrounds
  const result = luminance > 0.35 ? '#000000' : '#ffffff';  // Even lower threshold

  console.log("[DPD] Color:", colorInput, "Luminance:", luminance.toFixed(3), "->", result);
  return result;
};

window.generateFreqColors = window.generateFreqColors || function(hsl) {
  const freqColors = {};
  for (let i = 0; i <= 10; i++) {
    const opacity = i === 10 ? 1 : i / 10;
    freqColors[`--freq${i}`] = window.hslString(hsl.h, hsl.s, 50, opacity);
  }
  return freqColors;
};

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
    bgImage: "dpr_imgbk.png",
    niggahita: false
  },
  suttacentral: {
    name: "SuttaCentral",
    bg: "#fff8f3",
    text: "rgb(32, 27, 19)",
    primary: "#c68b05",
    accent: "#c68b05",
    border: "#e0e0e0",
    font: '"Skolar Sans PE Variable", sans-serif',
    niggahita: true
  },
  suttacentral_dark: {
    name: "SuttaCentral Dark",
    bg: "#414141",
    text: "#cccccc",
    primary: "#c68b05",
    accent: "#c68b05",
    border: "#666666",
    font: '"Skolar Sans PE Variable", sans-serif',
    niggahita: true
  },
  tbw_light: {
    name: "The Buddha's Words",
    bg: "#ffffff",
    text: "#000000",
    primary: "hsl(198, 100%, 50%)",
    border: "hsla(0, 0%, 50%, 0.25)",
    font: "URWPalladioITU, serif",
    niggahita: true
  },
  tbw_dark: {
    name: "The Buddha's Words Dark",
    bg: "#141516",
    text: "#ffffff",
    primary: "hsl(198, 100%, 50%)",
    border: "hsla(0, 0%, 50%, 0.25)",
    font: "URWPalladioITU, serif",
    niggahita: true
  },
  vri: {
    name: "Vipassana Research Institute",
    bg: "#ffffff",
    text: "#4f4d47",
    primary: "#b78730",
    border: "#dddddd",
    font: "'Maitree', 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif",
    fontSize: "16px",
    niggahita: false
  }
};

window.detectTheme = window.detectTheme || function() {
  const url = window.location.href;
  if (url.includes("digitalpalireader.online")) return "dpr";
  if (url.includes("suttacentral.net")) {
    return window.isSuttaCentralDark() ? "suttacentral_dark" : "suttacentral";
  }
  if (url.includes("thebuddhaswords")) {
    return window.isTBWDark() ? "tbw_dark" : "tbw_light";
  }
  if (url.includes("tipitaka.org")) return "vri";
  if (url.includes("open.tipitaka.lk")) {
    console.log("[DPD] Detected Tipitaka.lk");
    return "tipitakalk";
  }
  return "auto";
};

window.isSuttaCentralDark = window.isSuttaCentralDark || function() {
  const bg = window.getComputedStyle(document.body).backgroundColor;
  const rgb = bg.match(/\d+/g);
  if (rgb && rgb.length >= 3) {
    // Calculate perceived brightness (standard formula)
    const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
    return brightness < 128; // Return true if dark
  }
  return false;
};

window.isTBWDark = window.isTBWDark || function() {
  // Check body background
  let bg = window.getComputedStyle(document.body).backgroundColor;
  
  // If transparent, try to find a non-transparent ancestor or check HTML element
  if (bg === "rgba(0, 0, 0, 0)" || bg === "transparent") {
    bg = window.getComputedStyle(document.documentElement).backgroundColor;
  }
  
  // If still transparent, default to light (false) to be safe, 
  // or check if there is a specific class like "dark-mode" if known.
  // For now, let's assume if we can't find a color, it's likely light.
  if (bg === "rgba(0, 0, 0, 0)" || bg === "transparent") return false;

  const rgb = bg.match(/\d+/g);
  if (rgb && rgb.length >= 3) {
    const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
    // Dark if brightness < 100 (conservative)
    return brightness < 100; 
  }
  return false;
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
    primary: primaryColor,
    border: "hsla(0, 0%, 50%, 0.25)",
    font: bodyStyle.fontFamily
  };
};

window.extractTipitakaLkTheme = window.extractTipitakaLkTheme || function() {
  let bgColor = "#ffffff";
  let textColor = "hsl(198, 100%, 5%)";
  let fontSize = "16px";
  let fontFamily = '"Inter", "sans-serif"';
  let primaryColor = "hsl(198, 100%, 50%)";

  const bgEl = document.querySelector('.flex.flex-col.h-screen.overflow-y-hidden.bg-bg.text-text');
  if (bgEl) {
    const bgStyle = window.getComputedStyle(bgEl);
    bgColor = bgStyle.backgroundColor;
  }

  const textEl = document.querySelector('.ml-2.group-hover\\:text-primary');
  if (textEl) {
    const textStyle = window.getComputedStyle(textEl);
    textColor = textStyle.color;
    fontSize = textStyle.fontSize;
    fontFamily = textStyle.fontFamily;
  }

  const primaryEl = document.querySelector('.px-4.py-1.flex.justify-between.items-center.bg-primary.text-white');
  if (primaryEl) {
    const primaryStyle = window.getComputedStyle(primaryEl);
    primaryColor = primaryStyle.backgroundColor;
    console.log("[DPD] Tipitaka.lk primary color:", primaryColor);
  } else {
    console.log("[DPD] Primary element not found on Tipitaka.lk");
  }

  return {
    name: "Tipitaka.lk",
    bg: bgColor,
    text: textColor,
    primary: primaryColor,
    border: "hsla(0, 0%, 50%, 0.25)",
    font: fontFamily,
    fontSize: fontSize
  };
};

window.applyTheme = window.applyTheme || function(themeKey) {
  let theme = window.THEMES[themeKey];
  if (themeKey === "auto") {
    const detected = window.detectTheme();
    if (detected === "tipitakalk") {
      theme = window.extractTipitakaLkTheme();
    } else {
      theme = detected !== "auto" ? window.THEMES[detected] : window.extractColors();
    }
  } else if (themeKey === "tipitakalk") {
    theme = window.extractTipitakaLkTheme();
  }
  if (!theme) theme = window.THEMES.default;

  const panelEl = document.getElementById("dict-panel-25445");
  if (panelEl) {
    const primaryHsl = window.parseColorToHSL(theme.primary);
    const primaryStr = window.hslString(primaryHsl.h, primaryHsl.s, primaryHsl.l);
    const primaryAltHsl = window.adjustForButton(primaryHsl);
    const primaryAltStr = typeof primaryAltHsl === 'string' ? primaryAltHsl : window.hslString(primaryAltHsl.h, primaryAltHsl.s, primaryAltHsl.l);
    const primaryTextHsl = window.adjustForText(primaryHsl);
    const primaryTextStr = typeof primaryTextHsl === 'string' ? primaryTextHsl : window.hslString(primaryTextHsl.h, primaryTextHsl.s, primaryTextHsl.l);

    panelEl.style.setProperty("--dpd-bg", theme.bg);
    panelEl.style.setProperty("--light", theme.bg);
    panelEl.style.setProperty("--dpd-text", theme.text);
    panelEl.style.setProperty("--dark", theme.text);
    panelEl.style.setProperty("--dpd-primary", primaryStr);
    panelEl.style.setProperty("--primary", primaryStr);
    panelEl.style.setProperty("--primary-alt", primaryAltStr);
    panelEl.style.setProperty("--primary-text", primaryTextStr);
    panelEl.style.setProperty("--dpd-border", theme.border);
    panelEl.style.setProperty("--gray", theme.gray || "#808080");
    panelEl.style.setProperty("--gray-light", theme.gray || "#808080");

    const logoFilters = window.adjustForLogo(primaryHsl);
    console.log("[DPD] Theme primary:", primaryStr, "Logo filters:", logoFilters);
    panelEl.style.setProperty("--dpd-logo-hue-rotate", `${logoFilters.hueRotate}deg`);
    panelEl.style.setProperty("--dpd-logo-saturate", logoFilters.saturate);
    panelEl.style.setProperty("--dpd-logo-brightness", logoFilters.brightness);

    console.log("[DPD] Calculating contrast for primary-alt:", primaryAltStr);
    const altTextColor = window.getContrastText(primaryAltStr);
    console.log("[DPD] Resulting button text color:", altTextColor);
    panelEl.style.setProperty("--dpd-button-text", altTextColor);

    if (themeKey !== "default") {
      const freqColors = window.generateFreqColors(primaryHsl);
      Object.entries(freqColors).forEach(([key, value]) => {
        panelEl.style.setProperty(key, value);
      });
    }

    panelEl.style.setProperty("--dpd-accent", theme.accent || theme.primary);
    panelEl.style.setProperty("--dpd-bg-image", theme.bgImage ? `url(${chrome.runtime.getURL("images/" + theme.bgImage)})` : "none");

    panelEl.style.fontFamily = theme.font || '"Inter", "sans-serif"';
    if (theme.fontSize) {
      panelEl.style.fontSize = theme.fontSize;
    } else if (!panelEl.style.fontSize) {
      panelEl.style.fontSize = window.getComputedStyle(document.body).fontSize;
    }

    panelEl.style.setProperty("--dpd-title-size", "100%");
    panelEl.style.setProperty("--dpd-title-padding", "10px");

    panelEl.classList.remove("dpd-theme-suttacentral");
    panelEl.classList.remove("dpd-theme-dpr");
    panelEl.classList.remove("dpd-theme-vri");

    if (theme.niggahita !== undefined && window.panel) {
      window.panel.settings.niggahita = theme.niggahita;
    }

    const isSC = themeKey === "suttacentral" || themeKey === "suttacentral_dark" || 
                 (themeKey === "auto" && (window.detectTheme() === "suttacentral" || window.detectTheme() === "suttacentral_dark"));

    if (isSC) {
      panelEl.classList.add("dpd-theme-suttacentral");
      if (themeKey === "suttacentral_dark" || (themeKey === "auto" && window.detectTheme() === "suttacentral_dark")) {
        panelEl.style.setProperty("--dpd-header-text", "#cccccc");
      } else {
        panelEl.style.setProperty("--dpd-header-text", "rgb(124, 118, 111)");
      }
    } else if (themeKey === "dpr" || (themeKey === "auto" && window.detectTheme() === "dpr")) {
      panelEl.classList.add("dpd-theme-dpr");
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    } else if (themeKey === "vri" || (themeKey === "auto" && window.detectTheme() === "vri")) {
      panelEl.classList.add("dpd-theme-vri");
      panelEl.style.setProperty("--dpd-header-bg", theme.bg);
      panelEl.style.setProperty("--dpd-header-text", theme.primary);
    } else {
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    }
  }
};
