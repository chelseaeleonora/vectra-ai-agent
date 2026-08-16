import chainlit as cl
import sys
import os
import re
import re
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Ensure root folder is in path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm_service import call_fireworks_agent, call_gemini_guardrail, sanitize_ending

# --- Google Sheets Integration for Zero-Click Execution ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = "sheets_credentials.json"

def get_sheets_credentials():
    """Load Sheets credentials from local file OR env var (Render/Railway safe)."""
    if os.path.exists(CREDS_FILE):
        return Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
    env_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if env_creds:
        return Credentials.from_service_account_info(json.loads(env_creds), scopes=SCOPE)
    raise ValueError("No Sheets credentials: add sheets_credentials.json or GOOGLE_CREDENTIALS_JSON env var.")

def log_deal_to_sheet(user_msg: str, agent_used: str, final_response: str, status: str, discount: float, strategy_used: str = "", deal_outcome: str = "", personality: str = "",):
    """Logs the deal details to Google Sheets autonomously."""
    try:
        creds = get_sheets_credentials()
        client = gspread.authorize(creds)
        
        # TODO: Replace with your actual Google Sheet ID
        SPREADSHEET_ID = "1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY" 
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_msg, agent_used, final_response, status,
        ])

        # Keep the learning dashboard in sync after every logged deal
        try:
            refresh_strategy_stats_tab()
        except Exception as stats_err:
            print(f"Stats refresh error: {stats_err}")
        return True
    except Exception as e:
        print(f"Sheet logging error: {e}")
        return False

# --- Local RAG: Anti-Hallucination Knowledge Base ---
def load_knowledge_base() -> str:
    """Loads the local knowledge base file (no vector DB, ultra-lean)."""
    kb_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "knowledge_base.txt",
    )
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Vectra AI is an Autonomous Multi-Agent Sales System for SMBs."

KNOWLEDGE_BASE = load_knowledge_base()

# --- MULTI-AGENT PROMPTS (100% English) ---
MANAGER_PROMPT = """You are the Manager Agent (Router). Analyze the user's message intent.
- If the user wants to buy, negotiate price, asks for a discount, or says "yes" to a deal, reply ONLY with the word: CLOSER
- If the user is asking about features, general pricing, company info, or just saying hi, reply ONLY with the word: SDR
Do not output anything else."""

SDR_PROMPT = f"""You are the SDR (Sales Development Representative) for Vectra AI. 

PRODUCT FACTS (MUST FOLLOW):
- Vectra AI is an Autonomous Multi-Agent Sales System for SMBs.
- It is SOFTWARE, not hardware.
- It automates sales processes: prospecting, outreach, follow-ups, and qualification.
- It does NOT provide cybersecurity, threat detection, or firewall services.


Your goal is to qualify the lead. Ask 1-2 professional questions about their company size, current sales challenges, or timeline. 
Do not offer discounts yet. Be helpful and engaging.
Never invent specific statistics, percentages, SLAs, integrations, pricing models, or deployment timelines. If exact data is unavailable, describe capabilities qualitatively.
If the message contains a [LONG-TERM CRM MEMORY] block, naturally acknowledge the previous conversation (e.g., "Last time we discussed...") before answering.
# AFTER:
If the message contains a [PERSONALITY MODE] block, strictly adapt your tone and style to it.
CRITICAL: NEVER mention cybersecurity, threat detection, firewall, or hardware. ONLY talk about sales automation.

CRITICAL: Use ONLY the following product knowledge. Do NOT hallucinate features from other companies:
{KNOWLEDGE_BASE[:2000]}"""

