"""Voice-clone / AI-audio detector - DEMONSTRATION-GRADE heuristic.

HONEST NOTE (say this in the viva): real deepfake-voice detection needs a
trained anti-spoofing model (e.g. AASIST / RawNet2 trained on ASVspoof).
Those are heavy, so this module shows the *pipeline* with simple signal
features computed with the Python standard library only (``wave`` + math):

  * rms_cv        - variation of loudness across 20 ms frames
                    (human speech rises/falls; naive TTS is steadier)
  * silence_ratio - share of near-silent frames (pauses, breaths)
  * hf_noise      - energy of the 2nd difference vs the signal (a crude
                    high-frequency 'hiss' measure; real mics always add noise)
  * zcr_cv        - variation of zero-crossing rate (proxy for pitch/tone change)

Each "too synthetic" feature adds points. It works on our tiny synthetic
sample set (datasets/voice) and is meant to be replaced by a real model.
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from .common import make_result

FRAME_MS = 20


def read_wav(path: str | Path) -> tuple[list[float], int]:
    """Read a mono/stereo 8/16-bit PCM wav into floats in [-1, 1]."""
    with wave.open(str(path), "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    if sw == 2:
        vals = struct.unpack(f"<{len(raw) // 2}h", raw)
        samples = [v / 32768.0 for v in vals]
    elif sw == 1:
        samples = [(b - 128) / 128.0 for b in raw]
    else:
        raise ValueError("Only 8/16-bit PCM wav is supported")
    if ch > 1:
        samples = samples[::ch]
    return samples, sr


def _cv(xs: list[float]) -> float:
    m = sum(xs) / len(xs) if xs else 0.0
    if m == 0:
        return 0.0
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) / m


def _hf_noise(xs: list[float]) -> float:
    d2 = [xs[i + 1] - 2 * xs[i] + xs[i - 1] for i in range(1, len(xs) - 1)]
    sig = math.sqrt(sum(x * x for x in xs) / len(xs)) or 1e-9
    return math.sqrt(sum(d * d for d in d2) / max(1, len(d2))) / sig


def extract_features(samples: list[float], sr: int) -> dict:
    step = max(1, int(sr * FRAME_MS / 1000))
    rms, zcr = [], []
    for i in range(0, len(samples) - step + 1, step):
        fr = samples[i:i + step]
        rms.append(math.sqrt(sum(s * s for s in fr) / step))
        zcr.append(sum(1 for a, b in zip(fr, fr[1:]) if (a >= 0) != (b >= 0)) / step)
    if not rms:
        raise ValueError("Audio too short")
    peak = max(rms) or 1e-9
    voiced = [z for z, r in zip(zcr, rms) if r > 0.1 * peak]
    return {
        "duration_s": round(len(samples) / sr, 2),
        "sample_rate": sr,
        "rms_cv": round(_cv(rms), 3),
        "silence_ratio": round(sum(1 for r in rms if r < 0.05 * peak) / len(rms), 3),
        "hf_noise": round(_hf_noise(samples), 4),
        "zcr_cv": round(_cv(voiced) if voiced else 0.0, 3),
    }


def score_features(f: dict) -> tuple[int, list[str]]:
    score, codes = 0, []
    if f["rms_cv"] < 0.35:
        score += 30; codes.append("too_steady_volume")
    if f["silence_ratio"] < 0.05:
        score += 20; codes.append("no_pauses")
    if f["hf_noise"] < 0.13:
        score += 25; codes.append("too_clean")
    if f["zcr_cv"] < 0.08:
        score += 25; codes.append("flat_pitch")
    if not codes:
        codes.append("natural_audio")
    return score, codes


def score_audio(path: str | Path) -> dict:
    samples, sr = read_wav(path)
    f = extract_features(samples, sr)
    score, codes = score_features(f)
    res = make_result("audio", Path(path).name, score, codes, features=f,
                      engine="signal_heuristic (demo-grade, not ASVspoof)")
    return res
