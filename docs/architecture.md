# Architecture — Kavach AI Platform

## Overview

One shared AI agent core drives three modes behind a single FastAPI backend and
one Next.js dashboard. Modes can feed each other: Attack generates attack
patterns that harden Defend; Defend's detector powers Protect.

## Mermaid diagram

```mermaid
flowchart TB
  subgraph UI["Next.js Dashboard + Browser Extension"]
    Home["Home"]
    AttackUI["Attack page"]
    DefendUI["Defend page / timeline"]
    ProtectUI["Protect page + Kavach Shield ext"]
  end

  subgraph API["FastAPI Backend :8000"]
    Health["/health"]
    ARoutes["/attack/*"]
    DRoutes["/defend/*"]
    PRoutes["/protect/*"]
  end

  subgraph Core["Shared Agent Core (agents/)"]
    LLM["LLMClient\n(OpenAI-compatible\nlocal or hosted)"]
    Agent["Agent\n(role + prompt + tools)"]
  end

  subgraph Modes["Mode Pipelines"]
    Attack["Attack\nRecon → Scanner → Exploit → Reporter\nMITRE ATT&CK + PDF/MD report"]
    Defend["Defend / Sentinel\nFirewall + Red-team AI\nSelf-heal attack store"]
    Protect["Protect / Kavach Shield\nURL / SMS / Voice detectors\nen + hi explanations"]
  end

  subgraph Lab["Local Vulnerable Lab (Docker)"]
    Juice["OWASP Juice Shop / DVWA"]
  end

  subgraph Data["Datasets (datasets/)"]
    Phish["Phishing URL sets"]
    SMS["Scam SMS corpora"]
    Voice["Voice-clone samples"]
  end

  Home --> AttackUI & DefendUI & ProtectUI
  AttackUI --> ARoutes
  DefendUI --> DRoutes
  ProtectUI --> PRoutes
  ARoutes --> Attack
  DRoutes --> Defend
  PRoutes --> Protect
  Attack & Defend & Protect --> Agent --> LLM
  Attack --> Juice
  Protect --> Data
  Attack -.->|"attack patterns"| Defend
  Defend -.->|"hardened detector"| Protect
```

## Request flow (example)

1. User opens **Attack** in the dashboard and submits a lab URL.
2. `POST /attack/scan` kicks off the multi-agent pipeline.
3. Agents call the shared `LLMClient` (local Ollama by default).
4. Findings are mapped to MITRE ATT&CK and written as Markdown + PDF.
5. Patterns that succeeded against Defend's red-team loop can be exported into
   the Protect detectors' feature store (future work / self-heal).

## Safety constraints (college project)

- Attack mode is **authorized local-lab only** (Juice Shop / DVWA in Docker).
- No real-world pentesting of third-party systems.
- Protect mode uses public datasets and uploaded samples — no live phone
  interception in v1.
