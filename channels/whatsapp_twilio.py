"""Twilio WhatsApp webhook adapter."""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import httpx

from fastapi import APIRouter, BackgroundTasks, Form
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from config import (
    DEFAULT_LANGUAGE,
    MAX_WHATSAPP_REPLY_CHARS,
    SUTRADHAR_MODEL,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM,
)
from core.graph import build_graph
from core.memory import get_user_profile, update_session, upsert_user_profile
from core.llm import extract_profile_from_text, call_llm
from tools.ocr import extract_text_from_image, extract_text_from_pdf
from tools.stt_tts import transcribe_audio_bhashini


router = APIRouter()
graph = build_graph()

_RESET_PHRASES = {"reset", "restart"}


def _is_reset(text: str) -> bool:
    t = text.strip().lower()
    return t in _RESET_PHRASES or t.startswith("join ")


def _detect_lang(text: str) -> str:
    from agents.sutradhar import _detect_language
    return _detect_language(text)


def _translate(text_en: str, language: str) -> str:
    if not language or language == "en":
        return text_en
    prompt = (
        f"Translate the following English text to the language with ISO code '{language}'. "
        f"Output only the translated text, nothing else.\n\nText: {text_en}"
    )
    try:
        result = call_llm(prompt, "You are a professional translator.", "text", SUTRADHAR_MODEL)
        return result.strip() if result else text_en
    except Exception:
        return text_en


@router.post("/webhook/whatsapp/twilio")
async def receive_twilio_whatsapp(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    MediaUrl0: str | None = Form(None),
    MediaContentType0: str | None = Form(None),
) -> Response:
    """Receive a WhatsApp message and hand off to background processing."""
    caption_text = Body.strip()
    raw_text = caption_text
    is_voice = False
    has_media = bool(NumMedia and MediaUrl0)

    if NumMedia and MediaUrl0:
        try:
            profile_for_lang = get_user_profile(From)
            user_lang = profile_for_lang.get("language", DEFAULT_LANGUAGE)
            media_bytes = await _download_twilio_media(MediaUrl0)
            media_text, is_voice, audio_lang = _extract_media_text(
                media_bytes, MediaContentType0, user_lang
            )
            if audio_lang:
                upsert_user_profile(From, {"language": audio_lang})
        except Exception as exc:
            media_text = f"[Media error: {exc}]"
            audio_lang = None
        raw_text = "\n\n".join(p for p in [caption_text, media_text] if p.strip())

    if not raw_text:
        raw_text = "Please decode this financial document."

    background_tasks.add_task(_process_and_reply, From, raw_text, is_voice, has_media)
    return Response(content=str(MessagingResponse()), media_type="application/xml")


import logging as _logging
_log = _logging.getLogger("arthsetu.whatsapp")


def _process_and_reply(
    sender_id: str, raw_text: str, is_voice: bool, has_media: bool
) -> None:
    import traceback

    def _send_wait():
        send_whatsapp_text(to=sender_id, text="Still working on your request...")

    timer = threading.Timer(15.0, _send_wait)
    timer.start()
    try:
        result = run_channel_message(
            sender_id=sender_id, raw_text=raw_text, is_voice=is_voice, has_media=has_media
        )
        reply = (
            result.get("final_response") or "Sorry, I could not generate a response. Please try again."
        )[:MAX_WHATSAPP_REPLY_CHARS]
        send_whatsapp_text(to=sender_id, text=reply)
    except Exception as e:
        print(f"CRASH in _process_and_reply: {e}")
        _log.error("_process_and_reply crashed:\n" + traceback.format_exc())
        try:
            send_whatsapp_text(to=sender_id, text="Something went wrong on our end. Please try again.")
        except Exception:
            pass
    finally:
        timer.cancel()