CLOSER_PROMPT = f"""You are the Lead Closer Agent for Vectra AI. 
Keep your final message concise (under 100 words) and ALWAYS end with a complete sentence.
CRITICAL OUTPUT RULES:
1. Final message must be 2-3 sentences maximum.
2. Always end with a complete sentence and proper punctuation.
3. Only mention a discount if the customer explicitly asks about pricing or discounts; never volunteer the maximum 10% unprompted.
Your goal is to negotiate and close deals professionally. 
Business Rules:
1. Maximum discount allowed is 10%.
2. Never offer negative prices.
Never invent specific statistics, percentages, SLAs, integrations, pricing models, or deployment timelines. If exact data is unavailable, describe capabilities qualitatively.
If the message contains a [PERSONALITY MODE] block, strictly adapt your tone and style to it.
If the message contains a [OUTCOME LEARNING] block, prefer the strategy with the highest success rate.
If the message contains a [LONG-TERM CRM MEMORY] block, naturally acknowledge the previous conversation (e.g., "Last time we discussed...") before answering.
If the user asks for more than 10% discount, politely refuse and offer the maximum 10% or a value-add instead.
CRITICAL: Your final message MUST be exactly 2 sentences maximum, and MUST end with a question like "Shall we proceed?" or "Ready to move forward?"
CRITICAL: Use ONLY the following product knowledge. Do NOT hallucinate features from other companies:
{KNOWLEDGE_BASE[:500]}"""

FINANCE_RULES = "1. Maximum discount allowed is strictly 10%. 2. Prices must never be negative. 3. No unrealistic promises."

# --- Helper: Agent Router ---
async def get_agent_response(agent_type: str, message: str) -> str:
    if agent_type == "MANAGER": prompt = MANAGER_PROMPT
    elif agent_type == "SDR": prompt = SDR_PROMPT
    elif agent_type == "CLOSER": prompt = CLOSER_PROMPT
    else: raise ValueError(f"Unknown agent: {agent_type}")
    return sanitize_ending(await call_fireworks_agent(prompt, message))

@cl.on_chat_start
async def start():
    # Add the Autonomous Pipeline button to the UI
    actions = [
        cl.Action(
            name="run_autonomous_pipeline",
            payload={},
            value="run",
            label="🚀 Run Autonomous Sales Day",
            description="Process all NEW leads in Sheets autonomously"
        ),
        cl.Action(
            name="generate_bi_report",
            payload={},
            value="report",
            label="📊 Generate Strategic BI Report",
            description="CRO-level analysis of your sales performance"
        ),
    ]
    
    await cl.Message(
        content="# ⚡ VECTRA AI — AUTONOMOUS CRO\n👋 Welcome to the **Vectra AI War Room**. I am your autonomous sales team. How can I help you today?",
        author="System",
        actions=actions
    ).send()

