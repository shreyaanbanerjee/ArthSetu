"""Sutradhar orchestrator agent."""

from __future__ import annotations

import json
import re
from typing import Any

from config import DEFAULT_LANGUAGE, LANGUAGE_MAP, SUTRADHAR_MODEL
from core.llm import call_llm, format_user_persona


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
    "pwa_link",
    "general",
]
# We'll import json here to ensure it's available for classification/synthesis parsing
import json
EMOTION_LABELS = ["calm", "stressed", "urgent", "curious"]


SYSTEM_PROMPT_CLASS = f"""
You are Sutradhar, the orchestrator of ArthSetu, India's AI financial guardian.
Detect language, classify intent from {INTENT_LABELS}, and detect emotional register from {EMOTION_LABELS}.
Return only valid JSON.
"""


def sutradhar_node(state: dict[str, Any]) -> dict[str, Any]:
    """Classify the user message and synthesize final response after agents run."""
    raw = state.get("raw_input", "")
    detected_lang = _detect_language(raw)
    agent_outputs = state.get("agent_outputs", {})
    profile = state.get("user_profile", {})

    if not state.get("intent"):
        classification = _classify_with_llm(raw, detected_lang, profile) or _classify_locally(raw, detected_lang)
        state["language"] = classification["language"]
        state["intent"] = classification["intent"]
        state["emotional_register"] = classification["emotional_register"]

    if state.get("intent") == "pwa_link":
        from config import FRONTEND_ORIGIN
        lang = state.get("language", "en")
        msg = (
            f"अर्थसेतू ॲप येथे वापरा:\n{FRONTEND_ORIGIN}" if lang == "mr" 
            else f"अर्थसेतु ऐप यहाँ उपयोग करें:\n{FRONTEND_ORIGIN}" if lang == "hi"
            else f"You can access the ArthSetu App here:\n{FRONTEND_ORIGIN}"
        )
        state["final_response"] = msg
    elif agent_outputs:
        state["final_response"] = _synthesize_with_llm(state) or _synthesize_locally(state)
    return state


_lingua_detector = None

def _get_lingua_detector():
    global _lingua_detector
    if _lingua_detector is None:
        try:
            from lingua import Language, LanguageDetectorBuilder
            languages = [
                Language.ENGLISH, Language.HINDI, Language.MARATHI, 
                Language.BENGALI, Language.GUJARATI, Language.PUNJABI,
                Language.TAMIL, Language.TELUGU, Language.URDU
            ]
            _lingua_detector = LanguageDetectorBuilder.from_languages(*languages).build()
        except ImportError:
            pass
    return _lingua_detector

def _detect_language(text: str) -> str:
    """Detect ISO language code with lingua-language-detector (highly accurate)."""
    import string
    clean_text = text.strip().lower().strip(string.punctuation)
    if clean_text in {"hi", "hello", "hey", "test", "pwa", "app"}:
        return "en"
        
    detector = _get_lingua_detector()
    if detector:
        try:
            lang = detector.detect_language_of(text)
            if lang:
                code = lang.iso_code_639_1.name.lower()
                return code if code in LANGUAGE_MAP else DEFAULT_LANGUAGE
        except Exception:
            pass

    # Fallback if lingua fails or is missing
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    return "en" if re.search(r"[A-Za-z]", text) else DEFAULT_LANGUAGE


def _classify_with_llm(raw: str, detected_lang: str, profile: dict[str, Any]) -> dict[str, str] | None:
    """Use Gemini/Groq for intent classification tailored with user persona context."""
    user_persona = format_user_persona(profile)

    system_prompt = f"""You are Sutradhar, the orchestrator of ArthSetu, India's AI financial guardian.
Detect language, classify intent from {INTENT_LABELS}, and detect emotional register from {EMOTION_LABELS}.

{user_persona}

Analyze the message under the user's financial profile.
CRITICAL: If the user explicitly asks to speak in a specific language (e.g. 'speak in Marathi', 'मराठीत बोला'), you MUST change the 'language' field to that language's ISO code (e.g. 'mr', 'hi', 'en', 'bn', 'gu', 'ta', 'te', 'pa', 'ur'). Do not just echo the language they typed in if they are requesting a switch.
Return only valid JSON.
"""

    prompt = (
        "Return JSON with keys: language, intent, emotional_register.\n"
        f"Detected language hint: {detected_lang}\n"
        f"User message: {raw}"
    )

    try:
        response_text = call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            model=SUTRADHAR_MODEL
        )
        if not response_text:
            return None

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        parsed = json.loads(cleaned_text)
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
        ("pwa_link", ["pwa", "app", "link", "show me the pwa"]),
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
    """Use Gemini/Groq for final response synthesis incorporating user persona."""
    profile = state.get("user_profile", {})
    user_persona = format_user_persona(profile)

    system_prompt = f"""You are Sutradhar, the orchestrator of ArthSetu, India's AI financial guardian.
Your PRIMARY GOAL is to directly answer the user's question or address their input. Never recommend specific financial products by brand.

{user_persona}

For final answers:
- **Directly answer the user's question first.** If they ask about KYC, explain KYC. If they ask about a scheme, explain the scheme. Do NOT ignore their question.
- ONLY mention fraud/scam if a scam is actually detected or the user asked about it. Otherwise, stay completely silent about fraud/security.
- ONLY provide deep financial analysis or Arth Score details if the user explicitly asked about their finances, budget, or score.
- Do NOT pad your answer with unsolicited advice about their budget or emergency fund unless they asked for it.
- Give 2-4 concrete next steps only if appropriate for the query.
- State the Arth Score exactly out of 100 as provided (e.g., 70/100) ONLY if relevant to the query.
- Keep it WhatsApp-friendly: short paragraphs, no jargon, no long tables.
- Synthesize based on the user's specific context (e.g. adjust tone/actions if they are a low-income farmer or have high debt).
- For any Indian regional language (like mr, hi, bn, gu, pa, ta, te, ur, kn, ml), you MUST output the response in its native authentic script (e.g., Devanagari, Bengali, Tamil, etc.).
- Do NOT use the Latin/English alphabet to write out regional languages (no transliteration/Hinglish).
- If language is en (English), answer in English.
Return only valid JSON with key 'synthesis' only.
"""

    prompt = (
        f"Language: {state.get('language', 'hi')}\n"
        f"Emotion: {state.get('emotional_register', 'calm')}\n"
        f"User message: {state.get('raw_input', '')}\n"
        f"Agent outputs: {json.dumps(state.get('agent_outputs', {}), ensure_ascii=False)}\n"
        "Return JSON with key synthesis only. Make the synthesis friendly and practical. Use the requested language exactly. Do NOT mention agent findings if they are irrelevant to the user message."
    )

    try:
        response_text = call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json",
            model=SUTRADHAR_MODEL
        )
        if not response_text:
            return None

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        parsed = json.loads(cleaned_text)
        return str(parsed.get("synthesis", "")).strip() or None
    except Exception:
        return None


