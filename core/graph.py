"""ArthSetu graph orchestration."""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class GraphState(TypedDict, total=False):
    """State passed through the ArthSetu graph."""

    session_id: str
    user_id: str
    raw_input: str
    language: str
    intent: str
    emotional_register: str
    agent_outputs: dict[str, Any]
    final_response: str
    tts_audio_b64: Optional[str]
    upi_action: Optional[dict[str, Any]]
    scam_detected: bool
    scheme_matches: list[dict[str, Any]]
    arth_score_update: Optional[dict[str, Any]]
    error: Optional[str]
    user_profile: dict[str, Any]
    ocr_extracted_text: Optional[str]


class ArthSetuGraph:
    """Small invoke-compatible graph runner for deterministic local execution."""

    def invoke(self, state: GraphState) -> GraphState:
        """Run Sutradhar, selected agents, synthesis, and guardrails."""
        from agents.bodhak import bodhak_node
        from agents.prahari import prahari_node
        from agents.shilpi import shilpi_node
        from agents.sutradhar import sutradhar_node
        from agents.vivek import vivek_node
        from core.guardrails import guardrail_node

        state.setdefault("agent_outputs", {})
        state.setdefault("scheme_matches", [])
        state = sutradhar_node(state)
        for agent_name in route_after_sutradhar(state):
            if agent_name == "prahari":
                state = prahari_node(state)
            elif agent_name == "bodhak":
                state = bodhak_node(state)
            elif agent_name == "shilpi":
                state = shilpi_node(state)
            elif agent_name == "vivek":
                state = vivek_node(state)
        state = sutradhar_node(state)
        state = guardrail_node(state)
        return state


def build_graph() -> ArthSetuGraph:
    """Build the ArthSetu graph runner."""
    return ArthSetuGraph()


def route_after_sutradhar(state: GraphState) -> list[str]:
    """Return selected agent nodes based on detected intent; Prahari always fires."""
    intent = state.get("intent", "general")
    agents = ["prahari"]
    if intent in ("document", "decode", "explain", "saaf_bolna"):
        agents.append("bodhak")
    if intent in ("plan", "scheme", "budget", "fasal", "income_flex"):
        agents.append("shilpi")
    if intent in ("score", "habit", "nudge", "paisa_padhai", "myth"):
        agents.append("vivek")
    if intent == "scam_check":
        pass
    if intent == "general":
        agents.extend(["bodhak", "shilpi", "vivek"])
    return agents
