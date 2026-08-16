# ⚡ VECTRA AI — Autonomous CRO

[![LIVE DEMO](https://img.shields.io/badge/LIVE_DEMO-Railway-6C63FF?style=for-the-badge)](https://vectra-ai-agent-production.up.railway.app/) [![Gemini XPRIZE 2026](https://img.shields.io/badge/Gemini_XPRIZE-2026-4285F4?style=for-the-badge)](https://xprize.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE) [![Watch Demo](https://img.shields.io/badge/Watch_Demo-YouTube-FF0000?style=for-the-badge)](https://youtu.be/Nrrp1flN0v8)

**A CRM-native autonomous sales system that qualifies, negotiates, closes, and learns — running entirely on Google Sheets.**

**Built for the Gemini XPRIZE 2026 • Category: Small Business Services**

---

## 📖 Overview

Vectra AI is not a chatbot — it is an **autonomous revenue operator**. A human founder feeds leads into a Google Sheet; from that moment, the headless Autonomous Pipeline takes over 100% of the sales operation: qualifying prospects, adapting personality, negotiating within strict compliance guardrails, logging outcomes, and learning from every deal.

No expensive CRM. No database. No sales team. Near-zero cost per deal — the entire system runs on free tiers.

> *"Rather lose a deal than lie to win one."* — Every Vectra response is audit-logged, compliance-checked, and grounded in the knowledge base. The AI never grades its own deals; outcomes are derived from the customer's own words.

![Vectra AI War Room — glass-box multi-agent workflow](assets/war_room.png)

> More product screenshots — CRM logs, Strategy Stats, BI reports, and the Railway deployment — live in the [assets/](assets) folder.

---

## 🧬 The 4 Signature Capabilities

| # | Capability | What it does |
| --- | --- | --- |
| 1 | **Memory-Aware Negotiation** | CRM-native long-term memory — the AI greets returning leads with full context ("Last time we discussed…") |
| 2 | **Autonomous Outcome Detection** | Deal status (CLOSED / LOST / NEGOTIATING) is derived deterministically from the customer's own words — the AI never self-reports wins |
| 3 | **Adaptive Personality Engine** | Detects DRIVER / ANALYTICAL / AMIABLE / EXPRESSIVE leads and adapts tone in real time — zero LLM cost, pure heuristics |
| 4 | **Strategic BI (CRO Mode)** | DeepSeek acts as Chief Revenue Officer, writing honest strategic reports from live CRM data — including candid admissions when the sample size is too small |

---

## 🛡️ Compliance That Cannot Be Bypassed

Vectra ships with a **double-layer Finance Guardrail**:

- **Layer 1 — Gemini 3.5 Flash-Lite** audits every Closer response for discount violations, negative prices, and unrealistic promises
- **Layer 2 — Deterministic hard rules** catch edge cases Gemini may miss (fail-closed design: if audit is uncertain, the response is blocked and self-corrected)
- **Hard ceiling:** 10% maximum discount — CEO override attempts are politely refused
- **Honesty-first:** requests for hallucinated features (e.g., "hardware firewall", "100% uptime forever") are declined with the actual product scope

---

## 🏗️ Ultra-Lean Hybrid Architecture (95/5)

| Layer | Role |
| --- | --- |
| **DeepSeek V4 Pro** (95%) | All reasoning: routing, qualification, negotiation, memory synthesis, CRO reports |
| **Gemini 3.5 Flash Lite** (5%) | ONLY the Finance Guardrail compliance audit |
| **Google Sheets** | The CRM database (Lead Pipeline, CRM Log, Lead Memory, Strategy Stats) |
| **Deterministic Python** | Strategy detection, personality heuristics, outcome detection, stats aggregation — zero LLM cost |

```text
Lead (Sheets / Chat) -> Manager Agent (Router)
   -> SDR Agent (Qualify)  /  CLOSER Agent (Negotiate)
        -> Finance Guardrail (Gemini audit + self-correction)
             -> Zero-Click Execution (Google Sheets logging)
                  -> Autonomous Outcome Detection (from customer's words)
                       -> Strategy Stats + Lead Memory (learning loop)
```

---

## 🗂️ Repository Structure

```text
backend/chainlit_app.py    # Glass-Box UI + headless Autonomous Pipeline
services/llm_service.py    # Hybrid LLM layer + Finance Guardrail
public/                    # Neon Cyberpunk theme (CSS, SVG, JS branding)
.chainlit/config.toml      # Theme & custom asset configuration
knowledge_base.txt         # Local knowledge grounding (anti-hallucination)
engine.py                  # Terminal test harness
requirements.txt
```

---

## 🚀 Quick Start

**Prerequisites:** Python 3.10+, a Fireworks AI API key, a Google Gemini API key, and a Google Service Account JSON.

```bash
git clone https://github.com/chelseaeleonora/vectra-ai-agent.git
cd vectra-ai-agent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```text
FIREWORKS_API_KEY=your_key
GEMINI_API_KEY=your_key
```

Place your Service Account file as `sheets_credentials.json` in the root (or set `GOOGLE_CREDENTIALS_JSON` env var for cloud deployment).

Run:

```bash
chainlit run backend/chainlit_app.py
```

Then click **🚀 Run Autonomous Sales Day** to process all NEW leads in your Lead Pipeline tab — headlessly, with zero human intervention.

---

## ☁️ Deployment (Railway / Render)

| Setting | Value |
| --- | --- |
| **Build** | `pip install -r requirements.txt` |
| **Start** | `chainlit run backend/chainlit_app.py --host 0.0.0.0 --port $PORT --headless` |
| **Env vars** | `FIREWORKS_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_CREDENTIALS_JSON` |

---

## 💰 Unit Economics (transparent math)

| Item | Cost |
| --- | --- |
| Server / database | $0 (Google Sheets free tier) |
| Gemini guardrail | $0 (Google AI Studio free tier) |
| DeepSeek V4 Pro reasoning (Fireworks, Priority tier) | $1.65/M uncached input · $0.055/M cached input · $4.95/M output |
| Typical closed deal | A few cents — 2–4 negotiation turns of ~3K tokens each |
| Monthly infrastructure | $0 by design; only LLM inference carries a cost |

*Per-token prices are Fireworks' published Priority-tier rates for deepseek-v4-pro-0813 (August 2026). Per-deal cost is a qualitative estimate that varies with conversation length, retries, and prompt caching.*

---

## 📊 CRM Structure (Google Sheets)

The entire business runs on 5 tabs in a single spreadsheet:

| Tab | Purpose |
| --- | --- |
| **Lead Pipeline** | Incoming leads queued for the Autonomous Pipeline |
| **CRM Log** | Zero-click audit trail of every interaction |
| **Lead Memory** | Persistent conversation history per Lead_ID |
| **Strategy Stats** | Auto-updated win-rate per personality segment |
| **BI Reports** | Archive of CRO-mode strategic analyses |

---

## ⚖️ What This Is — and Is Not

**Is:** a production-grade, auditable sales-automation template you customize (knowledge base, prompts, business rules) for any product or service.

**Is not:** a lead generator, payment processor, or email sender. Buyers provide their own leads, payment links, and delivery automation.

---

## 🤝 Commercialization Note (Honest)

After more than a month of development for the Gemini XPRIZE, Vectra AI shipped to **three marketplaces simultaneously just 3 days ago**. Zero sales in the first 72 hours of a brand-new, zero-ad-spend listing is expected and normal. What matters is that the full commercial path exists and works end-to-end:

```text
public repository -> one-click deploy -> live CRM -> purchasable listing at $9 early-bird
```

We would rather report an honest day-3 listing than inflate numbers we don't have. This aligns with the core philosophy of the system itself: *rather lose a deal than lie to win one.*

---

## 🔗 Links

| Resource | URL |
| --- | --- |
| 🔴 Live Demo | https://vectra-ai-agent-production.up.railway.app/ |
| ▶️ Demo Video | https://youtu.be/Nrrp1flN0v8 |
| 💻 Source Code | https://github.com/chelseaeleonora/vectra-ai-agent |
| 🛒 Gumroad ($9 early-bird) | https://eleonora627.gumroad.com/l/uguqa |
| 🛒 Whop ($9 early-bird) | https://whop.com/joined/vectra-ai-autonomous-multi-agent-sales-system-for-smbs-full-source-code-setup-guide/products/vectra-ai-autonomous-multi-agent-sales-system-source-code-setup-guide/ |
| 🛒 Payhip ($9 early-bird) | https://payhip.com/b/FWV8D |

---

## 📜 License

**MIT** — learn, modify, deploy.

---

*Built with Python · Chainlit · DeepSeek V4 Pro on Fireworks · Gemini 3.5 Flash-Lite · Google Sheets API · Docker · Railway*

*An autonomous revenue-operations layer for SMBs — shipped to three marketplaces for the Gemini XPRIZE 2026.*
