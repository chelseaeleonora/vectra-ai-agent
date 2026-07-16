# 🚀 Vectra AI: Autonomous Multi-Agent Sales Workforce

**Build with Gemini XPRIZE Submission** | *Autonomous Digital Workforce for SMBs*

---

## 📖 Overview
Vectra AI is not just a chatbot; it is an autonomous, multi-agent digital workforce designed to handle end-to-end sales, negotiation, and accounting for Small and Medium Businesses (SMBs) 24/7 without human intervention. 

Built for the **Build with Gemini XPRIZE**, Vectra AI leverages the power of Google's Gemini API to create a deterministic, zero-hallucination sales pipeline that protects business margins while closing deals.

## ✨ Key Features
- **🧠 JSON Decision Engine:** Forces the AI to output strictly structured JSON, eliminating hallucinations and ensuring deterministic execution.
- **🛡️ Hardcoded Guardrails:** Strict business rules (e.g., maximum 10% discount) that the AI cannot bypass, protecting company revenue.
- **🔄 Multi-Agent Orchestration:** Specialized agents (Manager, SDR, Closer, Finance) working together seamlessly.
- **🧠 Contextual Memory:** Agents remember previous interactions, ensuring consistent pricing and negotiation history.
- **⚡ Optimized for Free Tier:** Architected to run efficiently on `gemini-3.1-flash-lite` with strict rate-limit management.

## 🏗️ Architecture: The 4-Agent System

Vectra AI uses a decentralized multi-agent architecture controlled by a central orchestrator:

1. **Manager Agent (Orchestrator):** Analyzes incoming messages and routes them to the correct specialized agent based on intent.
2. **SDR Agent (Sales Development Rep):** Greets potential customers, qualifies leads, and determines if they are serious buyers.
3. **Closer Agent (Negotiator):** Handles price discussions. Enforces strict discount guardrails (max 10%) and closes the deal.
4. **Finance Agent (Accounting):** Generates invoices and processes payments. Extracts exact figures from conversation memory to prevent pricing hallucinations.

## 🛠️ Tech Stack
- **Language:** Python 3.12+
- **AI Model:** Google Gemini API (`gemini-3.1-flash-lite`)
- **Core Logic:** Custom JSON-First Decision Engine
- **State Management:** Contextual Memory Injection

## 🚀 Getting Started

### Prerequisites
- Python 3.12 or higher
- A Google AI Studio API Key

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/chelseaeleonora/vectra-ai-agent.git
   cd vectra-ai-agent
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables:
   Create a `.env` file in the root directory and add your API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

### Running the System
To test the multi-agent system via CLI:
```bash
python -m tests.test_memory
```

##  Competition Strategy (XPRIZE)
Vectra AI is designed to achieve **Zero-Click Closing**. By combining strict JSON guardrails with multi-agent specialization, we ensure that the AI doesn't just "talk"—it executes real business logic safely and reliably.

---
*Built with love for the Build with Gemini XPRIZE 2026.*
```
