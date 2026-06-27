"""Vivek behavioural mirror and Arth Score agent."""

from __future__ import annotations

from typing import Any

from tools.arth_score import calculate_arth_score


def vivek_node(state: dict[str, Any]) -> dict[str, Any]:
    """Calculate Arth Score and behavioural nudges."""
    profile = state.get("user_profile", {})
    score = calculate_arth_score(profile, state)
    state["arth_score_update"] = score
    state.setdefault("agent_outputs", {})["vivek"] = {
        "arth_score": score,
        "nudge": _nudge_for_score(score),
        "reflection": "Small repeatable actions matter more than one perfect month.",
    }
    return state


def _nudge_for_score(score: dict[str, Any]) -> str:
    """Choose a practical behavioural nudge."""
    band = score.get("band")
    if band == "urgent_support":
        return "Today, avoid new borrowing and write down the most urgent payment only."
    if band == "fragile":
        return "Set aside a tiny emergency amount as soon as income arrives."
    if band == "improving":
        return "Increase savings by 1 percent this month if essentials are covered."
    return "Protect the habit: review your plan once a week."
