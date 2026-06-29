"""Speech-to-text and text-to-speech adapters."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import httpx

from config import BHASHINI_API_KEY, BHASHINI_PIPELINE_URL, BHASHINI_USER_ID


def transcribe_audio_bhashini(audio_bytes: bytes, language: str = "hi") -> tuple[str, str | None]:
    """Transcribe audio through Bhashini when configured, otherwise local Whisper."""
    if not audio_bytes:
        return "", None
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
            return _extract_bhashini_text(data), language
        except Exception:
            pass
    return transcribe_audio_local(audio_bytes, language)


def transcribe_audio_local(audio_bytes: bytes, language: str = "hi") -> tuple[str, str | None]:
    """Transcribe audio using faster-whisper (open-source) and detect language from text."""
    import logging
    logger = logging.getLogger("arthsetu.stt")
    
    try:
        from faster_whisper import WhisperModel

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)
        try:
            # We use base, but it's prone to audio-level language misclassification.
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(str(tmp_path), language=None)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            
            # The crucial fix: Ignore info.language (which hallucinates 'ur' for Marathi)
            # Detect language directly from the transcribed text script/words instead!
            from agents.sutradhar import _detect_language
            detected_lang = _detect_language(text) if text else "hi"
            
            return text, detected_lang
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"faster-whisper failed: {e}. Falling back to Gemini.")
        from config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content([
                    "You are a strict transcriber. Transcribe the following audio EXACTLY as spoken. Do NOT translate it to English or any other language. If the audio is in Marathi, output Marathi text in Devanagari script. If Hindi, output Hindi. Output ONLY the transcription, absolutely nothing else.",
                    {"mime_type": "audio/ogg", "data": audio_bytes}
                ])
                text_out = response.text.strip()
                from agents.sutradhar import _detect_language
                return text_out, _detect_language(text_out)
            except Exception as gemini_err:
                logger.error(f"Gemini fallback failed: {gemini_err}")
        return "", None


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
