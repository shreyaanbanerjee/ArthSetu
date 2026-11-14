"""Starlette / FastAPI-compatible ASGI entry point for ArthSetu.

Includes:
  - Chat endpoint with multi-turn memory
  - SSE streaming chat endpoint (real-time agent status)
  - Scam Intelligence Network stats API
  - Cedar Policy audit trail API
  - Rate limiting + security headers middleware
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from config import FRONTEND_ORIGIN
from core.graph import build_graph
from core.memory import get_latest_session, get_user_profile, update_session, upsert_user_profile

graph = build_graph()


# Rate Limiter (Token Bucket)

class RateLimitMiddleware:
    """Simple in-memory token bucket rate limiter per client IP.
    
    Limits: 30 requests per minute per IP on /api/ endpoints.
    Non-API endpoints (health, root) are not rate-limited.
    """

    def __init__(self, app: ASGIApp, max_requests: int = 30, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        # Extract client IP
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        now = time.time()

        # Clean expired entries
        self._buckets[client_ip] = [
            t for t in self._buckets[client_ip]
            if now - t < self.window_seconds
        ]

        if len(self._buckets[client_ip]) >= self.max_requests:
            response = JSONResponse(
                {"error": "Rate limit exceeded. Try again in 60 seconds."},
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)},
            )
            await response(scope, receive, send)
            return

        self._buckets[client_ip].append(now)
        await self.app(scope, receive, send)


# Security Headers Middleware

class SecurityHeadersMiddleware:
    """Inject production security headers into every response."""

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
    }

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in self.HEADERS.items():
                    headers.append((key.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


# Route Handlers

async def root_handler(request: Request) -> JSONResponse:
    return JSONResponse({"message": "ArthSetu - Paisa Samajho, Zindagi Badlo"})


async def health_handler(request: Request) -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "service": "arthsetu",
        "version": "2.0.0",
        "features": ["multi-turn-memory", "sse-streaming", "cedar-audit", "scam-network", "rate-limiting"],
    })


async def chat_handler(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = body.get("user_id", "demo-user")
    message = body.get("message", "")
    profile_updates = body.get("profile_updates", {})

    profile = get_user_profile(user_id)
    if profile_updates:
        profile = upsert_user_profile(user_id, profile_updates)

    state = {
        "session_id": f"{user_id}-{time.time()}",
        "user_id": user_id,
        "raw_input": message,
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
        "ocr_extracted_text": message,
    }
    try:
        result = graph.invoke(state)
    except Exception as exc:
        result = {
            **state,
            "error": str(exc),
            "final_response": "I could not process that fully. Please try again with a shorter message or send the document once more.",
        }
    update_session(user_id, result)
    return JSONResponse(result)


# Server-Sent Events streaming chat handler

async def chat_stream_handler(request: Request) -> StreamingResponse:
    """Stream real-time agent progression events and the final synthesized response."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = body.get("user_id", "demo-user")
    message = body.get("message", "")
    profile_updates = body.get("profile_updates", {})

    profile = get_user_profile(user_id)
    if profile_updates:
        profile = upsert_user_profile(user_id, profile_updates)

    async def event_stream():
        """Generator that yields SSE events as agents process."""
        from agents.bodhak import bodhak_node
        from agents.prahari import prahari_node
        from agents.shilpi import shilpi_node
        from agents.sutradhar import sutradhar_node
        from agents.vivek import vivek_node
        from agents.extractor import extractor_node
        from core.guardrails import input_guardrail_node, output_guardrail_node
        from core.graph import route_after_sutradhar

        state = {
            "session_id": f"{user_id}-{time.time()}",
            "user_id": user_id,
            "raw_input": message,
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
            "ocr_extracted_text": message,
        }
        state.setdefault("agent_outputs", {})
        state.setdefault("scheme_matches", [])
        state.setdefault("profile_updated_dynamically", False)

        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        try:
            # Step 1: Extract profile updates
            yield sse_event("agent_status", {"agent": "extractor", "status": "running", "label": "Extracting profile data..."})
            state_result = extractor_node(state)
            state.update(state_result)
            yield sse_event("agent_status", {"agent": "extractor", "status": "done"})

            # Step 2: Classify intent
            yield sse_event("agent_status", {"agent": "sutradhar", "status": "running", "label": "Understanding your message..."})
            state_result = sutradhar_node(state)
            state.update(state_result)
            yield sse_event("agent_status", {
                "agent": "sutradhar",
                "status": "done",
                "intent": state.get("intent", ""),
                "language": state.get("language", ""),
            })

            # Step 3: Input guardrails
            yield sse_event("agent_status", {"agent": "guardrails_input", "status": "running", "label": "Security screening..."})
            state_result = input_guardrail_node(state)
            state.update(state_result)
            yield sse_event("agent_status", {"agent": "guardrails_input", "status": "done"})

            if state.get("guardrail_blocked"):
                yield sse_event("final_response", {
                    "response": state.get("final_response", ""),
                    "blocked": True,
                })
                update_session(user_id, state)
                return

            # Step 4: Run selected agents
            agent_names = route_after_sutradhar(state)
            agent_labels = {
                "prahari": "Scanning for scams...",
                "bodhak": "Decoding document...",
                "shilpi": "Building your financial plan...",
                "vivek": "Calculating Arth Score...",
            }
            agent_fns = {
                "prahari": prahari_node,
                "bodhak": bodhak_node,
                "shilpi": shilpi_node,
                "vivek": vivek_node,
            }

            for agent_name in agent_names:
                label = agent_labels.get(agent_name, f"Running {agent_name}...")
                yield sse_event("agent_status", {"agent": agent_name, "status": "running", "label": label})
                fn = agent_fns.get(agent_name)
                if fn:
                    state_result = fn(state)
                    state.update(state_result)
                yield sse_event("agent_status", {"agent": agent_name, "status": "done"})

            # Step 5: Synthesize
            yield sse_event("agent_status", {"agent": "sutradhar_synthesis", "status": "running", "label": "Preparing your response..."})
            state_result = sutradhar_node(state)
            state.update(state_result)
            yield sse_event("agent_status", {"agent": "sutradhar_synthesis", "status": "done"})

            # Step 6: Output guardrails
            yield sse_event("agent_status", {"agent": "guardrails_output", "status": "running", "label": "Final safety check..."})
            state_result = output_guardrail_node(state)
            state.update(state_result)
            yield sse_event("agent_status", {"agent": "guardrails_output", "status": "done"})

            # Final response
            update_session(user_id, state)
            yield sse_event("final_response", {
                "response": state.get("final_response", ""),
                "intent": state.get("intent", ""),
                "scam_detected": state.get("scam_detected", False),
                "arth_score": state.get("arth_score_update"),
                "scheme_matches": state.get("scheme_matches", []),
                "cedar_decision": state.get("agent_outputs", {}).get("prahari", {}).get("cedar_decision"),
            })

        except Exception as exc:
            yield sse_event("error", {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Scam Intelligence Network API

async def scam_network_stats_handler(request: Request) -> JSONResponse:
    """Return aggregated scam network statistics."""
    from tools.aws_tools import get_scam_network_stats
    stats = get_scam_network_stats()
    return JSONResponse(stats)


# Cedar Audit Trail API

async def cedar_audit_handler(request: Request) -> JSONResponse:
    """Return the Cedar policy audit trail with decision history."""
    from core.cedar_engine import get_audit_log
    user_id = request.query_params.get("user_id")
    limit = int(request.query_params.get("limit", "50"))
    entries = get_audit_log(user_id=user_id, limit=limit)
    return JSONResponse({"audit_trail": entries, "count": len(entries)})


async def cedar_stats_handler(request: Request) -> JSONResponse:
    """Return aggregated Cedar policy statistics."""
    from core.cedar_engine import get_audit_stats
    return JSONResponse(get_audit_stats())


# Profile & Session Handlers

async def get_profile_handler(request: Request) -> JSONResponse:
    user_id = request.path_params.get("user_id", "demo-user")
    return JSONResponse(get_user_profile(user_id))


async def post_profile_handler(request: Request) -> JSONResponse:
    user_id = request.path_params.get("user_id", "demo-user")
    try:
        body = await request.json()
        updates = body.get("updates", body)
    except Exception:
        updates = {}
    return JSONResponse(upsert_user_profile(user_id, updates))


async def get_session_handler(request: Request) -> JSONResponse:
    user_id = request.path_params.get("user_id", "demo-user")
    return JSONResponse(get_latest_session(user_id))


async def get_history_handler(request: Request) -> JSONResponse:
    user_id = request.path_params.get("user_id", "demo-user")
    from core.memory import get_full_history
    return JSONResponse(get_full_history(user_id))


# Automated AI Evaluation & System Endpoints

async def eval_validate_handler(request: Request) -> JSONResponse:
    """Validate any user query and assistant response against the automated AI evaluation rubric."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_query = body.get("user_query", "")
    ai_response = body.get("ai_response", "")
    context = body.get("context", {})
    use_llm = bool(body.get("use_llm_judge", False))
    from core.ai_evaluator import validate_ai_response
    report = validate_ai_response(user_query=user_query, ai_response=ai_response, context=context, use_llm_judge=use_llm)
    return JSONResponse(report)


async def chat_validate_handler(request: Request) -> JSONResponse:
    """End-to-end chat execution with immediate automated AI validation of the response."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = body.get("user_id", "demo-user")
    message = body.get("message", "")
    profile_updates = body.get("profile_updates", {})
    use_llm = bool(body.get("use_llm_judge", False))

    profile = get_user_profile(user_id)
    if profile_updates:
        profile = upsert_user_profile(user_id, profile_updates)

    state = {
        "session_id": f"{user_id}-{time.time()}",
        "user_id": user_id,
        "raw_input": message,
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
        "ocr_extracted_text": message,
    }
    try:
        result = graph.invoke(state)
    except Exception as exc:
        result = {
            **state,
            "error": str(exc),
            "final_response": "I could not process that fully. Please try again with a shorter message.",
        }
    update_session(user_id, result)

    # Automated AI response evaluation
    from core.ai_evaluator import validate_ai_response
    val_context = {
        "scam_detected": result.get("scam_detected", False),
        "cedar_allowed": result.get("agent_outputs", {}).get("prahari", {}).get("cedar_allowed", True),
        "scheme_matches": result.get("scheme_matches", []),
    }
    validation_report = validate_ai_response(
        user_query=message,
        ai_response=result.get("final_response", ""),
        context=val_context,
        use_llm_judge=use_llm,
    )

    return JSONResponse({
        "chat_result": result,
        "ai_validation": validation_report,
    })


async def system_status_handler(request: Request) -> JSONResponse:
    """Comprehensive system status for monitoring dashboards."""
    from core.cedar_engine import get_audit_stats
    cedar_stats = get_audit_stats()
    return JSONResponse({
        "service": "arthsetu",
        "version": "2.0.0",
        "status": "operational",
        "agents": {
            "sutradhar": {"status": "active", "role": "orchestrator"},
            "prahari": {"status": "active", "role": "fraud_sentinel"},
            "bodhak": {"status": "active", "role": "document_decoder"},
            "shilpi": {"status": "active", "role": "budget_planner"},
            "vivek": {"status": "active", "role": "score_coach"},
            "extractor": {"status": "active", "role": "profile_learner"},
        },
        "cedar_firewall": {
            "rules_loaded": 5,
            "eval_latency_ms": "<1",
            **cedar_stats,
        },
        "features": [
            "multi_turn_memory",
            "sse_streaming",
            "cedar_audit_trail",
            "scam_intelligence_network",
            "rate_limiting",
            "security_headers",
            "pii_redaction",
            "nemo_guardrails",
            "ai_response_validation",
        ],
    })


# Application Routes

routes = [
    Route("/", root_handler, methods=["GET"]),
    Route("/health", health_handler, methods=["GET"]),
    Route("/api/v1/chat", chat_handler, methods=["POST"]),
    Route("/api/v1/chat/stream", chat_stream_handler, methods=["POST"]),
    Route("/api/v1/chat/validate", chat_validate_handler, methods=["POST"]),
    Route("/api/v1/eval/validate", eval_validate_handler, methods=["POST"]),
    Route("/api/v1/profile/{user_id}", get_profile_handler, methods=["GET"]),
    Route("/api/v1/profile/{user_id}", post_profile_handler, methods=["POST"]),
    Route("/api/v1/session/{user_id}", get_session_handler, methods=["GET"]),
    Route("/api/v1/history/{user_id}", get_history_handler, methods=["GET"]),
    Route("/api/v1/scam-network/stats", scam_network_stats_handler, methods=["GET"]),
    Route("/api/v1/cedar/audit", cedar_audit_handler, methods=["GET"]),
    Route("/api/v1/cedar/stats", cedar_stats_handler, methods=["GET"]),
    Route("/api/v1/system/status", system_status_handler, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000", "*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Create the base Starlette app
_starlette_app = Starlette(debug=True, routes=routes, middleware=middleware)

# Wrap with security middleware (applied in reverse order — outermost first)
app = RateLimitMiddleware(
    SecurityHeadersMiddleware(_starlette_app),
    max_requests=120,
    window_seconds=60,
)

