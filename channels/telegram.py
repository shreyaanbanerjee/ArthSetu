"""Telegram webhook adapter."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Request

from config import TELEGRAM_BOT_TOKEN
from channels.whatsapp_twilio import run_channel_message
from tools.ocr import extract_text_from_image, extract_text_from_pdf
from tools.stt_tts import transcribe_audio_bhashini


router = APIRouter()


@router.post("/webhook/telegram")
async def receive_telegram(request: Request) -> dict[str, str]:
    """Receive Telegram webhook update and reply through Bot API."""
    update = await request.json()
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    if not chat_id:
        return {"status": "ignored"}
    raw_text = await _extract_telegram_text(message)
    if not raw_text:
        raw_text = "Please explain this financial message."
    result = run_channel_message(sender_id=f"telegram:{chat_id}", raw_text=raw_text)
    await send_telegram_text(chat_id, result.get("final_response", "Please try again."))
    return {"status": "ok"}


async def send_telegram_text(chat_id: str, text: str) -> dict[str, Any]:
    """Send a Telegram text message."""
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text[:3900]},
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def _extract_telegram_text(message: dict[str, Any]) -> str:
    """Extract text from Telegram text, voice, photo, or document messages."""
    if message.get("text"):
        return str(message["text"])
    if not TELEGRAM_BOT_TOKEN:
        return ""
    file_id = None
    content_kind = ""
    if message.get("voice"):
        file_id = message["voice"]["file_id"]
        content_kind = "audio"
    elif message.get("document"):
        file_id = message["document"]["file_id"]
        content_kind = "pdf" if message["document"].get("mime_type") == "application/pdf" else "document"
    elif message.get("photo"):
        file_id = message["photo"][-1]["file_id"]
        content_kind = "image"
    if not file_id:
        return ""
    media = await _download_telegram_file(file_id)
    if content_kind == "audio":
        return transcribe_audio_bhashini(media, "hi")
    if content_kind == "pdf":
        return extract_text_from_pdf(media)
    if content_kind == "image":
        return extract_text_from_image(media)
    return ""


async def _download_telegram_file(file_id: str) -> bytes:
    """Download a file from Telegram Bot API."""
    async with httpx.AsyncClient(timeout=30) as client:
        file_response = await client.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile", params={"file_id": file_id})
        file_response.raise_for_status()
        file_path = file_response.json()["result"]["file_path"]
        data_response = await client.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}")
        data_response.raise_for_status()
        return data_response.content
