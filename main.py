"""FastAPI entry point for ArthSetu."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from channels.telegram import router as telegram_router
from channels.whatsapp_twilio import router as twilio_whatsapp_router
from config import FRONTEND_ORIGIN
from core.graph import build_graph
from core.memory import get_latest_session, get_user_profile, update_session, upsert_user_profile


app = FastAPI(title="ArthSetu API", version="1.0.0")
graph = build_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(twilio_whatsapp_router, prefix="/api/v1")
app.include_router(telegram_router, prefix="/api/v1")


class ChatRequest(BaseModel):
    """Request body for demo chat."""

    user_id: str = Field(default="demo-user")
    message: str
    profile_updates: dict[str, Any] = Field(default_factory=dict)


class ProfileUpdateRequest(BaseModel):
    """Request body for profile updates."""

    updates: dict[str, Any]


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "ArthSetu - Paisa Samajho, Zindagi Badlo"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health endpoint."""
    return {"status": "ok", "service": "arthsetu"}


@app.post("/api/v1/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Run a web/PWA message through the graph."""
    profile = get_user_profile(request.user_id)
    if request.profile_updates:
        profile = upsert_user_profile(request.user_id, request.profile_updates)
    state = {
        "session_id": f"{request.user_id}-{time.time()}",
        "user_id": request.user_id,
        "raw_input": request.message,
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
        "ocr_extracted_text": request.message,
    }
    try:
        result = graph.invoke(state)
    except Exception as exc:
        result = {
            **state,
            "error": str(exc),
            "final_response": "I could not process that fully. Please try again with a shorter message or send the document once more.",
        }
    update_session(request.user_id, result)
    return result


@app.get("/api/v1/profile/{user_id}")
async def read_profile(user_id: str) -> dict[str, Any]:
    """Read user profile."""
    return get_user_profile(user_id)


@app.post("/api/v1/profile/{user_id}")
async def update_profile(user_id: str, request: ProfileUpdateRequest) -> dict[str, Any]:
    """Update user profile."""
    return upsert_user_profile(user_id, request.updates)


@app.get("/api/v1/session/{user_id}")
async def read_session(user_id: str) -> dict[str, Any]:
    """Read latest session."""
    return get_latest_session(user_id)


@app.get("/api/v1/history/{user_id}")
async def read_history(user_id: str) -> list[dict[str, Any]]:
    """Read full conversation history."""
    from core.memory import get_full_history
    return get_full_history(user_id)
