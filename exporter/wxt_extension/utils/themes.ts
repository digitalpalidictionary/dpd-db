import { Theme, Themes, HSL, LogoFilters } from '../types/extension';
import { browser } from 'wxt/browser';

// Use window object to prevent SyntaxError on re-injection if needed
// But in WXT module context, we can just export functions.

export function parseColorToHSL(colorStr: string): HSL {
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
  let h = 0, s = 0, l = (max + min) / 2;

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
}

export function hslString(h: number, s: number, l: number, a: number | null = null): string {
  return a !== null ? `hsla(${h}, ${s}%, ${l}%, ${a})` : `hsl(${h}, ${s}%, ${l}%)`;
}

export function adjustForButton(hsl: HSL): string {
  return hslString((hsl.h + 7) % 360, hsl.s, Math.max(0, hsl.l - 10));
}

export function adjustForText(hsl: HSL): string {
  return hslString((hsl.h + 7) % 360, Math.max(0, hsl.s - 21), Math.max(0, hsl.l - 2));
}

export function adjustForLogo(targetHsl: HSL): LogoFilters {
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
}

export function getContrastText(colorInput: string): string {
  // Helper function to parse any color to RGB values
  const parseColorToRGB = (color: string): [number, number, number] => {
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

  // Special case: if all RGB values are very low, return white text immediately
  if (r < 30 && g < 30 && b < 30) {
    return '#ffffff';
  }

  // Calculate luminance using the standard formula
  const luminance = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);

  // For very dark colors, ensure we get light text
  return luminance > 0.35 ? '#000000' : '#ffffff';
}

export function generateFreqColors(hsl: HSL): { [key: string]: string } {
  const freqColors: { [key: string]: string } = {};
  for (let i = 0; i <= 10; i++) {
    const opacity = i === 10 ? 1 : i / 10;
    freqColors[`--freq${i}`] = hslString(hsl.h, hsl.s, 50, opacity);
  }
  return freqColors;
}

export const THEMES: Themes = {
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
    font: "\"Noto Sans\", sans-serif",
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
    font: "\"Skolar Sans PE Variable\", sans-serif",
    niggahita: true
  },
  suttacentral_dark: {
    name: "SuttaCentral Dark",
    bg: "#414141",
    text: "#cccccc",
    primary: "#c68b05",
    accent: "#c68b05",
    border: "#666666",
    font: "\"Skolar Sans PE Variable\", sans-serif",
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

export function isDark(): boolean {
  const html = document.documentElement;
  const body = document.body;

  if (html.classList.contains('dark') || 
      html.classList.contains('dark-theme') ||
      body.classList.contains('dark') ||
      body.classList.contains('dark-theme') ||
      html.getAttribute('data-theme') === 'dark' ||
      html.getAttribute('theme') === 'dark' ||
      body.getAttribute('data-theme') === 'dark' ||
      body.getAttribute('theme') === 'dark') {
    return true;
  }

  let bg = window.getComputedStyle(body).backgroundColor;
  if (bg === "rgba(0, 0, 0, 0)" || bg === "transparent") {
    bg = window.getComputedStyle(html).backgroundColor;
  }
  
  if (bg === "rgba(0, 0, 0, 0)" || bg === "transparent") return false;

  const rgb = bg.match(/\d+/g);
  if (rgb && rgb.length >= 3) {
    const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
    return brightness < 128; 
  }
  return false;
}

export function isSuttaCentralDark(): boolean {
  return isDark();
}

export function isTBWDark(): boolean {
  return isDark();
}

export function extractTipitakaLkTheme(): Theme {
  // Fallback to general color extraction as a base
  const theme = extractColors();
  theme.name = "Tipitaka.lk";
  theme.niggahita = false; // Tipitaka.lk usually uses ṃ

  // Try more specific Tailwind/Vuetify selectors for background
  const bgSelectors = [
    '.flex.flex-col.h-screen.overflow-y-hidden.bg-bg.text-text',
    '#app',
    '.v-application',
    '.bg-bg'
  ];
  
  for (const selector of bgSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      const style = window.getComputedStyle(el);
      const bg = style.backgroundColor;
      if (bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent") {
        theme.bg = bg;
        theme.text = style.color;
        break;
      }
    }
  }

  // Try to find the primary color more robustly
  const primarySelectors = [
    '.bg-primary',
    '.text-primary',
    '.v-toolbar',
    '.v-app-bar',
    'header',
    '.px-4.py-1.flex.justify-between.items-center.bg-primary.text-white'
  ];

  for (const selector of primarySelectors) {
    const el = document.querySelector(selector);
    if (el) {
      const style = window.getComputedStyle(el);
      // For background-color based elements
      let color = style.backgroundColor;
      if (!color || color === "rgba(0, 0, 0, 0)" || color === "transparent" || color === theme.bg) {
        // Try text color if background is invalid
        color = style.color;
      }
      
      if (color && color !== "rgba(0, 0, 0, 0)" && color !== "transparent" && color !== theme.bg && color !== theme.text) {
        theme.primary = color;
        break;
      }
    }
  }

  return theme;
}

