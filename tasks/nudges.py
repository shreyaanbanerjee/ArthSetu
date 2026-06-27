"""Celery background nudge tasks."""

from __future__ import annotations

from typing import Any

from celery import Celery

from config import RABBITMQ_URL, REDIS_URL
from core.memory import get_latest_session, get_user_profile
from tools.arth_score import calculate_arth_score


celery_app = Celery("arthsetu", broker=RABBITMQ_URL, backend=REDIS_URL)
celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.beat_schedule = {
    "seasonal-pmfby-reminder": {"task": "tasks.nudges.seasonal_scheme_scan", "schedule": 60 * 60 * 24},
}


@celery_app.task(name="tasks.nudges.income_received_nudge")
def income_received_nudge(user_id: str, amount_inr: float) -> dict[str, Any]:
    """Create a savings nudge after an income event."""
    profile = get_user_profile(user_id)
    suggested = max(50, min(float(amount_inr) * 0.05, float(amount_inr) - float(profile.get("monthly_expenses_inr", 0)) / 4))
    return {
        "user_id": user_id,
        "message": f"Income received: consider moving Rs {suggested:.0f} to emergency savings before spending.",
        "suggested_savings_inr": round(suggested, 2),
    }


@celery_app.task(name="tasks.nudges.seasonal_scheme_scan")
def seasonal_scheme_scan() -> dict[str, Any]:
    """Return seasonal reminder metadata for workers or admin UI."""
    return {
        "pmfby": "Check crop insurance enrolment windows before the season deadline.",
        "tax_march": "March is a good month to collect Form 16, insurance, and savings proofs.",
    }


@celery_app.task(name="tasks.nudges.arth_score_milestone")
def arth_score_milestone(user_id: str) -> dict[str, Any]:
    """Detect the current Arth Score for milestone nudges."""
    profile = get_user_profile(user_id)
    latest = get_latest_session(user_id)
    score = calculate_arth_score(profile, latest)
    return {"user_id": user_id, "score": score}
