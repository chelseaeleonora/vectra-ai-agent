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

async def call_fireworks_agent(system_prompt: str, user_message: str, max_retries: int = 2) -> str:
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY not found!")
        
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "model": "accounts/fireworks/models/deepseek-v4-flash-0731",
        "messages": [
            {"role": "system", "content": system_prompt + "\n\nIMPORTANT: Always respond in English only, regardless of the language the user or lead uses."},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 131072,
        "top_k": 40,
        "temperature": 0.7,
        "service_tier": "priority"
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Fireworks API failed: {str(e)}")
            await asyncio.sleep(2)

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
        return GuardrailDecision(is_approved=True, violation_type=None, reason="No discount detected.", extracted_discount=0.0)
    
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