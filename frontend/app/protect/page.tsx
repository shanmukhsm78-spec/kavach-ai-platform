"use client";

/**
 * Protect mode — Kavach Shield.
 * Three cards: Check URL, Check Message, Check Audio. Each shows the 0-100 risk
 * score, a verdict badge, highlighted reasons and an English/Hindi explanation.
 */
import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Reason = { code: string; en: string; hi: string };
type Result = {
  kind: string;
  input: string;
  risk_score: number;
  verdict: "safe" | "suspicious" | "dangerous";
  reasons: Reason[];
  explanation: { en: string; hi: string; llm?: string };
  engine: string;
  features: Record<string, unknown>;
};
type Stats = {
  total: number;
  by_kind: Record<string, number>;
  by_verdict: Record<string, number>;
  recent: { check_id: string; ts: string; kind: string; verdict: string; risk_score: number; preview: string }[];
};

const BADGE: Record<string, string> = {
  dangerous: "bg-red-900/60 text-red-300 border border-red-700",
  suspicious: "bg-yellow-900/50 text-yellow-300 border border-yellow-700",
  safe: "bg-emerald-900/50 text-emerald-300 border border-emerald-700",
};
const BAR: Record<string, string> = { dangerous: "bg-red-500", suspicious: "bg-yellow-400", safe: "bg-emerald-500" };
type Tab = "url" | "sms" | "audio";

function ResultCard({ r, lang }: { r: Result; lang: "en" | "hi" }) {
  // "natural_audio" / "trusted_domain" are reassuring reasons, not warnings.
  const good = new Set(["natural_audio", "trusted_domain"]);
  return (
    <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center gap-3">
        <span className={`rounded px-2 py-1 text-xs font-semibold uppercase ${BADGE[r.verdict]}`}>{r.verdict}</span>
        <span className="text-2xl font-bold">{r.risk_score}<span className="text-sm text-slate-500">/100</span></span>
        <span className="ml-auto text-xs text-slate-500">engine: {r.engine}</span>
      </div>
      <div className="mt-2 h-2 w-full rounded bg-slate-800">
        <div className={`h-2 rounded ${BAR[r.verdict]}`} style={{ width: `${r.risk_score}%` }} />
      </div>
      {r.reasons.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm">
          {r.reasons.map((x) => (
            <li key={x.code} className={good.has(x.code) ? "text-emerald-300" : "text-orange-300"}>
              {good.has(x.code) ? "✔" : "⚠"} <mark className="bg-transparent font-mono text-xs text-slate-400">{x.code}</mark> {x[lang]}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 rounded bg-slate-900 p-3 text-sm leading-relaxed">{r.explanation[lang]}</p>
      {r.explanation.llm && <p className="mt-2 text-xs text-sky-300">AI note: {r.explanation.llm}</p>}
    </div>
  );
}

export default function ProtectPage() {
  const [tab, setTab] = useState<Tab>("url");
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [url, setUrl] = useState("http://sbi-kyc-update.xyz/verify");
  const [sms, setSms] = useState("Dear customer your SBI account will be blocked today. Update KYC immediately.");
  const [file, setFile] = useState<File | null>(null);
  const [sample, setSample] = useState("datasets/voice/fake/fake_1.wav");
  const [result, setResult] = useState<Result | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setStats(await fetch(`${API_BASE}/protect/stats?limit=10`).then((r) => r.json()));
    } catch { /* backend offline — page still renders */ }
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null); setResult(null);
    try {
      let res: Response;
      if (tab === "url") {
        res = await fetch(`${API_BASE}/protect/url`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url, language: lang }) });
      } else if (tab === "sms") {
        res = await fetch(`${API_BASE}/protect/sms`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: sms, language: lang }) });
      } else {
        const fd = new FormData();
        if (file) fd.append("file", file); else fd.append("path", sample);
        fd.append("language", lang);
        res = await fetch(`${API_BASE}/protect/audio`, { method: "POST", body: fd });
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Check failed (${res.status})`);
      setResult(data);
      refresh();
    } catch (err: any) {
      setError(err.message || "Check failed");
    } finally {
      setLoading(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "url", label: "🔗 Check URL" }, { id: "sms", label: "💬 Check Message" }, { id: "audio", label: "🎙️ Check Audio" },
  ];

  return (
    <div>
      <div className="flex items-center">
        <h1 className="text-2xl font-bold text-sky-400">Protect — Kavach Shield</h1>
        <button onClick={() => setLang(lang === "en" ? "hi" : "en")} className="ml-auto rounded border border-slate-700 px-3 py-1 text-sm">
          {lang === "en" ? "हिंदी में देखें" : "View in English"}
        </button>
      </div>
      <p className="mt-2 text-slate-400">Detects phishing links, scam SMS (digital arrest, KYC, UPI, OTP…) and AI voice clones, with warnings in English + Hindi.</p>

      <div className="mt-6 flex gap-2">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => { setTab(t.id); setResult(null); }}
            className={`rounded-t px-4 py-2 text-sm ${tab === t.id ? "bg-slate-800 text-white" : "bg-slate-900 text-slate-400"}`}>{t.label}</button>
        ))}
      </div>
      <form onSubmit={submit} className="rounded-b-lg rounded-tr-lg bg-slate-900 p-4">
        {tab === "url" && <input value={url} onChange={(e) => setUrl(e.target.value)} className="w-full rounded bg-slate-950 p-2 font-mono text-sm" placeholder="https://…" />}
        {tab === "sms" && <textarea value={sms} onChange={(e) => setSms(e.target.value)} rows={4} className="w-full rounded bg-slate-950 p-2 text-sm" />}
        {tab === "audio" && (
          <div className="space-y-2 text-sm">
            <input type="file" accept=".wav,audio/wav" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <div>or sample:{" "}
              <select value={sample} onChange={(e) => setSample(e.target.value)} className="rounded bg-slate-950 p-1">
                {[1, 2, 3, 4].flatMap((n) => [`datasets/voice/real/real_${n}.wav`, `datasets/voice/fake/fake_${n}.wav`]).map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
            <p className="text-xs text-slate-500">Demo-grade signal heuristic — real deployments need an ASVspoof-trained model.</p>
          </div>
        )}
        <button disabled={loading} className="mt-3 rounded bg-sky-600 px-4 py-2 text-sm font-semibold disabled:opacity-50">{loading ? "Checking…" : "Check"}</button>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        {result && <ResultCard r={result} lang={lang} />}
      </form>

      {stats && (
        <div className="mt-8">
          <h2 className="font-semibold text-slate-300">History ({stats.total} checks · {stats.by_verdict?.dangerous ?? 0} dangerous)</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {stats.recent.map((c) => (
              <li key={c.check_id} className="flex gap-2">
                <span className={`rounded px-1 text-xs ${BADGE[c.verdict]}`}>{c.verdict}</span>
                <span className="text-slate-500">{c.kind}</span><span className="truncate">{c.preview}</span>
                <span className="ml-auto text-slate-500">{c.risk_score}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
