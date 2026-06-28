"""Twilio WhatsApp webhook adapter."""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import APIRouter, Form
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
from core.memory import get_user_profile, update_session
from tools.ocr import extract_text_from_image, extract_text_from_pdf
from tools.stt_tts import transcribe_audio_bhashini


router = APIRouter()
graph = build_graph()


@router.post("/webhook/whatsapp/twilio")
async def receive_twilio_whatsapp(
    From: str = Form(...),  # noqa: N803 - Twilio field name
    Body: str = Form(""),  # noqa: N803
    NumMedia: int = Form(0),  # noqa: N803
    MediaUrl0: str | None = Form(None),  # noqa: N803
    MediaContentType0: str | None = Form(None),  # noqa: N803
) -> Response:
    """Receive a WhatsApp message from Twilio and reply with TwiML."""
    caption_text = Body.strip()
    raw_text = caption_text
    is_voice = False
    has_media = bool(NumMedia and MediaUrl0)
    if NumMedia and MediaUrl0:
        try:
            media_bytes = await _download_twilio_media(MediaUrl0)
            media_text, is_voice = _extract_media_text(media_bytes, MediaContentType0)
        except Exception as exc:
            media_text = f"Document received, but text extraction failed: {exc}"
        raw_text = "\n\n".join(part for part in [caption_text, media_text] if part.strip())
    if not raw_text:
        raw_text = "Please decode this financial document."

    result = run_channel_message(sender_id=From, raw_text=raw_text, is_voice=is_voice, has_media=has_media)
    response = MessagingResponse()
    response.message((result.get("final_response") or "I could not prepare a reply. Please try again.")[:MAX_WHATSAPP_REPLY_CHARS])
    return Response(content=str(response), media_type="application/xml")


def run_channel_message(sender_id: str, raw_text: str, is_voice: bool = False, has_media: bool = False) -> dict[str, Any]:
    """Run a user message through the ArthSetu graph."""
    profile = get_user_profile(sender_id)
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


def _extract_media_text(media_bytes: bytes, content_type: str | None) -> tuple[str, bool]:
    """Extract text from supported media."""
    ctype = (content_type or "").lower()
    if ctype.startswith("audio/"):
        return transcribe_audio_bhashini(media_bytes, "hi"), True
    if ctype in {"application/pdf", "application/octet-stream"}:
        return extract_text_from_pdf(media_bytes), False
    if ctype.startswith("image/"):
        return extract_text_from_image(media_bytes), False
    return "", False