@cl.on_message
async def main(message: cl.Message):
    user_msg = message.content

    # SIGNATURE 1: CRM-Native memory lookup (session ID = lead identity)
    lead_id = cl.user_session.get("session_id") or "WALK-IN"
    memory_ctx = build_memory_context(load_lead_memory(lead_id))

    # SIGNATURE 3A: Detect personality and build tone context
    personality = detect_personality(user_msg)
    personality_ctx = build_personality_context(personality)

    # 1. MANAGER AGENT STEP
    try:
        async with cl.Step(name="Manager Agent", type="tool") as manager_step:
            manager_step.output = "Analyzing user intent and routing request..."
            routing_decision = await get_agent_response("MANAGER", user_msg)
            target_agent = "CLOSER" if "CLOSER" in routing_decision.upper() else "SDR"
            manager_step.output = f"Intent classified. Routing to **{target_agent} Agent**."
    except Exception as e:
        print(f"Routing Error: {e}")
        await cl.Message(content="⚠️ System experiencing technical difficulties. Let me connect you with our team or please try again in a moment.", author="System").send()
        return

    # 2. SDR OR CLOSER LOGIC
    if target_agent == "SDR":
        async with cl.Step(name="SDR Agent", type="tool") as sdr_step:
            sdr_step.output = "Qualifying lead and gathering context..."
            sdr_response = await get_agent_response("SDR", personality_ctx + memory_ctx + user_msg)
            sdr_step.output = "Lead qualification complete. Generating response..."

        await cl.Message(content=sdr_response, author="SDR Agent").send()
        save_lead_memory(lead_id, "Direct Chat", user_msg, sdr_response, personality)

    else: # CLOSER
        stats_ctx = compute_strategy_stats()
        max_retries = 2
        attempt = 0
        current_message = stats_ctx + personality_ctx + memory_ctx + user_msg
        final_response = ""

        while attempt <= max_retries:
            # Closer Step
            async with cl.Step(name=f"Closer Agent (Attempt {attempt+1})", type="tool") as closer_step:
                closer_step.output = "Drafting negotiation proposal..."
                closer_response = await get_agent_response("CLOSER", current_message)
                closer_step.output = f"Draft generated: \"{closer_response[:100]}...\""

            # Finance Guardrail Step
            async with cl.Step(name="Finance Guardrail (Gemini Audit)", type="tool") as finance_step:
                finance_step.output = "Auditing proposal against business rules..."
                audit_result = await call_gemini_guardrail(closer_response, FINANCE_RULES)

                if audit_result.is_approved:
                    finance_step.output = f"**APPROVED**. Reason: {audit_result.reason}"
                    final_response = closer_response
                    break
                else:
                    finance_step.output = f"**REJECTED**. Reason: {audit_result.reason}. Triggering self-correction..."
                    attempt += 1
                    current_message = f"REJECTED by Finance. Reason: {audit_result.reason}. Revise your response. Original request: {user_msg}"

        if attempt > max_retries:
            final_response = "I apologize, but I cannot fulfill this request due to strict company policies."
            await cl.Message(content=final_response, author="System Guardrail").send()
            save_lead_memory(lead_id, "Direct Chat", user_msg, final_response, personality)
        else:
            # Zero-Click Execution Step (Real Google Sheets Logging)
            async with cl.Step(name="Zero-Click Execution", type="tool") as exec_step:
                exec_step.output = "Extracting deal data and logging to Google Sheets CRM..."

                # Smart discount extraction: only extract OFFERED discounts, not rejected ones
                import re
                discount_val = 0.0

                # Look for patterns like "offer you X%", "discount of X%", "X% discount"
                offer_patterns = [
                    r'(?:offer|extend|provide|give)\s+(?:you\s+)?(?:a\s+|the\s+)?(\d+)%',
                    r'(?:discount|reduction)\s+(?:of\s+|is\s+)?(\d+)%',
                    r'(\d+)%\s+(?:discount|off|reduction)'
                ]

                # Strip markdown bold markers so "**10%**" reads as "10%"
                clean_response = final_response.replace("*", "").lower()
                for pattern in offer_patterns:
                    match = re.search(pattern, clean_response)
                    if match:
                        discount_val = float(match.group(1))
                        break

                # Cap at 10% maximum (safety net)
                if discount_val > 10:
                    discount_val = 10.0

                success = log_deal_to_sheet(
                    user_msg=user_msg,
                    agent_used="CLOSER",
                    final_response=final_response,
                    status="APPROVED",
                    discount=discount_val,
                    strategy_used=detect_strategy(final_response),
                    deal_outcome="NEGOTIATING",
                    personality=personality,
                )

                if success:
                    exec_step.output = "Deal logged successfully to Google Sheets. (Zero-Click Execution complete)"
                else:
                    exec_step.output = "UI updated, but background logging to Sheets failed. Please check credentials."

            save_lead_memory(lead_id, "Direct Chat", user_msg, final_response, personality)

# ==============================================================================
# UPGRADE A: AUTONOMOUS PIPELINE MODE (Headless Orchestration)
# ==============================================================================
import asyncio

