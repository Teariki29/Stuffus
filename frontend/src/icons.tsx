import type { ReactElement } from "react";

// Compact inline SVG icons (no external asset dependency, themeable via color).
const PATHS: Record<string, ReactElement> = {
  heart: <path d="M12 21C12 21 3.5 14.3 3.5 8.8A4.3 4.3 0 0 1 12 6.2 4.3 4.3 0 0 1 20.5 8.8C20.5 14.3 12 21 12 21Z" />,
  star: <path d="M12 2.5l2.6 6.3 6.8.5-5.2 4.4 1.7 6.6L12 16.9 6.3 20.8l1.7-6.6L2.8 9.8l6.8-.5z" />,
  diamond: <path d="M12 2l9 10-9 10L3 12z" />,
  droplet: <path d="M12 2.5c0 0-7 7.6-7 12.2a7 7 0 0 0 14 0C19 10.1 12 2.5 12 2.5z" />,
  shield: <path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z" />,
  bolt: <path d="M13 2L4 14h6l-1 8 11-13h-7z" />,
  crosshair: (
    <>
      <circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M12 1v5M12 18v5M1 12h5M18 12h5" stroke="currentColor" strokeWidth="2" />
    </>
  ),
  sparkle: <path d="M12 2l2 8 8 2-8 2-2 8-2-8-8-2 8-2z" />,
  cross: <path d="M9.5 3h5v6.5H21v5h-6.5V21h-5v-6.5H3v-5h6.5z" />,
  eye: (
    <>
      <path d="M12 5C5 5 2 12 2 12s3 7 10 7 10-7 10-7-3-7-10-7z" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  book: <path d="M5 3h11a3 3 0 0 1 3 3v15l-3-1.6L13 21V3H5zM4 5v15l1-.5V4.5z" />,
  burst: <path d="M12 2l2.2 5.1L20 6l-3.2 4.6L21 14l-5.6-.3L14 19l-2-4.7L8 19l-1.4-5.3L1 14l4.2-3.4L2 6l5.8 1.1z" />,
  fist: <path d="M6 9h9a3 3 0 0 1 3 3v3a4 4 0 0 1-4 4H9a3 3 0 0 1-3-3zM7 7V4h2v3zM10 7V3h2v4zM13 7V4h2v3z" />,
  skull: (
    <path d="M12 2a8 8 0 0 0-5 14v3h2v-2h2v2h2v-2h2v2h2v-3a8 8 0 0 0-5-14zM8.5 11a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm7 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z" />
  ),
  arrows: <path d="M12 2l4 4h-3v5h5V8l4 4-4 4v-3h-5v5h3l-4 4-4-4h3v-5H6v3l-4-4 4-4v3h5V6H8z" />,
  dot: <circle cx="12" cy="12" r="5" />,
  pods: <path d="M5 8h14l-1.2 12H6.2zM8 8V6a4 4 0 0 1 8 0v2h-2V6a2 2 0 0 0-4 0v2z" />,
  // element / characteristic shapes
  flame: (
    <path d="M12 2c2.4 3.2 5 5.3 5 9.2A5 5 0 0 1 7 11.4c0-1 .4-2 1.2-2.8-.1 1.3.6 2.4 1.6 2.6C10.6 8.4 12 6 12 2z" />
  ),
  waterdrop: <path d="M12 3c3 4 6 7.2 6 10.4a6 6 0 0 1-12 0C6 10.2 9 7 12 3z" />,
  wing: (
    <path d="M21 4c-8 .6-13.5 4.8-16 12.4l1.3 1c1.2-3 3.2-5.2 6.1-6.4-2.3 1.8-3.9 4-4.8 6.9l1.3 1C15 16.4 19 11.6 21 4z" />
  ),
  gem: <path d="M7 3h10l4 6-9 12L3 9zM7 3l2 6h6l2-6M3 9h18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />,
  clover: (
    <path d="M12 13c-1-2-2-3-4-3a3 3 0 1 0 0 6c0 2 1 3 4 3-1-2-1-3 0-6zm0 0c1-2 2-3 4-3a3 3 0 1 1 0 6c0 2-1 3-4 3 1-2 1-3 0-6z" />
  ),
  magnifier: (
    <path d="M10.5 3a7.5 7.5 0 0 1 5.9 12.1l4.3 4.3-1.4 1.4-4.3-4.3A7.5 7.5 0 1 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z" />
  ),
  link: (
    <path d="M9 7h2v2H9a3 3 0 0 0 0 6h2v2H9A5 5 0 0 1 9 7zm6 0h-2v2h2a3 3 0 0 1 0 6h-2v2h2a5 5 0 0 0 0-10zM8 11h8v2H8z" />
  ),
};

// Real Dofus icons, if the user drops PNGs in src/assets/icons/. Auto-detected
// at build time — no file means the SVG fallback below is used, so the app
// keeps working with zero icons present.
const REAL_ICONS = import.meta.glob("./assets/icons/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

const REAL_BY_NAME: Record<string, string> = {};
for (const [path, url] of Object.entries(REAL_ICONS)) {
  const base = path.split("/").pop()!.replace(/\.png$/, "");
  REAL_BY_NAME[base] = url;
}

/** Filename (without extension) expected in src/assets/icons/ for a given dim. */
export function iconFile(dim: string): string {
  // flat and % resistances share the same element shield icon
  return dim.startsWith("res_fixe_") ? dim.replace("res_fixe_", "res_") : dim;
}

export function Icon({
  name,
  color,
  file,
}: {
  name: string;
  color?: string;
  file?: string;
}) {
  const real = file ? REAL_BY_NAME[file] : undefined;
  if (real) {
    return <img className="stat-icon stat-icon-img" src={real} alt="" aria-hidden />;
  }
  const path = PATHS[name] ?? PATHS.dot;
  return (
    <svg
      className="stat-icon"
      viewBox="0 0 24 24"
      width="14"
      height="14"
      fill="currentColor"
      style={color ? { color } : undefined}
      aria-hidden
    >
      {path}
    </svg>
  );
}