export function extractColors(): Theme {
  const bodyStyle = window.getComputedStyle(document.body);
  let bgColor = bodyStyle.backgroundColor;
  let el = document.body;
  while (bgColor === "rgba(0, 0, 0, 0)" || bgColor === "transparent") {
    if (!el.parentElement) { bgColor = "#ffffff"; break; }
    el = el.parentElement;
    bgColor = window.getComputedStyle(el).backgroundColor;
  }
  const link = document.querySelector('a');
  let primaryColor = link ? window.getComputedStyle(link).color : "hsl(198, 100%, 50%)";

  // If the link color is basically grayscale, try to find a real primary color
  const isGrayscale = (color: string) => {
    const hsl = parseColorToHSL(color);
    return hsl.s < 10;
  };

  if (isGrayscale(primaryColor)) {
    const coloredEl = document.querySelector('.primary, .bg-primary, .text-primary, [class*="primary"], [class*="accent"]');
    if (coloredEl) {
      const style = window.getComputedStyle(coloredEl);
      const color = style.backgroundColor !== "rgba(0, 0, 0, 0)" ? style.backgroundColor : style.color;
      if (!isGrayscale(color)) primaryColor = color;
    }
  }

  return {
    name: "Extracted",
    bg: bgColor, text: bodyStyle.color,
    primary: primaryColor,
    border: "hsla(0, 0%, 50%, 0.25)",
    font: bodyStyle.fontFamily
  };
}

export function detectTheme(): string {
  const url = window.location.href;
  if (url.includes("digitalpalireader.online")) return "dpr";
  if (url.includes("suttacentral.net")) {
    return isSuttaCentralDark() ? "suttacentral_dark" : "suttacentral";
  }
  if (url.includes("thebuddhaswords")) {
    return isTBWDark() ? "tbw_dark" : "tbw_light";
  }
  if (url.includes("tipitaka.org")) return "vri";
  if (url.includes("tipitaka.lk")) {
    return "tipitakalk";
  }
  return "auto";
}