async def process_lead_autonomous(user_msg: str, lead_id: str = "WALK-IN", company_name: str = "Direct Chat") -> dict:
    """Headless orchestration logic for Autonomous Pipeline (No UI steps)."""
    # SIGNATURE 1: Load CRM memory and build context
    memory_ctx = build_memory_context(load_lead_memory(lead_id))
    augmented_msg = memory_ctx + user_msg

    # SIGNATURE 3A: Detect personality and build tone context
    personality = detect_personality(user_msg)
    personality_ctx = build_personality_context(personality)

    # 1. Manager Routing (route on raw message to avoid memory bias)
    routing_decision = await get_agent_response("MANAGER", user_msg)
    target_agent = "CLOSER" if "CLOSER" in routing_decision.upper() else "SDR"

    # 2. SDR Logic
    if target_agent == "SDR":
        response = await get_agent_response("SDR", personality_ctx + augmented_msg)
        save_lead_memory(lead_id, company_name, user_msg, response, personality)
        return {
            "response": response,
            "agent": "SDR",
            "status": "QUALIFYING",
            "discount": 0.0,
            "stage": "QUALIFYING",
        }

    # 3. CLOSER Logic (with Guardrail + Outcome Learning)
    stats_ctx = compute_strategy_stats()
    max_retries = 2
    attempt = 0
    current_message = stats_ctx + personality_ctx + augmented_msg
    final_response = "I apologize, but I cannot fulfill this request due to strict company policies."
    discount_val = 0.0
    status = "REJECTED"
    stage = "LOST"

    while attempt <= max_retries:
        closer_response = await get_agent_response("CLOSER", current_message)
        audit_result = await call_gemini_guardrail(closer_response, FINANCE_RULES)

        if audit_result.is_approved:
            final_response = closer_response
            discount_val = audit_result.extracted_discount if audit_result.extracted_discount <= 10 else 10.0
            status = "APPROVED"
            stage = "NEGOTIATING"
            break

        attempt += 1
        current_message = f"REJECTED by Finance. Reason: {audit_result.reason}. Revise your response. Original request: {user_msg}"

    save_lead_memory(lead_id, company_name, user_msg, final_response, personality)
    log_deal_to_sheet(
        user_msg=user_msg,
        agent_used="CLOSER",
        final_response=final_response,
        status=status,
        discount=discount_val,
        strategy_used=detect_strategy(final_response),
        deal_outcome="NEGOTIATING" if status == "APPROVED" else "LOST",
        personality=personality,
    )
    return {
        "response": final_response,
        "agent": "CLOSER",
        "status": status,
        "discount": discount_val,
        "stage": stage,
    }

PIPELINE_SHEET_NAME = "Lead Pipeline"

