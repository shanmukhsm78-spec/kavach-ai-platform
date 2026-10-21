"use client";

import { useState } from "react";

// Base URL of the FastAPI backend (configured in next.config.mjs).
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Finding = {
  check_id: string;
  title: string;
  severity: string;
  cvss_qualitative: string;
  location: string;
  description: string;
  evidence: string;
  exploit_proof: string;
  remediation: string;
  mitre: { id: string; name: string; tactic: string };
};

type ScanResult = {
  scan_id: string;
  target: string;
  status: string;
  summary: string;
  summary_engine: string;
  findings: Finding[];
};

// Tailwind colour per severity for the badge in the findings table.
const SEV_STYLE: Record<string, string> = {
  Critical: "bg-red-900/60 text-red-300 border border-red-700",
  High: "bg-orange-900/60 text-orange-300 border border-orange-700",
  Medium: "bg-yellow-900/50 text-yellow-300 border border-yellow-700",
  Low: "bg-blue-900/50 text-blue-300 border border-blue-700",
  Info: "bg-slate-800 text-slate-300 border border-slate-600",
};

export default function AttackPage() {
  const [target, setTarget] = useState("http://localhost:3000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);

  async function startScan(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/attack/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_url: target, scope: "web" }),
      });
      const data = await res.json();
      if (!res.ok) {
        // Backend returns 400 with {detail} when the target is out of scope.
        throw new Error(data.detail || `Request failed (${res.status})`);
      }
      setResult(data as ScanResult);
    } catch (err: any) {
      setError(err.message || "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-rose-400">
        Attack — AI Pentester
      </h1>
      <p className="mt-3 text-slate-400">
        Multi-agent team (Recon → Scanner → Exploit → Reporter) scans a local
        vulnerable lab and produces a PDF + Markdown report mapped to MITRE
        ATT&amp;CK. Only loopback / private targets are allowed.
      </p>

      {/* Scan form */}
      <form onSubmit={startScan} className="mt-6 flex flex-wrap gap-3">
        <input
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="http://localhost:3000"
          className="flex-1 min-w-[18rem] rounded-lg bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-rose-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-50"
        >
          {loading ? "Scanning…" : "Start scan"}
        </button>
      </form>

      {error && (
        <p className="mt-4 rounded-lg bg-red-950/60 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-8">
          {/* Summary + report links */}
          <div className="rounded-lg bg-slate-900 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="text-sm text-slate-400">Scan</span>{" "}
                <code className="text-slate-200">{result.scan_id}</code>{" "}
                <span className="ml-2 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                  {result.summary_engine}
                </span>
              </div>
              <div className="flex gap-3 text-sm">
                <a
                  className="text-rose-400 hover:underline"
                  href={`${API_BASE}/attack/report/${result.scan_id}`}
                  target="_blank"
                >
                  Download PDF
                </a>
                <a
                  className="text-rose-400 hover:underline"
                  href={`${API_BASE}/attack/report/${result.scan_id}/markdown`}
                  target="_blank"
                >
                  Markdown
                </a>
              </div>
            </div>
            <p className="mt-3 text-sm text-slate-300">{result.summary}</p>
          </div>

          {/* Findings table */}
          <h2 className="mt-6 text-lg font-semibold text-slate-200">
            Findings ({result.findings.length})
          </h2>
          <div className="mt-3 overflow-x-auto rounded-lg ring-1 ring-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-slate-400">
                <tr>
                  <th className="px-3 py-2">Severity</th>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">MITRE ATT&amp;CK</th>
                  <th className="px-3 py-2">Location</th>
                </tr>
              </thead>
              <tbody>
                {result.findings.map((f, i) => (
                  <tr key={i} className="border-t border-slate-800">
                    <td className="px-3 py-2">
                      <span
                        className={`rounded px-2 py-0.5 text-xs ${
                          SEV_STYLE[f.severity] || SEV_STYLE.Info
                        }`}
                      >
                        {f.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-200">{f.title}</td>
                    <td className="px-3 py-2 text-slate-400">
                      {f.mitre.id} {f.mitre.name}
                    </td>
                    <td className="px-3 py-2 text-slate-500 break-all">
                      {f.location}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
