import os
import re
import json
import httpx
import asyncio
from dotenv import load_dotenv
from google import genai  # ✅ SDK BARU
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

load_dotenv()

class GuardrailDecision(BaseModel):
    is_approved: bool = False
    violation_type: Optional[str] = None
    reason: str = "Unknown"
    extracted_discount: float = 0.0

def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = re.sub(r'```json\s*|\s*```', '', text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            json_str = re.sub(r',\s*}', '}', json_str)
            return json.loads(json_str)
    raise ValueError("No valid JSON object found.")

async def call_fireworks_agent(system_prompt: str, user_message: str, max_retries: int = 4) -> str:
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY not found!")

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": "accounts/fireworks/models/deepseek-v4-pro-0813",
        "messages": [
            {"role": "system", "content": system_prompt + "\n\nIMPORTANT: Always respond in English only, regardless of the language the user or lead uses."},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 131072,
        "top_k": 40,
        "temperature": 0.7,
        "service_tier": "priority"
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                finish_reason = data["choices"][0].get("finish_reason", "unknown")

                # Check if response was properly completed
                valid_ending = content.rstrip().endswith(('.', '!', '?', '"', "'"))
                
                if finish_reason == "stop" and valid_ending:
                    return content
                elif finish_reason == "length" or not valid_ending:
                    # Truncated or incomplete - retry with higher temperature for variation
                    print(f"[VECTRA RETRY] Attempt {attempt + 1}: finish_reason={finish_reason}, ending_valid={valid_ending}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        # Slightly increase temperature for retry to get different response
                        payload["temperature"] = min(payload["temperature"] + 0.1, 0.9)
                        continue
                    else:
                        print(f"[VECTRA WARNING] Truncation persisted - trimming to last complete sentence")
                        # Find last complete sentence (ends with . ! ? followed by space or end)
                        import re
                        # Match sentence endings more robustly
                        matches = list(re.finditer(r'[.!?](?:\s|$)', content))
                        if matches:
                            last_complete = matches[-1]
                            content = content[:last_complete.end()].strip()
                            print(f"[VECTRA TRIM] Trimmed to {len(content)} chars")
                        else:
                            # No complete sentence found, try to find last period anywhere
                            last_period = content.rfind('.')
                            if last_period > 0:
                                content = content[:last_period + 1].strip()
                            print(f"[VECTRA TRIM] Fallback trim applied")
                        return content
                else:
                    return content

        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                raise RuntimeError(f"Fireworks API failed: {str(e)}")
            await asyncio.sleep(2)
    
    raise RuntimeError(f"Fireworks API failed after {max_retries} attempts: {last_error}")

async def call_gemini_guardrail(text_to_audit: str, business_rules: str) -> GuardrailDecision:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found!")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # ✅ PROMPT YANG LEBIH PINTAR: Eksplisit membedakan Penawaran vs Penolakan
        prompt = f"""
        You are a strict Business Compliance Auditor.
        Rules: {business_rules}
        
        Audit this AI Response: "{text_to_audit[:800]}"
        
        CRITICAL INSTRUCTION: 
        If the AI explicitly REFUSES, DENIES, or APOLOGIZES for the excessive discount and does NOT agree to it, the response is SAFE and must be APPROVED. 
        Only REJECT if the AI actually AGREES to give a discount > 10%.
        
        Return ONLY valid JSON: {{"is_approved": bool, "violation_type": str | null, "reason": str, "extracted_discount": float}}
        """

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model='gemini-3.5-flash-lite',
                contents=prompt
            ),
            timeout=8.0 
        )
        
        json_data = extract_json_from_text(response.text)
        return GuardrailDecision(**json_data)
        
    except asyncio.TimeoutError:
        print("  ⚠️ Gemini timeout (8s) -> Fallback to Smart Regex Rule")
        return _hardcoded_guardrail_fallback(text_to_audit)
        
    except Exception as e:
        print(f"  ⚠️ Gemini error -> Fallback to Smart Regex Rule: {str(e)}")
        return _hardcoded_guardrail_fallback(text_to_audit)

def _hardcoded_guardrail_fallback(text: str) -> GuardrailDecision:
    """Layer 2: Smart Regex Rule (Detects Refusals vs Offers)"""
    text_lower = text.lower()
    
    # Deteksi kata-kata penolakan
    refusal_words = ["cannot", "unable", "apologize", "refuse", "not allowed", "not authorized", "i'm afraid", "unfortunately", "must decline"]
    is_refusal = any(word in text_lower for word in refusal_words)

    # Ekstrak angka diskon
    matches = re.findall(r'(\d+)%?\s*(?:discount|off)', text_lower)
        
    if not matches:
        unrealistic_keywords = [
            "lifetime", "forever", "unlimited", "guaranteed", "100% uptime",
            "free maintenance", "no cost", "zero cost"
        ]
        found_unrealistic = [word for word in unrealistic_keywords if word in text_lower]
        
        if found_unrealistic:
            return GuardrailDecision(
                is_approved=False,
                violation_type="unrealistic_promise",
                reason=f"Hard rule: Contains unrealistic promise: {', '.join(found_unrealistic)}",
                extracted_discount=0.0
            )
        
        return GuardrailDecision(
            is_approved=True,
            violation_type=None,
            reason="No discount or unrealistic promises detected.",
            extracted_discount=0.0
        )
    
    max_discount = max([float(m) for m in matches])
    
    # ✅ LOGIKA PINTAR: Jika AI menolak diskon besar, itu AMAN (Approved)
    if is_refusal and max_discount > 10:
        return GuardrailDecision(
            is_approved=True, 
            violation_type=None, 
            reason=f"AI explicitly refused {max_discount}% discount. Safe.", 
            extracted_discount=0.0
        )
    
    # Jika benar-benar menawarkan > 10%, blokir
    if max_discount > 10:
        return GuardrailDecision(is_approved=False, violation_type="excessive_discount", reason=f"Hard rule: {max_discount}% > 10%", extracted_discount=max_discount)
    
    return GuardrailDecision(is_approved=True, violation_type=None, reason=f"Hard rule: {max_discount}% <= 10%. Safe.", extracted_discount=max_discount)

def sanitize_ending(text: str) -> str:
    """Final safety net: never return mid-sentence endings."""
    import re
    text = text.strip()
    applied = False
    if text and text[-1] not in '.!?"\'':
        cuts = list(re.finditer(r'[.!?]\s', text))
        if cuts:
            text = text[:cuts[-1].end()].strip()
            applied = True
        else:
            idx = text.rfind(',')
            if idx > int(len(text) * 0.4):
                text = text[:idx].rstrip() + '.'
                applied = True
    print(f"[VECTRA SANITIZE] applied={applied} tail={text[-25:]!r}", flush=True)
    return text