def get_pipeline_sheet():
    """Helper to access or auto-create the Lead Pipeline tab."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    try:
        return spreadsheet.worksheet(PIPELINE_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        # Auto-create for hackathon demo robustness
        ws = spreadsheet.add_worksheet(title=PIPELINE_SHEET_NAME, rows="100", cols="20")
        ws.append_row(["Lead_ID", "Lead_Name", "Company", "Email", "Initial_Message", "Stage", "Final_Response", "Status", "Discount", "Timestamp"])
        return ws

async def run_autonomous_sales_day(status_msg=None):
    """Scans 'Lead Pipeline' for NEW leads and processes them autonomously."""
    sheet = get_pipeline_sheet()
    headers = sheet.row_values(1)
    col_map = {h: i for i, h in enumerate(headers)}

    records = sheet.get_all_records()
    updated_rows = 0

    for idx, row in enumerate(records):
        # Defensive normalization: strip whitespace + stray quotes, force uppercase
        stage = str(row.get("Stage", "")).strip().strip('"').strip("'").upper()
        if stage != "NEW":
            continue

        initial_msg = str(row.get("Initial_Message", "Hi")).strip().strip('"').strip("'")
        lead_id = str(row.get("Lead_ID", f"LEAD-{idx+2}")).strip().strip('"').strip("'") or f"LEAD-{idx+2}"
        company = str(row.get("Company", "Unknown")).strip().strip('"').strip("'")

        try:
            result = await process_lead_autonomous(initial_msg, lead_id=lead_id, company_name=company)
            row_idx = idx + 2  # 1-indexed + header offset

            if "Stage" in col_map: sheet.update_cell(row_idx, col_map["Stage"] + 1, result["stage"])
            if "Final_Response" in col_map: sheet.update_cell(row_idx, col_map["Final_Response"] + 1, result["response"])
            if "Status" in col_map: sheet.update_cell(row_idx, col_map["Status"] + 1, result["status"])
            if "Discount" in col_map: sheet.update_cell(row_idx, col_map["Discount"] + 1, result["discount"])
            if "Timestamp" in col_map: sheet.update_cell(row_idx, col_map["Timestamp"] + 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            updated_rows += 1
            if status_msg and updated_rows % 2 == 0:
                status_msg.content = f"⚙️ **Processing...** {updated_rows} leads completed. Working on Lead {lead_id}..."
                await status_msg.update()
        except Exception as e:
            print(f"❌ Pipeline Error on Lead {lead_id}: {e}")
            if "Status" in col_map: sheet.update_cell(idx + 2, col_map["Status"] + 1, "ERROR")

        await asyncio.sleep(1)  # Prevent API rate limits

    return updated_rows

@cl.action_callback("run_autonomous_pipeline")
async def on_run_autonomous_pipeline(action: cl.Action):
    status_msg = await cl.Message(content="🚀 **Autonomous Sales Day** initiated. Scanning 'Lead Pipeline' for NEW leads...", author="System").send()
    try:
        processed_count = await run_autonomous_sales_day(status_msg=status_msg)
        status_msg.content = f"✅ **Pipeline Execution Complete!**\nProcessed and updated **{processed_count}** NEW leads autonomously.\nCheck your Google Sheets 'Lead Pipeline' tab for results."
        await status_msg.update()
    except Exception as e:
        status_msg.content = f"❌ Pipeline Error: {str(e)}"
        await status_msg.update()

# ==============================================================================
# SIGNATURE 1: MEMORY-AWARE NEGOTIATION (CRM-Native Long-Term Memory)
# ==============================================================================
MEMORY_SHEET_NAME = "Lead Memory"

def get_memory_sheet():
    """Access or auto-create the Lead Memory tab."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    try:
        return spreadsheet.worksheet(MEMORY_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=MEMORY_SHEET_NAME, rows="100", cols="10")
        ws.append_row(["Lead_ID", "Company_Name", "Personality_Type", "Interaction_History", "Last_Interaction", "Total_Interactions"])
        return ws

def load_lead_memory(lead_id: str):
    """Lookup CRM memory for a lead. Returns row dict or None."""
    sheet = get_memory_sheet()
    for row in sheet.get_all_records():
        if str(row.get("Lead_ID", "")).strip() == str(lead_id).strip():
            return row
    return None

def build_memory_context(mem) -> str:
    """Build injectable context block from CRM memory."""
    if not mem or not str(mem.get("Interaction_History", "")).strip():
        return ""
    history = str(mem.get("Interaction_History", ""))[-600:]
    total = mem.get("Total_Interactions", 1)
    return (f"[LONG-TERM CRM MEMORY] Returning lead ({total} prior interactions). "
            f"History: {history}. "
            f"IMPORTANT: Naturally acknowledge the previous conversation before answering.\n")

