import { browser } from 'wxt/browser';

let cachedBaseUrl: string | null = null;
let lastCheckTime: number = 0;
const CACHE_TTL = 60000; // 1 minute

export async function getApiBaseUrl(): Promise<string> {
  // If we are in a content script, always ask the background script for the base URL.
  // This ensures background and content scripts are perfectly in sync.
  if (typeof window !== 'undefined' && window.document) {
    try {
      const response = await browser.runtime.sendMessage({ action: "getApiBaseUrl" }) as any;
      console.log("[DPD] Content script received response:", response);
      if (response && response.baseUrl) {
        return response.baseUrl;
      }
    } catch (e) {
      console.error("[DPD] Failed to get base URL from background, error:", e);
      console.warn("[DPD] Falling back to production due to communication failure.");
      return "https://dpdict.net";
    }
    console.warn("[DPD] No baseUrl in response, falling back to production.");
    return "https://dpdict.net";
  }

  // Logic for background script detection
  const now = Date.now();
  if (cachedBaseUrl && (now - lastCheckTime < CACHE_TTL)) {
    return cachedBaseUrl;
  }

  const localUrls = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.1.1.1:8080",
    "http://0.0.0.0:8080"
  ];

  for (const url of localUrls) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 150); // Slightly longer timeout
      
      // Use GET on root path to avoid 405 Method Not Allowed
      const response = await fetch(`${url}/`, { 
        method: 'GET', 
        signal: controller.signal 
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok || response.status === 404 || response.status === 405) {
        console.log(`[DPD] Local server detected at ${url}`);
        cachedBaseUrl = url;
        lastCheckTime = now;
        return url;
      } else {
        console.log(`[DPD] Server at ${url} responded with status: ${response.status}`);
      }
    } catch (e) {
      console.log(`[DPD] Failed to connect to ${url}:`, e.message);
    }
  }

  cachedBaseUrl = "https://dpdict.net";
  lastCheckTime = now;
  return cachedBaseUrl;
}

export async function fetchFromApi(endpoint: string): Promise<any> {
  const baseUrl = await getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (e: any) {
    console.error(`[DPD] API fetch error (${url}):`, e);
    throw e;
  }
}

export async function getAudioUrl(headword: string, gender: string): Promise<string> {
  const baseUrl = await getApiBaseUrl();
  return `${baseUrl}/audio/${encodeURIComponent(headword)}?gender=${gender}`;
}
