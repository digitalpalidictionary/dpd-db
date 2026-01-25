import { Browser } from 'webextension-polyfill';

declare module "wxt/browser" {
    export interface WxtBrowser extends Browser {}
}

export interface Settings {
    fontSize: number;
    niggahita: boolean;
    grammar: boolean;
    example: boolean;
    oneButton: boolean;
    summary: boolean;
    sandhi: boolean;
    audio: boolean;
}

export interface Theme {
    name: string;
    bg: string;
    text: string;
    primary: string;
    border: string;
    gray?: string;
    accent?: string;
    font?: string;
    fontSize?: string;
    bgImage?: string;
    niggahita?: boolean;
}

export interface Themes {
    [key: string]: Theme;
}

export interface MessageRequest {
    action: string;
    url?: string;
    text?: string;
}

export interface MessageResponse {
    success: boolean;
    data?: any;
    error?: string;
}

export interface HSL {
    h: number;
    s: number;
    l: number;
}

export interface LogoFilters {
    hueRotate: number;
    saturate: number;
    brightness: number;
}

// Global window extensions
declare global {
    interface Window {
        DictionaryPanel: new () => any;
        panel: any;
        handleSelectedWord: (word: string) => void;
        expandSelectionToWord: () => void;
        getSelectedWord: () => string | null;
        
        // Theme functions
        parseColorToHSL: (colorStr: string) => HSL;
        hslString: (h: number, s: number, l: number, a?: number | null) => string;
        adjustForButton: (hsl: HSL) => string;
        adjustForText: (hsl: HSL) => string;
        adjustForLogo: (targetHsl: HSL) => LogoFilters;
        getContrastText: (colorInput: string) => string;
        generateFreqColors: (hsl: HSL) => { [key: string]: string };
        detectTheme: () => string;
        applyTheme: (themeKey: string) => void;
        isDark: () => boolean;
        isSuttaCentralDark: () => boolean;
        isTBWDark: () => boolean;
        extractColors: () => Theme;
        extractTipitakaLkTheme: () => Theme;
        THEMES: Themes;
        
        // Helper functions
        wrapApostrophesInHTML: (html: string) => string;
        niggahitaUp: () => void;
        niggahitaDown: () => void;
        
        // Event handlers
        handleMouseDown: (e: MouseEvent) => void;
        handleMouseUp: (e: MouseEvent) => void;
        handleDblClick: (e: MouseEvent) => void;
        addListenersToTextElements: () => void;
        removeListenersFromTextElements: () => void;
    }
}