def save_lead_memory(lead_id: str, company_name: str, user_msg: str, agent_response: str, personality: str = ""):
    """Append a deterministic interaction summary to Lead Memory (zero extra LLM cost)."""
    sheet = get_memory_sheet()
    headers = sheet.row_values(1)
    col_map = {h: i for i, h in enumerate(headers)}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Deterministic summary: trim + regex discount detection
    requested_disc = re.search(r'(\d+)\s*%', user_msg)
    disc_note = f" | Asked {requested_disc.group(1)}% discount" if requested_disc else ""
    summary = f"[{now}] Lead: \"{user_msg[:80]}\"{disc_note} -> AI: \"{agent_response[:80]}\""

    records = sheet.get_all_records()
    for idx, row in enumerate(records):
        if str(row.get("Lead_ID", "")).strip() == str(lead_id).strip():
            row_idx = idx + 2
            history = str(row.get("Interaction_History", ""))
            new_history = f"{history} {summary}" if history else summary
            total = int(row.get("Total_Interactions", 0) or 0) + 1
            if "Interaction_History" in col_map: sheet.update_cell(row_idx, col_map["Interaction_History"] + 1, new_history[:4800])
            if "Last_Interaction" in col_map: sheet.update_cell(row_idx, col_map["Last_Interaction"] + 1, now)
            if "Total_Interactions" in col_map:
                sheet.update_cell(row_idx, col_map["Total_Interactions"] + 1, total)
            if personality and "Personality_Type" in col_map:
                sheet.update_cell(row_idx, col_map["Personality_Type"] + 1, personality)
            return

    # New lead: create memory row
    sheet.append_row([lead_id, company_name, personality, summary, now, 1])    

# ==============================================================================
# SIGNATURE 2: OUTCOME LEARNING (Self-Improving Agent)
# ==============================================================================
def detect_strategy(response_text: str) -> str:
    """Deterministic strategy classifier (regex-based, zero LLM cost)."""
    text = response_text.lower()
    has_discount = bool(re.search(r'\d+\s*%', text))
    has_discount = has_discount and ("discount" in text or "off" in text)
    value_words = ["onboarding", "bonus", "package", "include", "complimentary"]
    has_value_add = any(k in text for k in value_words)

    if has_discount and has_value_add:
        return "DISCOUNT_PLUS_VALUE_ADD"
    if has_discount:
        return "DISCOUNT_ONLY"
    return "VALUE_ONLY"

