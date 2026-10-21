"""Generate the tiny SYNTHETIC voice sample set in datasets/voice/{real,fake}.

No real recordings are shipped (privacy + size). We *simulate* the acoustic
properties our heuristic looks at:
  real/  -> 'human-like': syllable bursts with pauses, pitch glides, mic noise
  fake/  -> 'naive TTS-like': constant loudness, flat pitch, perfectly clean
Replace these with real clips (e.g. ASVspoof 2019 LA subset) for a real study.
Run:  .venv/bin/python scripts/make_voice_samples.py
"""
import math
import random
import struct
import wave
from pathlib import Path

SR, DUR = 8000, 2.0
OUT = Path(__file__).resolve().parents[1] / "datasets" / "voice"


def write(path, xs):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32000)) for x in xs))


def voice(f0_fn, env_fn, noise, rng):
    xs, ph = [], 0.0
    for i in range(int(SR * DUR)):
        t = i / SR
        ph += 2 * math.pi * f0_fn(t) / SR
        s = sum(math.sin(k * ph) / k for k in (1, 2, 3, 4))
        xs.append(0.4 * env_fn(t) * s + rng.gauss(0, noise))
    return xs


def main():
    for d in ("real", "fake"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for n in range(4):
        rng = random.Random(n)
        base = 110 + 30 * n
        syl = 3 + n % 2                                  # syllables per second
        real = voice(lambda t: base * (1 + 0.25 * math.sin(2 * math.pi * 0.7 * t) + 0.08 * math.sin(2 * math.pi * 5 * t)),
                     lambda t: max(0.0, math.sin(math.pi * syl * t)) ** 2 * (0 if 0.9 < t < 1.2 else 1),
                     0.01, rng)
        fake = voice(lambda t: base, lambda t: 1.0, 0.0, rng)
        write(OUT / "real" / f"real_{n + 1}.wav", real)
        write(OUT / "fake" / f"fake_{n + 1}.wav", fake)
    print("wrote samples to", OUT)


if __name__ == "__main__":
    main()
