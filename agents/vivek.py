"""Vivek behavioural mirror and Arth Score agent."""

from __future__ import annotations

import json
from typing import Any

from config import VIVEK_MODEL
from core.llm import call_llm, format_user_persona
from tools.arth_score import calculate_arth_score

def vivek_node(state: dict[str, Any]) -> dict[str, Any]:
    """Calculate Arth Score and behavioural nudges."""
    profile = state.get("user_profile", {})
    language = state.get("language", "hi")
    score = calculate_arth_score(profile, state)
    
    if state.get("profile_updated_dynamically"):
        score["next_best_action"] = f"Your profile was automatically updated based on what you said! Your new Arth Score is {score.get('score')}/100. " + score.get("next_best_action", "")
        
    state["arth_score_update"] = score
    parsed = _nudge_with_llm(profile, score, language) or _nudge_locally(score)
    state.setdefault("agent_outputs", {})["vivek"] = parsed
    return state

def _nudge_with_llm(profile: dict[str, Any], score: dict[str, Any], language: str) -> dict[str, Any] | None:
    """Use Gemini or Groq to generate customized behavioral nudges and reflections."""
    user_persona = format_user_persona(profile)
    system_prompt = f"""You are Vivek, ArthSetu's behavioral mirror and financial wisdom agent.
Your task is to analyze the user's financial profile and their calculated Arth Score, and generate a customized behavioral nudge and reflection tailored to their job, income, and financial situation.

{user_persona}

Arth Score Details:
- Total Score: {score.get('score')}/100
- Band: {score.get('band')}
- Dimension Scores: {score.get('dimensions')}

Provide a highly targeted, realistic, actionable, and encouraging nudge and reflection in the target language ({language}). Avoid generalities.

You must output ONLY a valid JSON object matching this structure:
{{
    "arth_score": {{
        "score": {score.get('score')},
        "dimensions": {json.dumps(score.get('dimensions'))},
        "band": "{score.get('band')}",
        "next_best_action": "{score.get('next_best_action')}"
    }},
    "nudge": "A simple, practical nudge (1-2 sentences) tailored to their situation and current score.",
    "reflection": "An encouraging reflection or observation about their situation (1-2 sentences) to build their financial confidence."
}}
Do not add any markdown formatting outside the JSON. Return only valid JSON."""

    try:
        response_text = call_llm(
            prompt="Analyze the profile and score to generate the nudge and reflection.",
            system_prompt=system_prompt,
            response_format="json",
            model=VIVEK_MODEL
        )
        if not response_text:
            return None

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        return json.loads(cleaned_text)
    except Exception:
        return None

def _nudge_locally(score: dict[str, Any]) -> dict[str, Any]:
    """Fallback local nudge generator."""
    return {
        "arth_score": score,
        "nudge": _nudge_for_score(score),
        "reflection": "Small repeatable actions matter more than one perfect month.",
    }

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