def compute_strategy_stats() -> str:
    """Aggregate CRM Log outcomes into a strategy performance context block."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    sheet = spreadsheet.sheet1

    rows = sheet.get_all_values()
    if not rows:
        return ""

    # Skip header row if present
    if "Strategy_Used" in rows[0]:
        rows = rows[1:]

    stats = {}
    for row in rows:
        strategy = row[6].strip() if len(row) > 6 else ""
        outcome = row[7].strip().upper() if len(row) > 7 else ""
        if not strategy or outcome not in ("CLOSED", "LOST"):
            continue
        entry = stats.setdefault(strategy, {"attempts": 0, "wins": 0})
        entry["attempts"] += 1
        if outcome == "CLOSED":
            entry["wins"] += 1

    if not stats:
        return ""

    ranked = []
    for strategy, entry in stats.items():
        attempts = max(entry["attempts"], 1)
        rate = round(100 * entry["wins"] / attempts)
        ranked.append((rate, strategy, entry))
    ranked.sort(reverse=True)

    lines = []
    for rate, strategy, entry in ranked:
        wins = entry["wins"]
        attempts = entry["attempts"]
        lines.append(f"- {strategy}: {wins}W/{attempts}A ({rate}%)")

    body = " | ".join(lines)
    return (
        "[OUTCOME LEARNING] Historical strategy performance: "
        + body
        + " . Prefer the highest success-rate strategy.\n"
    )          

# ==============================================================================
# SIGNATURE 3A: ADAPTIVE PERSONALITY ENGINE (Micro-Level)
# ==============================================================================
def detect_personality(text: str) -> str:
    """Heuristic personality detection (keyword/emoji based, zero LLM cost)."""
    t = text.lower()

    emoji_pattern = "[\U0001F300-\U0001FAFF\u2600-\u27BF]"
    emoji_count = len(re.findall(emoji_pattern, text))
    exclamations = text.count("!")

    analytical_words = ["data", "metric", "roi", "statistic", "report", "detail", "spec", "benchmark", "proof"]
    driver_words = ["price", "cost", "deadline", "quick", "fast", "bottom line", "straight", "direct", "asap"]
    amiable_words = ["thanks", "thank", "appreciate", "friendly", "team", "relationship", "please", "hope"]

    analytical_score = sum(1 for w in analytical_words if w in t)
    driver_score = sum(1 for w in driver_words if w in t)
    amiable_score = sum(1 for w in amiable_words if w in t)
    expressive_score = emoji_count + (1 if exclamations >= 2 else 0)

    scores = {
        "DRIVER": driver_score,
        "ANALYTICAL": analytical_score,
        "AMIABLE": amiable_score,
        "EXPRESSIVE": expressive_score,
    }

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # Fallback: short message = DRIVER, otherwise AMIABLE
        return "DRIVER" if len(t.split()) <= 8 else "AMIABLE"
    return best 

PERSONALITY_TONES = {
    "DRIVER": "Lead is a DRIVER: be concise, use bullet points, focus on price and bottom line, no small talk.",
    "ANALYTICAL": "Lead is ANALYTICAL: provide data, metrics, ROI logic, and structured details.",
    "AMIABLE": "Lead is AMIABLE: warm tone, build rapport, mention team and partnership.",
    "EXPRESSIVE": "Lead is EXPRESSIVE: enthusiastic tone, match their energy, short vivid sentences.",
}

def build_personality_context(personality: str) -> str:
    """Build injectable tone-adaptation block."""
    tone = PERSONALITY_TONES.get(personality, "")
    if not tone:
        return ""
    return f"[PERSONALITY MODE] Detected lead type: {personality}. {tone}\n"

# ==============================================================================
# SIGNATURE 3B: STRATEGIC BUSINESS INTELLIGENCE (Macro-Level)
# ==============================================================================
async def generate_strategic_bi_report() -> str:
    """Aggregates CRM data and uses DeepSeek (Fireworks) to generate a CRO-level strategic report."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    sheet = spreadsheet.sheet1 # CRM Log

    records = sheet.get_all_records()
    if not records:
        return "No historical deal data available to analyze yet."

    # Deterministic aggregation (header-variation safe)
    def get_field(record, prefix):
        for key, value in record.items():
            if key and key.strip().lower().startswith(prefix):
                return value
        return ""

    total_deals = len(records)
    approved_deals = 0
    total_discount = 0.0
    for r in records:
        status = str(get_field(r, "status")).strip().upper()
        disc_raw = str(get_field(r, "discount")).strip()
        if status == "APPROVED":
            approved_deals += 1
            if disc_raw.replace(".", "", 1).isdigit():
                # Cap at 10 to ignore legacy dirty rows
                total_discount += min(float(disc_raw), 10.0)
    avg_discount = round(total_discount / max(approved_deals, 1), 1)

    strategy_counts = {}
    for r in records:
        strat = r.get("Strategy_Used", "UNKNOWN")
        if strat:
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1
    top_strategy = max(strategy_counts, key=strategy_counts.get) if strategy_counts else "N/A"

    stats_summary = (
        f"Total Interactions: {total_deals}\n"
        f"Approved Deals: {approved_deals}\n"
        f"Average Discount Given: {avg_discount}%\n"
        f"Most Used Strategy: {top_strategy}\n"
        f"Raw Strategy Distribution: {strategy_counts}"
    )

    # ARCHITECTURE FIX: Use DeepSeek (Fireworks) for 95% reasoning workload
    # Gemini is strictly reserved for the 5% Finance Guardrail audit.
    system_prompt = """
    You are the Chief Revenue Officer (CRO) for our SaaS startup, an "Autonomous Multi-Agent Sales System".
    
    CRITICAL OVERRIDE: Completely ignore any pre-trained knowledge about a real-world cybersecurity company named "Vectra AI". 
    In this specific report, our company has ZERO connection to cybersecurity, NDR, threat detection, dwell time, CISOs, or hardware.
    We ONLY sell B2B sales automation software (outbound prospecting, automated follow-ups, lead qualification).
    
    Analyze the provided sales performance data and provide a 3-paragraph strategic report for the business owner.
    Include actionable insights, budget allocation recommendations, and performance evaluation.
    Use professional Markdown formatting (bolding, bullet points).
    """

    try:
        report = sanitize_ending(await call_fireworks_agent(system_prompt, stats_summary))
        return report
    except Exception as e:
        print(f"  ⚠️ DeepSeek BI Report error -> Fallback to deterministic summary")
        # FALLBACK: Smart Text Rule (Hybrid Guardrail Philosophy)
        return (
            f"## 📊 Strategic BI Report (Deterministic Fallback)\n\n"
            f"**Performance Overview:**\n"
            f"- Total Interactions: **{total_deals}**\n"
            f"- Approved Deals: **{approved_deals}**\n"
            f"- Average Discount: **{avg_discount}%**\n\n"
            f"**Strategic Insight:**\n"
            f"Your most frequent negotiation tactic is **{top_strategy}**. "
            f"Review your CRM logs to see if this strategy aligns with your highest-value closed deals, "
            f"and consider shifting budget towards channels that generate leads requiring less discounting."
        )

