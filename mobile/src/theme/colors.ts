/** Shared colour palette so every screen looks consistent. */
export const colors = {
  bg: "#0b1120",
  card: "#111a2e",
  border: "#1f2a44",
  text: "#e5e7eb",
  muted: "#94a3b8",
  accent: "#38bdf8",
  safe: "#22c55e",
  suspicious: "#f59e0b",
  dangerous: "#ef4444",
};

export type Verdict = "safe" | "suspicious" | "dangerous";

export const verdictColor = (v: Verdict): string => colors[v];
