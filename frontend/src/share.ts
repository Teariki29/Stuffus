import type { OptimizeRequest } from "./types";

// Encode the *request* (not the result) in the URL hash. Re-opening the link
// reproduces the build by re-solving — deterministic for a given input.

function toBase64(s: string): string {
  // handle UTF-8 (accents) safely
  return btoa(unescape(encodeURIComponent(s)));
}
function fromBase64(s: string): string {
  return decodeURIComponent(escape(atob(s)));
}

export function buildShareUrl(req: OptimizeRequest): string {
  const payload = toBase64(JSON.stringify(req));
  const base = `${window.location.origin}${window.location.pathname}`;
  return `${base}#build=${payload}`;
}

export function readBuildFromHash(): OptimizeRequest | null {
  const m = window.location.hash.match(/build=([^&]+)/);
  if (!m) return null;
  try {
    const req = JSON.parse(fromBase64(m[1])) as OptimizeRequest;
    if (!req.stuff_type || !req.level) return null;
    return req;
  } catch {
    return null;
  }
}
