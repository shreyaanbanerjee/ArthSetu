"""Sutradhar orchestrator agent."""

from __future__ import annotations

import json
import re
from typing import Any

from config import DEFAULT_LANGUAGE, GROQ_API_KEY, LANGUAGE_MAP, SUTRADHAR_MODEL


INTENT_LABELS = [
    "scam_check",
    "document",
    "decode",
    "plan",
    "scheme",
    "budget",
    "fasal",
    "income_flex",
    "score",
    "habit",
    "nudge",
    "paisa_padhai",
    "myth",
    "saaf_bolna",
    "general",
]
EMOTION_LABELS = ["calm", "stressed", "urgent", "curious"]


SYSTEM_PROMPT = f"""
You are Sutradhar, the orchestrator of ArthSetu, India's AI financial guardian.
Detect language, classify intent from {INTENT_LABELS}, detect emotional register from {EMOTION_LABELS},
and synthesize agent outputs into one friendly, useful response. Never recommend specific financial products by brand.
For final answers:
- Start with a reassuring human sentence.
- Give the verdict first if fraud risk exists.
- Explain why in simple words.
- Give 2-4 concrete next steps.
- If useful, mention score/scheme/document findings.
- Keep it WhatsApp-friendly: short paragraphs, no jargon, no long tables.
Return only valid JSON.
"""


def sutradhar_node(state: dict[str, Any]) -> dict[str, Any]:
    """Classify the user message and synthesize final response after agents run."""
    raw = state.get("raw_input", "")
    detected_lang = _detect_language(raw)
    agent_outputs = state.get("agent_outputs", {})

    if not state.get("intent"):
        classification = _classify_with_llm(raw, detected_lang) or _classify_locally(raw, detected_lang)
        state["language"] = classification["language"]
        state["intent"] = classification["intent"]
        state["emotional_register"] = classification["emotional_register"]

    if agent_outputs:
        state["final_response"] = _synthesize_with_llm(state) or _synthesize_locally(state)
    return state


def _detect_language(text: str) -> str:
    """Detect ISO language code with a safe fallback."""
    try:
        from langdetect import detect

        code = detect(text)
        return code if code in LANGUAGE_MAP else DEFAULT_LANGUAGE
    except Exception:
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        return "en" if re.search(r"[A-Za-z]", text) else DEFAULT_LANGUAGE


def _classify_with_llm(raw: str, detected_lang: str) -> dict[str, str] | None:
    """Use Groq for intent classification when configured."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=SUTRADHAR_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Return JSON with language, intent, emotional_register, synthesis.\n"
                        f"Detected language hint: {detected_lang}\nUser message: {raw}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content or "{}")
        intent = parsed.get("intent", "general")
        emotion = parsed.get("emotional_register", "calm")
        return {
            "language": parsed.get("language") if parsed.get("language") in LANGUAGE_MAP else detected_lang,
            "intent": intent if intent in INTENT_LABELS else "general",
            "emotional_register": emotion if emotion in EMOTION_LABELS else "calm",
        }
    except Exception:
        return None


def _classify_locally(raw: str, detected_lang: str) -> dict[str, str]:
    """Classify intent with deterministic keyword rules."""
    text = raw.lower()
    keyword_intents = [
        ("scam_check", ["otp", "upi pin", "kyc", "fraud", "scam", "link", "lottery", "refund"]),
        ("document", ["policy", "agreement", "statement", "form 16", "document", "pdf", "decode"]),
        ("scheme", ["scheme", "yojana", "subsidy", "pm kisan", "pension", "benefit"]),
        ("budget", ["budget", "expense", "spend", "save", "saving"]),
        ("fasal", ["fasal", "crop", "kisan", "farmer", "harvest"]),
        ("income_flex", ["gig", "daily wage", "variable income", "irregular income"]),
        ("score", ["score", "arth score", "health"]),
        ("habit", ["habit", "nudge", "remind"]),
        ("paisa_padhai", ["learn", "explain", "samjhao", "what is"]),
        ("myth", ["myth", "true or false", "sach"]),
    ]
    intent = "general"
    for label, words in keyword_intents:
        if any(word in text for word in words):
            intent = label
            break
    emotion = "urgent" if any(word in text for word in ["urgent", "immediately", "now", "abhi", "तुरंत"]) else "calm"
    if any(word in text for word in ["worried", "scared", "problem", "help", "डर", "परेशान"]):
        emotion = "stressed"
    if any(word in text for word in ["?", "how", "kaise", "what", "क्या"]):
        emotion = "curious" if emotion == "calm" else emotion
    return {"language": detected_lang, "intent": intent, "emotional_register": emotion}


def _synthesize_with_llm(state: dict[str, Any]) -> str | None:
    """Use Groq for final response synthesis when configured."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=SUTRADHAR_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Language: {state.get('language', 'hi')}\n"
                        f"Emotion: {state.get('emotional_register', 'calm')}\n"
                        f"User message: {state.get('raw_input', '')}\n"
                        f"Agent outputs: {json.dumps(state.get('agent_outputs', {}), ensure_ascii=False)}\n"
                        "Return JSON with key synthesis only. Make the synthesis friendly and practical, around 120-220 words unless the user only needs a one-line answer."
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        return str(json.loads(response.choices[0].message.content or "{}").get("synthesis", "")).strip() or None
    except Exception:
        return None


