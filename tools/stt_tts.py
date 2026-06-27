"""Speech-to-text and text-to-speech adapters."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import httpx

from config import BHASHINI_API_KEY, BHASHINI_PIPELINE_URL, BHASHINI_USER_ID


def transcribe_audio_bhashini(audio_bytes: bytes, language: str = "hi") -> str:
    """Transcribe audio through Bhashini when configured, otherwise local Whisper."""
    if not audio_bytes:
        return ""
    if BHASHINI_API_KEY and BHASHINI_PIPELINE_URL:
        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {"language": {"sourceLanguage": language}},
                    }
                ],
                "inputData": {"audio": [{"audioContent": base64.b64encode(audio_bytes).decode("ascii")}]},
            }
            headers = {"Authorization": BHASHINI_API_KEY}
            if BHASHINI_USER_ID:
                headers["userID"] = BHASHINI_USER_ID
            response = httpx.post(BHASHINI_PIPELINE_URL, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            return _extract_bhashini_text(data)
        except Exception:
            pass
    return transcribe_audio_local(audio_bytes, language)


def transcribe_audio_local(audio_bytes: bytes, language: str = "hi") -> str:
    """Transcribe audio using faster-whisper when installed."""
    try:
        from faster_whisper import WhisperModel

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)
        try:
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(tmp_path), language=language if language != "en" else "en")
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception:
        return ""


def synthesise_speech_bhashini(text: str, language: str = "hi") -> bytes:
    """Synthesize speech through Bhashini when configured, otherwise return empty bytes."""
    if not text.strip():
        return b""
    if BHASHINI_API_KEY and BHASHINI_PIPELINE_URL:
        try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {"language": {"sourceLanguage": language}},
                    }
                ],
                "inputData": {"input": [{"source": text}]},
            }
            headers = {"Authorization": BHASHINI_API_KEY}
            if BHASHINI_USER_ID:
                headers["userID"] = BHASHINI_USER_ID
            response = httpx.post(BHASHINI_PIPELINE_URL, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            audio_b64 = _extract_bhashini_audio(data)
            return base64.b64decode(audio_b64) if audio_b64 else b""
        except Exception:
            return b""
    return b""


def _extract_bhashini_text(data: dict) -> str:
    """Extract text from common Bhashini pipeline response shapes."""
    try:
        outputs = data.get("pipelineResponse", [{}])[0].get("output", [])
        return str(outputs[0].get("source", "")).strip() if outputs else ""
    except Exception:
        return ""


def _extract_bhashini_audio(data: dict) -> str:
    """Extract base64 audio from common Bhashini pipeline response shapes."""
    try:
        audio = data.get("pipelineResponse", [{}])[0].get("audio", [])
        return str(audio[0].get("audioContent", "")) if audio else ""
    except Exception:
        return ""
