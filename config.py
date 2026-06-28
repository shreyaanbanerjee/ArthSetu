"""Application configuration for ArthSetu."""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv

load_dotenv(override=True)


APP_ENV: Final[str] = os.getenv("APP_ENV", "local")
DEMO_MODE: Final[bool] = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"}
API_BASE_URL: Final[str] = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_ORIGIN: Final[str] = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# LLM providers
GROQ_API_KEY: Final[str | None] = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY: Final[str | None] = os.getenv("GEMINI_API_KEY")

# Model names
SUTRADHAR_MODEL: Final[str] = os.getenv("SUTRADHAR_MODEL", "llama-3.1-70b-versatile")
PRAHARI_MODEL: Final[str] = os.getenv("PRAHARI_MODEL", "llama-3.1-8b-instant")
BODHAK_MODEL: Final[str] = os.getenv("BODHAK_MODEL", "llama3.1:8b")
SHILPI_MODEL: Final[str] = os.getenv("SHILPI_MODEL", "llama-3.1-70b-versatile")
VIVEK_MODEL: Final[str] = os.getenv("VIVEK_MODEL", "gemini-1.5-flash")

# Infrastructure
REDIS_URL: Final[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL: Final[str | None] = os.getenv("DATABASE_URL")
CHROMADB_PATH: Final[str] = os.getenv("CHROMADB_PATH", "./chroma_db")
OLLAMA_HOST: Final[str] = os.getenv("OLLAMA_HOST", "http://localhost:11434")
RABBITMQ_URL: Final[str] = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")

# DPI and reporting
DPI_MODE: Final[str] = os.getenv("DPI_MODE", "simulation")
NPCI_API_BASE: Final[str | None] = os.getenv("NPCI_API_BASE_URL")
NPCI_MERCHANT_ID: Final[str] = os.getenv("NPCI_MERCHANT_ID", "ARTHSETU-DEMO")
RBI_SACHET_URL: Final[str] = os.getenv("RBI_SACHET_URL", "https://sachet.rbi.org.in")

# WhatsApp via Twilio
WHATSAPP_PROVIDER: Final[str] = os.getenv("WHATSAPP_PROVIDER", "twilio")
TWILIO_ACCOUNT_SID: Final[str | None] = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN: Final[str | None] = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM: Final[str] = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Optional Meta WhatsApp keys
WHATSAPP_TOKEN: Final[str | None] = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID: Final[str | None] = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_VERIFY_TOKEN: Final[str | None] = os.getenv("WHATSAPP_VERIFY_TOKEN")

# Telegram
TELEGRAM_BOT_TOKEN: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")

# Bhashini
BHASHINI_USER_ID: Final[str | None] = os.getenv("BHASHINI_USER_ID")
BHASHINI_API_KEY: Final[str | None] = os.getenv("BHASHINI_API_KEY")
BHASHINI_PIPELINE_URL: Final[str | None] = os.getenv("BHASHINI_PIPELINE_URL")

LANGUAGE_MAP: Final[dict[str, str]] = {
    "hi": "hi",
    "mr": "mr",
    "kn": "kn",
    "ta": "ta",
    "te": "te",
    "bn": "bn",
    "gu": "gu",
    "pa": "pa",
    "or": "or",
    "ml": "ml",
    "as": "as",
    "ur": "ur",
    "en": "en",
}

SESSION_TTL_SECONDS: Final[int] = int(os.getenv("SESSION_TTL_SECONDS", "1800"))
SCAM_CONFIDENCE_THRESHOLD: Final[float] = float(os.getenv("SCAM_CONFIDENCE_THRESHOLD", "0.72"))
APR_WARNING_THRESHOLD: Final[float] = float(os.getenv("APR_WARNING_THRESHOLD", "36.0"))
DEFAULT_LANGUAGE: Final[str] = os.getenv("DEFAULT_LANGUAGE", "hi")
MAX_WHATSAPP_REPLY_CHARS: Final[int] = int(os.getenv("MAX_WHATSAPP_REPLY_CHARS", "1500"))
