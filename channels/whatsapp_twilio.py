"""Twilio WhatsApp webhook adapter."""

from __future__ import annotations

import time
from typing import Any

import httpx

from fastapi import APIRouter, BackgroundTasks, Form
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from config import (
    MAX_WHATSAPP_REPLY_CHARS,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM,
)
from core.graph import build_graph
from core.memory import get_user_profile, update_session, upsert_user_profile
from core.llm import extract_profile_from_text
from tools.ocr import extract_text_from_image, extract_text_from_pdf
from tools.stt_tts import transcribe_audio_bhashini


router = APIRouter()
graph = build_graph()


@router.post("/webhook/whatsapp/twilio")
async def receive_twilio_whatsapp(
    background_tasks: BackgroundTasks,
    From: str = Form(...),  # noqa: N803 - Twilio field name
    Body: str = Form(""),  # noqa: N803
    NumMedia: int = Form(0),  # noqa: N803
    MediaUrl0: str | None = Form(None),  # noqa: N803
    MediaContentType0: str | None = Form(None),  # noqa: N803
) -> Response:
    """Receive a WhatsApp message from Twilio.

    Return an EMPTY TwiML response immediately so Twilio does not time out
    (Twilio requires a reply within 15 s).  The actual processing and reply
    are handled asynchronously by a background task that calls the Twilio
    REST API once the graph finishes.
    """
    caption_text = Body.strip()
    raw_text = caption_text
    is_voice = False
    has_media = bool(NumMedia and MediaUrl0)

    # Capture media bytes synchronously before we background the heavy work
    media_text = ""
    if NumMedia and MediaUrl0:
        try:
            profile_for_lang = get_user_profile(From)
            user_lang = profile_for_lang.get("language", "hi")
            media_bytes = await _download_twilio_media(MediaUrl0)
            media_text, is_voice = _extract_media_text(media_bytes, MediaContentType0, user_lang)
        except Exception as exc:
            media_text = f"Document received, but text extraction failed: {exc}"
        raw_text = "\n\n".join(part for part in [caption_text, media_text] if part.strip())
    if not raw_text:
        raw_text = "Please decode this financial document."

    # ACK Twilio immediately with an empty response
    background_tasks.add_task(
        _process_and_reply, From, raw_text, is_voice, has_media
    )
    return Response(content=str(MessagingResponse()), media_type="application/xml")


def _process_and_reply(sender_id: str, raw_text: str, is_voice: bool, has_media: bool) -> None:
    """Run the ArthSetu graph and send the reply via Twilio REST API."""
    result = run_channel_message(
        sender_id=sender_id, raw_text=raw_text, is_voice=is_voice, has_media=has_media
    )
    reply = (result.get("final_response") or "माफ़ करें, मैं अभी जवाब नहीं दे पाया। कृपया दोबारा भेजें।")[:MAX_WHATSAPP_REPLY_CHARS]
    send_whatsapp_text(to=sender_id, text=reply)


def run_channel_message(sender_id: str, raw_text: str, is_voice: bool = False, has_media: bool = False) -> dict[str, Any]:
    """Run a user message through the ArthSetu graph."""
    profile = get_user_profile(sender_id)

    # ── Profile extraction ──────────────────────────────────────────────────
    # If the user mentions their income, expenses, occupation etc. in plain
    # language (e.g. "my salary is 30k and expenses are 10k, I'm a content
    # creator"), extract those fields and persist them NOW so that every
    # subsequent message — even in a different language — has the correct
    # financial context.
    if not has_media and raw_text.strip():
        extracted = extract_profile_from_text(raw_text)
        if extracted:
            profile = upsert_user_profile(sender_id, extracted)
    # ────────────────────────────────────────────────────────────────────────

    state = {
        "session_id": f"{sender_id}-{time.time()}",
        "user_id": sender_id,
        "raw_input": raw_text,
        "language": profile.get("language", "hi"),
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
    # Persist the language detected in this session back to the profile
    # so that future messages are always answered in the correct language.
    detected_lang = result.get("language")
    if detected_lang and detected_lang != profile.get("language"):
        upsert_user_profile(sender_id, {"language": detected_lang})
    return result


def send_whatsapp_text(to: str, text: str) -> dict[str, Any]:
    """Send an outbound WhatsApp message through Twilio."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"status": "not_configured", "message": "Twilio credentials missing."}
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=to, body=text[:MAX_WHATSAPP_REPLY_CHARS])
        return {"status": "sent", "sid": message.sid}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def _download_twilio_media(url: str) -> bytes:
    """Download Twilio media using basic auth when credentials exist."""
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, auth=auth)
        response.raise_for_status()
        return response.content


def _extract_media_text(media_bytes: bytes, content_type: str | None, language: str = "hi") -> tuple[str, bool]:
    """Extract text from supported media."""
    ctype = (content_type or "").lower()
    if ctype.startswith("audio/"):
        return transcribe_audio_bhashini(media_bytes, language), True
    if ctype in {"application/pdf", "application/octet-stream"}:
        return extract_text_from_pdf(media_bytes), False
    if ctype.startswith("image/"):
        return extract_text_from_image(media_bytes), False
    return "", False
