"""Session and profile memory using Redis/PostgreSQL with local fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import DATABASE_URL, DEFAULT_LANGUAGE, REDIS_URL, SESSION_TTL_SECONDS


DATA_DIR = Path(".arthsetu_data")
PROFILE_FILE = DATA_DIR / "profiles.json"
SESSION_FILE = DATA_DIR / "sessions.json"

DEFAULT_PROFILE: dict[str, Any] = {
    "language": DEFAULT_LANGUAGE,
    "occupation": "",
    "monthly_income_inr": 0,
    "monthly_expenses_inr": 0,
    "emergency_fund_inr": 0,
    "has_bank_account": True,
    "has_disability": False,
    "land_ownership": False,
    "age": 30,
    "voice_first": False,
    "has_daughter_below_10": False,
    "has_child": False,
    "not_epf_member": True,
    "monthly_debt_emi_inr": 0,
    "has_informal_debt": False,
    "savings_rate_pct": 0,
}


def get_user_profile(user_id: str) -> dict[str, Any]:
    """Load a persistent user profile."""
    profile = _get_profile_from_postgres(user_id) or _get_profile_from_file(user_id)
    merged = {**DEFAULT_PROFILE, **profile, "user_id": user_id}
    return merged


def upsert_user_profile(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update a user profile in available storage."""
    profile = {**get_user_profile(user_id), **updates, "user_id": user_id}
    _save_profile_to_file(user_id, profile)
    _save_profile_to_postgres(profile)
    return profile


def update_session(user_id: str, state: dict[str, Any]) -> None:
    """Store latest session in Redis with local fallback."""
    saved = _save_session_to_redis(user_id, state)
    if not saved:
        _save_session_to_file(user_id, state)


def get_latest_session(user_id: str) -> dict[str, Any]:
    """Load latest session for a user."""
    redis_session = _get_session_from_redis(user_id)
    if redis_session:
        return redis_session
    data = _read_json(SESSION_FILE)
    return data.get(user_id, {})


def _get_profile_from_postgres(user_id: str) -> dict[str, Any] | None:
    """Read profile from PostgreSQL when configured."""
    if not DATABASE_URL:
        return None
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("select profile from user_profiles where user_id = %s", (user_id,))
                row = cur.fetchone()
                return row[0] if row else None
    except Exception:
        return None


def _save_profile_to_postgres(profile: dict[str, Any]) -> None:
    """Persist profile to PostgreSQL when configured."""
    if not DATABASE_URL:
        return
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    create table if not exists user_profiles (
                        user_id text primary key,
                        profile jsonb not null,
                        updated_at timestamptz default now()
                    )
                    """
                )
                cur.execute(
                    """
                    insert into user_profiles (user_id, profile, updated_at)
                    values (%s, %s, now())
                    on conflict (user_id) do update set profile = excluded.profile, updated_at = now()
                    """,
                    (profile["user_id"], json.dumps(profile)),
                )
                conn.commit()
    except Exception:
        return


def _save_session_to_redis(user_id: str, state: dict[str, Any]) -> bool:
    """Save session to Redis."""
    try:
        import redis

        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.setex(f"session:{user_id}", SESSION_TTL_SECONDS, json.dumps(_json_safe(state), ensure_ascii=False))
        return True
    except Exception:
        return False


def _get_session_from_redis(user_id: str) -> dict[str, Any] | None:
    """Read session from Redis."""
    try:
        import redis

        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        raw = client.get(f"session:{user_id}")
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _get_profile_from_file(user_id: str) -> dict[str, Any]:
    """Read profile from local JSON fallback."""
    return _read_json(PROFILE_FILE).get(user_id, {})


def _save_profile_to_file(user_id: str, profile: dict[str, Any]) -> None:
    """Write profile to local JSON fallback."""
    data = _read_json(PROFILE_FILE)
    data[user_id] = _json_safe(profile)
    _write_json(PROFILE_FILE, data)


def _save_session_to_file(user_id: str, state: dict[str, Any]) -> None:
    """Write session to local JSON fallback."""
    data = _read_json(SESSION_FILE)
    data[user_id] = _json_safe(state)
    _write_json(SESSION_FILE, data)


def _read_json(path: Path) -> dict[str, Any]:
    """Read JSON object from disk."""
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON object to disk."""
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _json_safe(value: Any) -> Any:
    """Convert values into JSON-safe structures."""
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        return str(value)
