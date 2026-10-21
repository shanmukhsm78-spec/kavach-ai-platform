"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Accent = {
  title: string;
  hover: string;
  dot: string;
};

const accents: Record<string, Accent> = {
  rose: { title: "text-rose-400", hover: "hover:border-rose-500", dot: "bg-rose-400" },
  emerald: { title: "text-emerald-400", hover: "hover:border-emerald-500", dot: "bg-emerald-400" },
  sky: { title: "text-sky-400", hover: "hover:border-sky-500", dot: "bg-sky-400" },
};

type Status = "checking" | "online" | "offline";

/**
 * A mode card for the landing dashboard. It links to the mode page and shows a
 * live status pill that pings the backend's per-mode status route (e.g.
 * /attack/status). Falls back to "offline" if the backend isn't running.
 */
export default function ModeCard({
  href,
  title,
  tagline,
  accent,
  statusPath,
}: {
  href: string;
  title: string;
  tagline: string;
  accent: string;
  statusPath: string;
}) {
  const a = accents[accent] ?? accents.emerald;
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let active = true;
    const ping = async () => {
      try {
        const res = await fetch(`${API_BASE}${statusPath}`, { cache: "no-store" });
        if (active) setStatus(res.ok ? "online" : "offline");
      } catch {
        if (active) setStatus("offline");
      }
    };
    ping();
    const id = setInterval(ping, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [statusPath]);

  const pill =
    status === "online"
      ? { dot: a.dot, label: "backend online", text: "text-slate-300" }
      : status === "offline"
      ? { dot: "bg-slate-600", label: "backend offline", text: "text-slate-500" }
      : { dot: "bg-slate-500 animate-pulse", label: "checking…", text: "text-slate-500" };

  return (
    <Link
      href={href}
      className={`block rounded-2xl border border-slate-800 bg-slate-900/60 p-6 transition ${a.hover}`}
    >
      <div className="flex items-center justify-between">
        <h3 className={`text-xl font-semibold ${a.title}`}>{title}</h3>
        <span className={`inline-flex items-center gap-1.5 text-xs ${pill.text}`}>
          <span className={`h-2 w-2 rounded-full ${pill.dot}`} />
          {pill.label}
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-400">{tagline}</p>
      <span className={`mt-4 inline-block text-sm font-medium ${a.title}`}>Open {title} →</span>
    </Link>
  );
}
