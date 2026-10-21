/**
 * Tiny typed API client for the Protect-mode endpoints.
 * Mirrors the backend response shape from modes/protect/common.py::make_result.
 */
import { API_BASE_URL } from "./config";
import type { Verdict } from "../theme/colors";

export type Lang = "en" | "hi";

export interface Reason {
  code: string;
  en: string;
  hi: string;
}

export interface CheckResult {
  kind: "url" | "sms" | "audio";
  input: string;
  risk_score: number; // 0-100
  verdict: Verdict;
  reasons: Reason[];
  explanation: { en: string; hi: string; llm?: string };
  engine: string;
  check_id?: string;
}

const TIMEOUT_MS = 8000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Abort slow requests so the UI never hangs forever.
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { ...init, signal: ctrl.signal });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body?.detail) detail = String(body.detail);
      } catch {
        /* non-JSON error body */
      }
      throw new Error(detail);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

const postJson = <T>(path: string, body: unknown) =>
  request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

/** GET /health -> true if the backend answered. */
export async function pingBackend(): Promise<boolean> {
  try {
    await request<unknown>("/health");
    return true;
  } catch {
    return false;
  }
}

export const checkUrl = (url: string, language: Lang = "en") =>
  postJson<CheckResult>("/protect/url", { url, language });

export const checkSms = (text: string, language: Lang = "en") =>
  postJson<CheckResult>("/protect/sms", { text, language });

/**
 * POST /protect/audio (multipart, field "file", .wav only).
 * Not used by the UI yet - wired here for when the Audio screen is built
 * (pick a file with expo-document-picker and pass its uri).
 */
export function checkAudio(fileUri: string, name = "clip.wav", language: Lang = "en") {
  const form = new FormData();
  // React Native's FormData accepts {uri, name, type} objects for files.
  form.append("file", { uri: fileUri, name, type: "audio/wav" } as unknown as Blob);
  form.append("language", language);
  return request<CheckResult>("/protect/audio", { method: "POST", body: form });
}

export const getStats = () => request<Record<string, unknown>>("/protect/stats");
