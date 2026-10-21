# Shared Agent Core (`agents/core`)

All three Kavach modes (Attack, Defend, Protect) share this tiny agent core
instead of each importing an LLM SDK directly. It keeps the platform cohesive:
one place defines "what an agent is" and "how we talk to a model".

## What's here

| File | Role |
|------|------|
| `agent.py` | Minimal `Agent` = role + system prompt + optional tools. Mode pipelines (e.g. Recon → Scanner → Exploit → Reporter) compose several `Agent`s. |
| `llm.py`   | `LLMClient`, a thin wrapper over the **OpenAI-compatible** chat API. |
| `__init__.py` | Re-exports `Agent`, `LLMClient`, `get_llm`. |

## Pluggable, vendor-neutral LLM

`LLMClient` speaks the OpenAI-compatible API, so the same code works with:

- **Local models** (default): Ollama / LM Studio / vLLM — `LLM_PROVIDER=local`,
  `LLM_BASE_URL=http://localhost:11434/v1`.
- **Hosted endpoints**: OpenAI or any compatible proxy — `LLM_PROVIDER=openai`,
  `LLM_API_KEY=sk-...`.

Everything is configured by environment variables (see `.env.example`); no code
change is needed to switch providers. The real SDK (`openai`) is imported
**lazily**, so the package imports cleanly even before that dependency is
installed.

## Offline-first: `KAVACH_LLM=off`

The LLM is an **optional enhancer, never a hard dependency**. Each mode has a
small `llm_assist.py` that follows the same contract:

```
KAVACH_LLM=off    -> never call the LLM (default; safe for grading / viva)
KAVACH_LLM=auto   -> try the LLM, silently fall back to deterministic output
```

- **Attack** — deterministic rule-based report is always produced; the LLM only
  *rewrites* the executive summary and remediation prose.
- **Defend** — rule engine decides allow/sanitize/block; the LLM can only
  *agree or escalate* a verdict (it can never downgrade a BLOCK).
- **Protect** — deterministic score + verdict are fixed; the LLM only *rewrites
  the explanation* in friendlier words.

Any LLM failure (no server, bad key, timeout) is caught and the deterministic
path takes over, so demos and the automated test suite never break. This is why
the whole platform passes its tests fully offline.
