"""
ArthSetu — AWS Tools
Shared utilities for SQS, DynamoDB, and OpenSearch interactions.
All functions degrade gracefully if AWS is unreachable (no crash).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from typing import Any

logger = logging.getLogger("arthsetu.aws_tools")

# AWS and service configuration
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-south-1"))
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
DYNAMODB_SCAM_TABLE = os.getenv("DYNAMODB_SCAM_TABLE", "ArthSetu-ScamReports")
DYNAMODB_NETWORK_TABLE = os.getenv("DYNAMODB_NETWORK_TABLE", "ArthSetu-ScamNetwork")
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "")
OPENSEARCH_INDEX = "arthsetu-schemes"

# Lazy-initialized clients
_sqs = None
_dynamodb = None
_opensearch = None


def _get_sqs():
    global _sqs
    if _sqs is None:
        import boto3
        _sqs = boto3.client("sqs", region_name=AWS_REGION)
    return _sqs


def _get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        import boto3
        _dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return _dynamodb


def _get_opensearch():
    global _opensearch
    if _opensearch is None and OPENSEARCH_ENDPOINT:
        from opensearchpy import OpenSearch
        _opensearch = OpenSearch(
            hosts=[OPENSEARCH_ENDPOINT],
            use_ssl=OPENSEARCH_ENDPOINT.startswith("https"),
            verify_certs=OPENSEARCH_ENDPOINT.startswith("https"),
            timeout=5,
        )
    return _opensearch


# SQS queue publication

def push_scam_to_sqs(
    scam_type: str,
    message_excerpt: str,
    confidence: float,
    language: str,
    red_flags: list[str],
    user_id: str = "anonymous",
    fingerprints: dict[str, str] | None = None,
) -> str | None:
    """
    Send a scam report to SQS for async processing by the Lambda fraud parser.
    Returns the SQS MessageId on success, None on failure (silent degradation).
    """
    if not SQS_QUEUE_URL:
        logger.debug("SQS_QUEUE_URL not set — scam report not queued")
        return None

    payload = {
        "scam_id": str(uuid.uuid4()),
        "scam_type": scam_type,
        "message_excerpt": message_excerpt[:500],
        "confidence": round(float(confidence), 4),
        "language": language,
        "red_flags": red_flags[:10],
        "user_id": user_id,
        "fingerprints": _extract_fingerprints(message_excerpt) if not fingerprints else fingerprints,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        sqs = _get_sqs()
        resp = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(payload, ensure_ascii=False),
            MessageAttributes={
                "scam_type": {"StringValue": scam_type, "DataType": "String"},
                "confidence": {"StringValue": str(confidence), "DataType": "String"},
            },
        )
        msg_id = resp.get("MessageId", "")
        logger.info(f"Scam report queued to SQS: {msg_id} | type={scam_type} | confidence={confidence:.2f}")
        return msg_id
    except Exception as exc:
        logger.warning(f"SQS push failed (non-critical): {exc}")
        return None


# DynamoDB scam network queries

def check_scam_network(text: str) -> dict[str, Any]:
    """
    Look up phone numbers, UPI IDs, and URLs in the ScamNetwork DynamoDB table.
    Returns a dict with report_count and display info for any known fingerprints.
    """
    fingerprints = _extract_fingerprints(text)
    if not fingerprints:
        return {"known": False, "report_count": 0, "matches": []}

    matches: list[dict[str, Any]] = []
    try:
        dynamodb = _get_dynamodb()
        table = dynamodb.Table(DYNAMODB_NETWORK_TABLE)

        for fp_type, fp_value in fingerprints.items():
            if not fp_value:
                continue
            fp_key = f"{fp_type}#{_hash(fp_value)}"
            resp = table.get_item(Key={"fingerprint": fp_key})
            item = resp.get("Item")
            if item:
                count = int(item.get("report_count", 1))
                matches.append({
                    "type": fp_type,
                    "display": item.get("fp_display", "****"),
                    "report_count": count,
                    "scam_type": item.get("scam_type", "Unknown"),
                    "last_reported": item.get("last_reported", ""),
                })
                logger.info(f"ScamNetwork hit: {fp_type}={fp_value[:6]}**** | {count} reports")

    except Exception as exc:
        logger.warning(f"ScamNetwork lookup failed (non-critical): {exc}")
        return {"known": False, "report_count": 0, "matches": []}

    if not matches:
        return {"known": False, "report_count": 0, "matches": []}

    total = sum(m["report_count"] for m in matches)
    return {
        "known": True,
        "report_count": total,
        "matches": matches,
        "warning": f"⚠️ {total} ArthSetu user{'s' if total > 1 else ''} reported this previously.",
    }


# OpenSearch scheme search

def search_opensearch_schemes(query: str, top_k: int = 5, profile: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Search OpenSearch for government schemes matching the query and user profile.
    Returns list of scheme dicts. Falls back to empty list if OpenSearch is unavailable.
    """
    client = _get_opensearch()
    if not client:
        logger.debug("OpenSearch not configured — skipping scheme search")
        return []

    try:
        # Build profile-aware filter
        filters = []
        if profile:
            income = profile.get("monthly_income_inr")
            if income:
                filters.append({"range": {"max_income_inr": {"gte": float(income)}}})

        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description^2", "keywords", "hi_description", "mr_description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filters,
                }
            },
            "size": top_k,
            "_source": ["name", "description", "benefits", "benefit_inr_annual", "eligibility", "apply_url", "tags"],
        }

        resp = client.search(index=OPENSEARCH_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        schemes = []
        for hit in hits:
            src = hit.get("_source", {})
            src["_score"] = hit.get("_score", 0)
            schemes.append(src)
        logger.info(f"OpenSearch returned {len(schemes)} schemes for query='{query[:40]}'")
        return schemes
    except Exception as exc:
        logger.warning(f"OpenSearch search failed (non-critical): {exc}")
        return []


def index_scheme(scheme: dict[str, Any]) -> bool:
    """Index a single scheme document into OpenSearch."""
    client = _get_opensearch()
    if not client:
        return False
    try:
        client.index(
            index=OPENSEARCH_INDEX,
            body=scheme,
            id=scheme.get("scheme_id", str(uuid.uuid4())),
        )
        return True
    except Exception as exc:
        logger.warning(f"OpenSearch index failed: {exc}")
        return False


def ensure_opensearch_index() -> bool:
    """Create the arthsetu-schemes index with mappings if it doesn't exist."""
    client = _get_opensearch()
    if not client:
        return False
    try:
        if client.indices.exists(index=OPENSEARCH_INDEX):
            return True
        mapping = {
            "mappings": {
                "properties": {
                    "name": {"type": "text", "analyzer": "standard"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "hi_description": {"type": "text"},
                    "mr_description": {"type": "text"},
                    "keywords": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "benefit_inr_annual": {"type": "float"},
                    "max_income_inr": {"type": "float"},
                    "min_age": {"type": "integer"},
                    "max_age": {"type": "integer"},
                    "eligibility": {"type": "text"},
                    "apply_url": {"type": "keyword"},
                    "scheme_id": {"type": "keyword"},
                }
            }
        }
        client.indices.create(index=OPENSEARCH_INDEX, body=mapping)
        logger.info(f"Created OpenSearch index: {OPENSEARCH_INDEX}")
        return True
    except Exception as exc:
        logger.warning(f"Failed to create OpenSearch index: {exc}")
        return False


# Fingerprint extraction helpers

def _extract_fingerprints(text: str) -> dict[str, str]:
    """Extract phone numbers, UPI IDs, and URLs from text for fingerprinting."""
    fp: dict[str, str] = {}

    # Indian mobile numbers
    phone_match = re.search(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    if phone_match:
        fp["phone"] = re.sub(r"[\s\-]", "", phone_match.group())

    # UPI IDs (name@bank format)
    upi_match = re.search(r"[\w.\-]+@(?:okaxis|oksbi|okicici|okhdfcbank|paytm|gpay|ybl|axl|ibl|upi)\b", text, re.I)
    if upi_match:
        fp["upi"] = upi_match.group().lower()

    # URLs
    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        fp["url"] = url_match.group()[:100]

    return fp


def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:16]


# Scam network aggregate statistics

def get_scam_network_stats() -> dict[str, Any]:
    """Aggregate Scam Intelligence Network statistics from local + DynamoDB.
    
    Returns comprehensive scam intelligence including:
    - Total reports processed
    - Top scam types and patterns
    - Recent scam alerts
    - Confidence score distribution
    - Network fingerprint count
    """
    stats: dict[str, Any] = {
        "total_reports": 0,
        "top_scam_types": [],
        "recent_alerts": [],
        "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
        "network_fingerprints": 0,
        "source": "local",
    }

    # Try local SQLite first (always available)
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), "..", ".arthsetu_data", "arthsetu.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path, timeout=2.0)
            try:
                conn.row_factory = sqlite3.Row

                # Count scam-detected conversations
                try:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM user_conversations WHERE scam_detected = 1"
                    ).fetchone()[0]
                    stats["total_reports"] = total
                except Exception:
                    pass

                # Recent scam alerts
                try:
                    rows = conn.execute(
                        "SELECT query, response, intent, timestamp FROM user_conversations "
                        "WHERE scam_detected = 1 ORDER BY timestamp DESC LIMIT 10"
                    ).fetchall()
                    stats["recent_alerts"] = [
                        {
                            "query_excerpt": (row["query"] or "")[:100],
                            "intent": row["intent"],
                            "timestamp": row["timestamp"],
                        }
                        for row in rows
                    ]
                except Exception:
                    pass

                # Intent distribution for scam queries
                try:
                    intent_rows = conn.execute(
                        "SELECT intent, COUNT(*) as cnt FROM user_conversations "
                        "WHERE scam_detected = 1 GROUP BY intent ORDER BY cnt DESC LIMIT 5"
                    ).fetchall()
                    stats["top_scam_types"] = [
                        {"type": row["intent"], "count": row["cnt"]}
                        for row in intent_rows
                    ]
                except Exception:
                    pass
            finally:
                conn.close()
    except Exception as exc:
        logger.debug(f"Local scam stats query failed: {exc}")

    # Try DynamoDB ScamNetwork table (if available)
    try:
        dynamodb = _get_dynamodb()
        if dynamodb:
            table = dynamodb.Table(DYNAMODB_NETWORK_TABLE)
            scan_result = table.scan(Limit=100)
            items = scan_result.get("Items", [])
            stats["network_fingerprints"] = len(items)
            stats["source"] = "dynamodb+local"

            # Count by scam type
            type_counts: dict[str, int] = {}
            for item in items:
                stype = item.get("scam_type", "unknown")
                type_counts[stype] = type_counts.get(stype, 0) + int(item.get("report_count", 1))
            if type_counts:
                stats["top_scam_types"] = [
                    {"type": k, "count": v}
                    for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
    except Exception as exc:
        logger.debug(f"DynamoDB scam network stats failed (non-critical): {exc}")

    return stats