export function applyTheme(themeKey: string): void {
  let theme: Theme | undefined = THEMES[themeKey];
  if (themeKey === "auto") {
    const detected = detectTheme();
    if (detected === "tipitakalk") {
      theme = extractTipitakaLkTheme();
    } else {
      theme = detected !== "auto" ? THEMES[detected] : extractColors();
    }
  } else if (themeKey === "tipitakalk") {
    theme = extractTipitakaLkTheme();
  }
  if (!theme) theme = THEMES.default;

  const panelEl = document.getElementById("dict-panel-25445");
  if (panelEl) {
    const primaryHsl = parseColorToHSL(theme.primary);
    const primaryStr = hslString(primaryHsl.h, primaryHsl.s, primaryHsl.l);
    const primaryAltStr = adjustForButton(primaryHsl);
    const primaryTextStr = adjustForText(primaryHsl);

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

    const logoFilters = adjustForLogo(primaryHsl);
    panelEl.style.setProperty("--dpd-logo-hue-rotate", `${logoFilters.hueRotate}deg`);
    panelEl.style.setProperty("--dpd-logo-saturate", logoFilters.saturate.toString());
    panelEl.style.setProperty("--dpd-logo-brightness", logoFilters.brightness.toString());

    const altTextColor = getContrastText(primaryAltStr);
    panelEl.style.setProperty("--dpd-button-text", altTextColor);

    const tooltipTextColor = getContrastText(primaryStr);
    panelEl.style.setProperty("--dpd-tooltip-text-color", tooltipTextColor);

    if (themeKey !== "default") {
      const freqColors = generateFreqColors(primaryHsl);
      Object.entries(freqColors).forEach(([key, value]) => {
        panelEl.style.setProperty(key, value);
      });
    }

    panelEl.style.setProperty("--dpd-accent", theme.accent || theme.primary);
    
    // Handle bgImage
    if (theme.bgImage) {
      // WXT handles assets differently. If it's in public/ or assets/, we need the URL.
      // browser.runtime.getURL returns the correct path.
      // Assuming images are in public/ or accessible.
      // If we put dpr_imgbk.png in public/, getURL('dpr_imgbk.png') works.
      panelEl.style.setProperty("--dpd-bg-image", `url(${browser.runtime.getURL(theme.bgImage)})`);
    } else {
      panelEl.style.setProperty("--dpd-bg-image", "none");
    }

    panelEl.style.fontFamily = theme.font || "'Inter', 'sans-serif'";
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

    if (theme.niggahita !== undefined && window.panel && window.panel.settings) {
      window.panel.settings.niggahita = theme.niggahita;
      // Niggahita updates should happen in the panel logic, but we can call it if exposed
      if (typeof window.niggahitaUp === 'function' && typeof window.niggahitaDown === 'function') {
          if (theme.niggahita) window.niggahitaUp();
          else window.niggahitaDown();
      }
    }

    const isSC = themeKey === "suttacentral" || themeKey === "suttacentral_dark" || 
                 (themeKey === "auto" && (detectTheme() === "suttacentral" || detectTheme() === "suttacentral_dark"));

    if (isSC) {
      panelEl.classList.add("dpd-theme-suttacentral");
      if (themeKey === "suttacentral_dark" || (themeKey === "auto" && detectTheme() === "suttacentral_dark")) {
        panelEl.style.setProperty("--dpd-header-text", "#cccccc");
      } else {
        panelEl.style.setProperty("--dpd-header-text", "rgb(124, 118, 111)");
      }
    } else if (themeKey === "dpr" || (themeKey === "auto" && detectTheme() === "dpr")) {
      panelEl.classList.add("dpd-theme-dpr");
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    } else if (themeKey === "vri" || (themeKey === "auto" && detectTheme() === "vri")) {
      panelEl.classList.add("dpd-theme-vri");
      panelEl.style.setProperty("--dpd-header-bg", theme.bg);
      panelEl.style.setProperty("--dpd-header-text", theme.primary);
    } else {
      panelEl.style.setProperty("--dpd-header-text", theme.text);
    }
  }
}

// Attach to window for legacy compatibility
if (typeof window !== 'undefined') {
    window.parseColorToHSL = parseColorToHSL;
    window.hslString = hslString;
    window.adjustForButton = adjustForButton;
    window.adjustForText = adjustForText;
    window.adjustForLogo = adjustForLogo;
    window.getContrastText = getContrastText;
    window.generateFreqColors = generateFreqColors;
    window.THEMES = THEMES;
    window.detectTheme = detectTheme;
    window.isDark = isDark;
    window.isSuttaCentralDark = isSuttaCentralDark;
    window.isTBWDark = isTBWDark;
    window.extractColors = extractColors;
    window.extractTipitakaLkTheme = extractTipitakaLkTheme;
    window.applyTheme = applyTheme;
}
