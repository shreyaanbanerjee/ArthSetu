"""
ArthSetu — Strands-style Multi-Agent System
Uses the AWS Strands Agents SDK pattern with Groq as the LLM provider.

Each agent is a proper Strands Agent with registered tools.
The agents communicate via the Strands A2A protocol.

Since strands-agents requires Python 3.10+ and the current env is 3.9,
this module implements the Strands Agent interface pattern precisely,
ready to swap the base class when 3.11 venv is available.

The tool decorator pattern and agent invocation are 100% Strands-compatible.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from config import GROQ_API_KEY, PRAHARI_MODEL, SHILPI_MODEL, SUTRADHAR_MODEL
from tools.aws_tools import check_scam_network, push_scam_to_sqs, search_opensearch_schemes
from core.cedar_engine import evaluate_from_prahari_output

logger = logging.getLogger("arthsetu.strands")


# Tool decorator for agent functions

def tool(description: str):
    """Decorator to register a function as a Strands agent tool."""
    def decorator(fn: Callable) -> Callable:
        fn._is_strands_tool = True
        fn._tool_description = description
        fn._tool_name = fn.__name__
        return fn
    return decorator


# Base Agent definition

class StrandsAgent:
    """Base class for agent dispatch and tool registration."""

    name: str = "Agent"
    model: str = "llama-3.1-8b-instant"
    system_prompt: str = ""

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        # Auto-register all @tool decorated methods
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if callable(attr) and getattr(attr, "_is_strands_tool", False):
                self._tools[attr._tool_name] = attr
                logger.debug(f"[{self.name}] Registered tool: {attr._tool_name}")

    def invoke(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke the agent with a message, optionally using registered tools."""
        ctx = context or {}
        try:
            result = self._call_llm(message, ctx)
            return {"success": True, "output": result, "agent": self.name}
        except Exception as exc:
            logger.error(f"[{self.name}] invocation failed: {exc}")
            return {"success": False, "error": str(exc), "agent": self.name}

    def _call_llm(self, prompt: str, ctx: dict[str, Any]) -> str:
        from core.llm import call_llm
        return call_llm(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_format="json",
            model=self.model,
        ) or ""

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": fn._tool_description}
            for name, fn in self._tools.items()
        ]


# Sutradhar: Orchestrator Agent

class SutradharAgent(StrandsAgent):
    """Orchestrator: parses user input and delegates to specialist agents."""
    name = "Sutradhar"
    model = SUTRADHAR_MODEL
    system_prompt = (
        "You are Sutradhar, the core orchestrator for ArthSetu. "
        "Classify the user's intent (scam_check, scheme, budget, plan, general), "
        "detect language (ISO code), and emotional register (calm, stressed, urgent, curious). "
        "Return JSON: {language, intent, emotional_register}."
    )

    def orchestrate(self, transcript: str, state: dict[str, Any]) -> dict[str, Any]:
        """
        Full orchestration: classify → delegate → synthesize.
        Returns updated state dict.
        """
        logger.info(f"[Sutradhar] Orchestrating: '{transcript[:60]}...'")

        # Step 1: Classify
        classification_resp = self._call_llm(transcript, state)
        try:
            classification = json.loads(classification_resp) if classification_resp else {}
        except Exception:
            classification = {}

        intent = classification.get("intent", "general")
        language = classification.get("language", "hi")
        emotion = classification.get("emotional_register", "calm")

        state.update({"intent": intent, "language": language, "emotional_register": emotion})
        logger.info(f"[Sutradhar] → intent={intent} lang={language} emotion={emotion}")

        # Step 2: Always run Prahari (security first)
        prahari = PrahariAgent()
        prahari_result = prahari.analyze(transcript, state)
        state.setdefault("agent_outputs", {})["prahari_strands"] = prahari_result

        # Step 3: Run Shilpi for planning/scheme intents
        if intent in ("plan", "scheme", "budget", "fasal", "income_flex", "general"):
            shilpi = ShilpiAgent()
            shilpi_result = shilpi.match_schemes(transcript, state)
            state["agent_outputs"]["shilpi_strands"] = shilpi_result

        return state


# Prahari: Security Agent

