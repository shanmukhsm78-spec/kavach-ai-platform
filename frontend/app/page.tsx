"use client";

import { useEffect, useState } from "react";
import ModeCard from "../components/ModeCard";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Health = { status: string; app: string; version: string; llm_provider: string; llm_model: string };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [online, setOnline] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let active = true;
    const ping = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
        const data = await res.json();
        if (active) {
          setHealth(data);
          setOnline("online");
        }
      } catch {
        if (active) setOnline("offline");
      }
    };
    ping();
    const id = setInterval(ping, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  return (
    <div>
      {/* Hero */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">🛡️ Kavach AI Platform</h1>
          <p className="mt-3 max-w-2xl text-slate-400">
            One shared AI agent core, three modes. Attackers and defenders are both AI now — so we
            build both and let them train each other, then point the hardened detector at everyday
            scams.
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                online === "online"
                  ? "bg-emerald-400"
                  : online === "offline"
                  ? "bg-rose-500"
                  : "bg-slate-500 animate-pulse"
              }`}
            />
            <span className="text-slate-300">
              {online === "online" ? "Backend online" : online === "offline" ? "Backend offline" : "Checking backend…"}
            </span>
          </div>
          {health && (
            <div className="mt-1 text-xs text-slate-500">
              v{health.version} · LLM: {health.llm_provider}/{health.llm_model}
            </div>
          )}
          {online === "offline" && (
            <div className="mt-1 text-xs text-slate-500">Start it: <code>make backend</code></div>
          )}
        </div>
      </div>

      {/* Mode cards */}
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <ModeCard
          href="/attack"
          title="Attack"
          accent="rose"
          statusPath="/attack/status"
          tagline="AI pentester: Recon → Scanner → Exploit → Reporter on a local lab, mapped to MITRE ATT&CK, with PDF/Markdown reports."
        />
        <ModeCard
          href="/defend"
          title="Defend"
          accent="emerald"
          statusPath="/defend/status"
          tagline="Sentinel firewall: blocks prompt injection, data exfil and dangerous tool calls in real time, and self-heals from a red-team loop."
        />
        <ModeCard
          href="/protect"
          title="Protect"
          accent="sky"
          statusPath="/protect/status"
          tagline="Kavach shield: flags phishing URLs, scam SMS and voice clones with multilingual (English/Hindi) warnings."
        />
      </div>

      {/* Footer note */}
      <p className="mt-10 text-xs text-slate-600">
        Offline-first: runs fully without an LLM (KAVACH_LLM=off). Attack mode only scans local /
        private lab targets. Final-year project · solo build.
      </p>
    </div>
  );
}
