# Voice sample set (synthetic, demonstration only)

`real/*.wav` and `fake/*.wav` are **generated** by `scripts/make_voice_samples.py`
(8 kHz, 2 s). "real" simulates human-like properties (pauses, pitch glides,
mic noise); "fake" simulates naive TTS (steady loudness, flat pitch, no noise).
They are NOT real recordings and modern voice clones would fool this heuristic.

For real work use ASVspoof 2019/2021 (https://www.asvspoof.org/) or
"In-the-Wild" deepfake audio, with a model such as AASIST.