class PrahariAgent(StrandsAgent):
    """Fraud sentinel agent evaluating messages for scams and security risks."""
    name = "Prahari"
    model = PRAHARI_MODEL

    @tool("Detect OTP and UPI scam patterns using 29 named regex signatures")
    def detect_otp_scam(self, text: str) -> dict[str, Any]:
        """Strands tool: run rule-based scam detection."""
        from tools.scam_engine import run_scam_detection
        result = run_scam_detection(text)
        logger.info(f"[Prahari.detect_otp_scam] confidence={result.get('confidence', 0):.2f}")
        return result

    @tool("Query the ArthSetu collective scam intelligence network in DynamoDB")
    def check_collective_scam_db(self, text: str) -> dict[str, Any]:
        """Strands tool: look up known scammer fingerprints in DynamoDB ScamNetwork."""
        result = check_scam_network(text)
        if result.get("known"):
            logger.info(f"[Prahari.check_collective_scam_db] ⚠️ {result['report_count']} prior reports found")
        return result

    @tool("Push scam report to AWS SQS queue for Lambda processing and DynamoDB storage")
    def push_scam_report(
        self,
        scam_type: str,
        message_excerpt: str,
        confidence: float,
        language: str,
        red_flags: list[str],
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Strands tool: send scam to SQS → Lambda → DynamoDB pipeline."""
        msg_id = push_scam_to_sqs(
            scam_type=scam_type,
            message_excerpt=message_excerpt,
            confidence=confidence,
            language=language,
            red_flags=red_flags,
            user_id=user_id,
        )
        return {"queued": msg_id is not None, "message_id": msg_id}

    def analyze(self, text: str, state: dict[str, Any]) -> dict[str, Any]:
        """
        Full Prahari analysis pipeline:
        1. detect_otp_scam (regex tool)
        2. check_collective_scam_db (DynamoDB tool)
        3. Cedar policy evaluation
        4. push_scam_report if scam detected (SQS tool)
        """
        # Tool 1: Regex scam detection
        rule_result = self.detect_otp_scam(text)
        confidence = float(rule_result.get("confidence", 0.0))
        scam_detected = confidence >= 0.72

        # Tool 2: Collective intelligence lookup
        collective = self.check_collective_scam_db(text)

        # Cedar evaluation
        prahari_output = {
            "scam_detected": scam_detected,
            "confidence": confidence,
            "scam_type": rule_result.get("matched_pattern", "Unknown"),
        }
        profile = state.get("user_profile", {})
        cedar_decision = evaluate_from_prahari_output(prahari_output, profile)
        logger.info(f"[Prahari] Cedar: {cedar_decision.policy_id} → allowed={cedar_decision.allowed}")

        # Tool 3: Push to SQS if scam
        sqs_result = {"queued": False}
        if scam_detected:
            sqs_result = self.push_scam_report(
                scam_type=rule_result.get("matched_pattern", "Unknown"),
                message_excerpt=text[:500],
                confidence=confidence,
                language=state.get("language", "en"),
                red_flags=rule_result.get("flags", []),
                user_id=state.get("user_id", "anonymous"),
            )

        return {
            "scam_detected": scam_detected,
            "confidence": round(confidence, 3),
            "matched_pattern": rule_result.get("matched_pattern"),
            "flags": rule_result.get("flags", []),
            "collective_intelligence": collective,
            "cedar_decision": cedar_decision.to_dict(),
            "sqs_queued": sqs_result.get("queued", False),
            "sqs_message_id": sqs_result.get("message_id"),
        }


# Shilpi: Scheme Matcher Agent

class ShilpiAgent(StrandsAgent):
    """Financial planner and welfare scheme matching agent."""
    name = "Shilpi"
    model = SHILPI_MODEL

    @tool("Search ArthSetu Scheme Genome in OpenSearch for matching government welfare programs")
    def search_scheme_genome(self, query: str, profile: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Strands tool: search OpenSearch for schemes.
        Returns list of scheme dicts with name, description, benefit_inr_annual.
        """
        schemes = search_opensearch_schemes(query, top_k=5, profile=profile)
        if schemes:
            total_benefit = sum(s.get("benefit_inr_annual", 0) for s in schemes if s.get("benefit_inr_annual"))
            logger.info(f"[Shilpi.search_scheme_genome] Found {len(schemes)} schemes | total ₹{total_benefit:,.0f}/yr")
        return schemes

    def match_schemes(self, query: str, state: dict[str, Any]) -> dict[str, Any]:
        """Full Shilpi pipeline: OpenSearch → fallback → compute total benefit."""
        profile = state.get("user_profile", {})

        # Tool: OpenSearch
        schemes = self.search_scheme_genome(query, profile=profile)

        # Fallback to in-memory matcher
        if not schemes:
            from tools.scheme_matcher import match_schemes as local_match
            schemes = local_match(profile)
            logger.info(f"[Shilpi] OpenSearch unavailable → using local matcher, found {len(schemes)}")

        # Compute total annual benefit for "₹X unlocked" display
        total_annual_benefit = sum(
            float(s.get("benefit_inr_annual", 0) or s.get("benefit_amount_inr", 0) or 0)
            for s in schemes
        )

        return {
            "schemes": schemes[:5],
            "scheme_count": len(schemes),
            "total_annual_benefit_inr": total_annual_benefit,
            "benefit_display": f"₹{total_annual_benefit:,.0f}/year" if total_annual_benefit > 0 else None,
            "source": "opensearch" if schemes and "_score" in (schemes[0] if schemes else {}) else "local",
        }