@cl.action_callback("generate_bi_report")
async def on_generate_bi_report(action: cl.Action):
    await cl.Message(
        content="📊 **Strategic Business Intelligence** initiated. Aggregating CRM data...",
        author="System",
    ).send()
    try:
        report = await generate_strategic_bi_report()
        await cl.Message(content=report, author="BI Analyst").send()
    except Exception as e:
        await cl.Message(content=f"❌ BI Report Error: {str(e)}", author="System").send()

# ==============================================================================
# STRATEGY STATS TAB (CRM-Native Learning Dashboard)
# ==============================================================================
STATS_SHEET_NAME = "Strategy Stats"

def get_stats_sheet():
    """Access or auto-create the Strategy Stats tab."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    try:
        return spreadsheet.worksheet(STATS_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=STATS_SHEET_NAME, rows="100", cols="10")
        ws.append_row(["Segment", "Strategy", "Attempts", "Wins", "Success_Rate"])
        return ws

def refresh_strategy_stats_tab():
    """Aggregate CRM Log into per-segment strategy win rates and write to Stats tab."""
    creds = get_sheets_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1PE1X2yLNF9HEkVwsjSp20fw6k8PQ0BYqeAPLQImjLgY")
    records = spreadsheet.sheet1.get_all_records()

    def get_field(record, prefix):
        for key, value in record.items():
            if key and key.strip().lower().startswith(prefix):
                return value
        return ""

    stats = {}
    for r in records:
        strategy = str(get_field(r, "strategy_used")).strip()
        outcome = str(get_field(r, "deal_outcome")).strip().upper()
        segment = str(get_field(r, "personality")).strip().upper() or "UNKNOWN"
        if not strategy or outcome not in ("CLOSED", "LOST"):
            continue
        key = (segment, strategy)
        entry = stats.setdefault(key, {"attempts": 0, "wins": 0})
        entry["attempts"] += 1
        if outcome == "CLOSED":
            entry["wins"] += 1

    ws = get_stats_sheet()
    ws.clear()
    ws.append_row(["Segment", "Strategy", "Attempts", "Wins", "Success_Rate"])

    rows = []
    for (segment, strategy), entry in stats.items():
        attempts = entry["attempts"]
        wins = entry["wins"]
        rate = round(100 * wins / max(attempts, 1))
        rows.append([segment, strategy, attempts, wins, rate])
    rows.sort(key=lambda x: (x[0], -x[4]))

    if rows:
        ws.append_rows(rows)
    return len(rows)