def _synthesize_locally(state: dict[str, Any]) -> str:
    """Create a clear deterministic response from agent outputs."""
    outputs = state.get("agent_outputs", {})
    parts: list[str] = ["I checked this carefully for you."]
    prahari = outputs.get("prahari")
    if prahari:
        if prahari.get("scam_detected"):
            flags = prahari.get("red_flags", [])[:4]
            parts.append(
                f"Verdict: this looks risky, so do not click the link or share any OTP, PIN, CVV, Aadhaar, or bank details. "
                f"My confidence is {prahari.get('confidence')}. "
                f"Red flags I noticed: {', '.join(flags) if flags else 'pressure, sensitive data request, or suspicious payment pattern'}."
            )
            parts.append(
                "What to do now: 1. Stop replying to the sender. 2. Block/report the number in WhatsApp or SMS. "
                "3. If money was deducted, contact your bank immediately and save screenshots. "
                "4. Share this warning with family before they act on the same message."
            )
        else:
            parts.append(
                "I did not find a strong scam signal in this message. Still, stay careful: no genuine bank or government service "
                "will ask for OTP, UPI PIN, CVV, or full Aadhaar over chat."
            )
    bodhak = outputs.get("bodhak")
    if bodhak:
        parts.append(str(bodhak.get("plain_summary") or "I decoded the document and listed the key points."))
        if bodhak.get("one_action_now"):
            parts.append(f"Next step: {bodhak['one_action_now']}")
    shilpi = outputs.get("shilpi")
    if shilpi:
        monthly = shilpi.get("monthly_plan")
        parts.append(monthly if isinstance(monthly, str) else "I prepared a practical plan based on your income and needs.")
        roadmap = shilpi.get("action_roadmap") or []
        if roadmap:
            parts.append("Next steps: " + " ".join(str(step) for step in roadmap[:3]))
        schemes = shilpi.get("schemes_to_apply") or []
        if schemes:
            names = [item.get("name", str(item)) if isinstance(item, dict) else str(item) for item in schemes[:3]]
            parts.append(f"Useful schemes to check: {', '.join(names)}.")
    vivek = outputs.get("vivek")
    if vivek:
        score = vivek.get("arth_score", {}).get("score")
        action = vivek.get("arth_score", {}).get("next_best_action")
        if score is not None:
            parts.append(f"Your Arth Score is {score}/100. {action}")
    return "\n\n".join(part for part in parts if part).strip() or "I am ready. Send a message, document, or question about money."