def _synthesize_locally(state: dict[str, Any]) -> str:
    """Create a clear deterministic response from agent outputs."""
    outputs = state.get("agent_outputs", {})
    lang = state.get("language", "en")
    parts: list[str] = [_t(lang, "checked")]
    prahari = outputs.get("prahari")
    if prahari:
        if prahari.get("scam_detected"):
            flags = prahari.get("red_flags", [])[:4]
            parts.append(
                _t(lang, "scam_verdict").format(confidence=prahari.get("confidence"), flags=", ".join(flags) if flags else _t(lang, "generic_flags"))
            )
            parts.append(
                _t(lang, "scam_steps")
            )
        elif state.get("intent") == "scam_check" or prahari.get("confidence", 0) >= 0.35 or prahari.get("red_flags"):
            parts.append(
                _t(lang, "clear_scam")
            )
    bodhak = outputs.get("bodhak")
    if bodhak:
        parts.append(str(bodhak.get("plain_summary") or "I decoded the document and listed the key points."))
        if bodhak.get("one_action_now"):
            parts.append(f"{_t(lang, 'next_step')}: {bodhak['one_action_now']}")
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
            parts.append(f"{_t(lang, 'schemes')}: {', '.join(names)}.")
    vivek = outputs.get("vivek")
    if vivek:
        score = vivek.get("arth_score", {}).get("score")
        action = vivek.get("arth_score", {}).get("next_best_action")
        if score is not None:
            parts.append(f"{_t(lang, 'score')} {score}/100. {action}")
    return "\n\n".join(part for part in parts if part).strip() or "I am ready. Send a message, document, or question about money."


def _t(language: str, key: str) -> str:
    """Tiny fallback phrasebook for non-LLM responses."""
    mr = {
        "checked": "मी हे काळजीपूर्वक तपासले.",
        "scam_verdict": "निर्णय: हे धोकादायक वाटते.\n\nकाय करू नका: लिंक उघडू नका आणि OTP, UPI PIN, CVV, आधार किंवा बँक माहिती शेअर करू नका.\n\nविश्वास: {confidence}\nलाल चिन्हे: {flags}",
        "generic_flags": "घाई लावणे किंवा संवेदनशील माहिती मागणे",
        "scam_steps": "आता काय करा:\n1. त्या व्यक्तीला उत्तर देऊ नका.\n2. नंबर ब्लॉक/रिपोर्ट करा.\n3. पैसे गेले असल्यास लगेच बँकेशी संपर्क करा.\n4. स्क्रीनशॉट जतन करा.",
        "clear_scam": "या संदेशात मोठा फसवणुकीचा संकेत दिसत नाही.",
        "next_step": "पुढचे पाऊल",
        "schemes": "तपासण्यासारख्या योजना",
        "score": "तुमचा Arth Score आहे",
    }
    en = {
        "checked": "I checked this carefully.",
        "scam_verdict": "Verdict: this looks risky.\n\nDo not click the link or share OTP, UPI PIN, CVV, Aadhaar, or bank details.\n\nConfidence: {confidence}\nRed flags: {flags}",
        "generic_flags": "pressure or sensitive data request",
        "scam_steps": "What to do now:\n1. Stop replying.\n2. Block/report the number.\n3. If money was deducted, contact your bank immediately.\n4. Save screenshots.",
        "clear_scam": "I did not find a strong scam signal in this message.",
        "next_step": "Next step",
        "schemes": "Useful schemes to check",
        "score": "Your Arth Score is",
    }
    return (mr if language == "mr" else en).get(key, en[key])