def run_channel_message(
    sender_id: str,
    raw_text: str,
    is_voice: bool = False,
    has_media: bool = False,
) -> dict[str, Any]:
    profile = get_user_profile(sender_id)
    onboarding_step = profile.get("onboarding_step", 0)
    text = raw_text.strip()

    # Reset / Join handler
    if _is_reset(text):
        new_profile = {
            "onboarding_step": 1,
            "name": "",
            "occupation": "",
            "monthly_income_inr": 0,
            "language": DEFAULT_LANGUAGE,
        }
        upsert_user_profile(sender_id, new_profile)
        return {
            "final_response": "Welcome to ArthSetu! I'm your personal financial guardian.\nWhat's your name?",
            "language": DEFAULT_LANGUAGE,
        }

    # Onboarding steps 0-3
    if onboarding_step < 4:
        lang = _detect_lang(text) if text else DEFAULT_LANGUAGE
        if lang != profile.get("language"):
            upsert_user_profile(sender_id, {"language": lang})

        if onboarding_step == 0:
            upsert_user_profile(sender_id, {"onboarding_step": 1, "language": lang})
            msg = _translate("Welcome to ArthSetu! I'm your personal financial guardian.\nWhat's your name?", lang)
            return {"final_response": msg, "language": lang}

        if onboarding_step == 1:
            upsert_user_profile(sender_id, {"name": text, "onboarding_step": 2})
            msg = _translate(f"Nice to meet you, {text}! What is your occupation or profession?", lang)
            return {"final_response": msg, "language": lang}

        if onboarding_step == 2:
            upsert_user_profile(sender_id, {"occupation": text, "onboarding_step": 3})
            msg = _translate("Got it! What is your approximate monthly income? (e.g. '25000' or '25k')", lang)
            return {"final_response": msg, "language": lang}

        if onboarding_step == 3:
            extracted = extract_profile_from_text(text) or {}
            updates: dict[str, Any] = {"onboarding_step": 4}
            updates.update(extracted)
            if "monthly_income_inr" not in updates:
                nums = re.findall(r"\d+", text.replace(",", ""))
                if nums:
                    val = int(nums[0])
                    tl = text.lower()
                    if "lakh" in tl or "lac" in tl:
                        val *= 100_000
                    elif "k" in tl:
                        val *= 1_000
                    updates["monthly_income_inr"] = val
            upsert_user_profile(sender_id, updates)
            msg = _translate("Your profile is all set up! How can I help you with your finances today?", lang)
            return {"final_response": msg, "language": lang}

    # Main graph (post-onboarding)
    # Re-read profile in case audio_lang was updated upstream
    profile = get_user_profile(sender_id)
    lang = profile.get("language", DEFAULT_LANGUAGE)

    # Detect language from text; audio language already saved takes precedence
    if text and not is_voice:
        text_lang = _detect_lang(text)
        if text_lang and text_lang != lang:
            lang = text_lang
            upsert_user_profile(sender_id, {"language": lang})
            profile = {**profile, "language": lang}

    # Extract financial facts from message
    if not has_media and text:
        extracted = extract_profile_from_text(text)
        if extracted:
            profile = upsert_user_profile(sender_id, extracted)

    state = {
        "session_id": f"{sender_id}-{time.time()}",
        "user_id": sender_id,
        "raw_input": raw_text,
        "language": lang,
        "intent": "",
        "emotional_register": "calm",
        "agent_outputs": {},
        "final_response": "",
        "tts_audio_b64": None,
        "upi_action": None,
        "scam_detected": False,
        "scheme_matches": [],
        "arth_score_update": None,
        "error": None,
        "user_profile": profile,
        "ocr_extracted_text": raw_text,
        "is_voice": is_voice,
        "has_media": has_media,
    }

    result = graph.invoke(state)
    update_session(sender_id, result)

    result_lang = result.get("language")
    if result_lang and result_lang != profile.get("language"):
        upsert_user_profile(sender_id, {"language": result_lang})

    return result


def send_whatsapp_text(to: str, text: str) -> dict[str, Any]:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("send_whatsapp_text ERROR: Missing Twilio credentials")
        return {"status": "not_configured"}
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=to,
            body=text[:MAX_WHATSAPP_REPLY_CHARS],
        )
        print(f"Twilio msg sent successfully: {msg.sid}")
        return {"status": "sent", "sid": msg.sid}
    except Exception as exc:
        print(f"Twilio error in send_whatsapp_text: {exc}")
        return {"status": "error", "message": str(exc)}


async def _download_twilio_media(url: str) -> bytes:
    auth = (
        (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        else None
    )
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, auth=auth)
        response.raise_for_status()
        return response.content


def _extract_media_text(
    media_bytes: bytes, content_type: str | None, language: str = "en"
) -> tuple[str, bool, str | None]:
    ctype = (content_type or "").lower()
    if ctype.startswith("audio/"):
        text, detected_lang = transcribe_audio_bhashini(media_bytes, language)
        return text, True, detected_lang
    if ctype in {"application/pdf", "application/octet-stream"}:
        return extract_text_from_pdf(media_bytes), False, None
    if ctype.startswith("image/"):
        return extract_text_from_image(media_bytes), False, None
    return "", False, None
