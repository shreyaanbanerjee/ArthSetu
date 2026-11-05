"""
ArthSetu — Fraud Parser Lambda Handler
SQS → Lambda → DynamoDB (ScamReports + ScamNetwork)

Deployed via SAM CLI on AWS ap-south-1.
Triggered by ScamReportQueue SQS messages from Prahari agent.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "ap-south-1"))
SCAM_TABLE = dynamodb.Table(os.environ.get("SCAM_TABLE_NAME", "ArthSetu-ScamReports"))
NETWORK_TABLE = dynamodb.Table(os.environ.get("NETWORK_TABLE_NAME", "ArthSetu-ScamNetwork"))


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process a batch of scam reports from SQS."""
    batch_item_failures: list[dict[str, str]] = []
    records_processed = 0

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
            _process_scam_report(body)
            records_processed += 1
            logger.info(f"Processed scam report: {body.get('scam_type', 'unknown')} | msgId={message_id}")
        except Exception as exc:
            logger.error(f"Failed to process messageId={message_id}: {exc}", exc_info=True)
            batch_item_failures.append({"itemIdentifier": message_id})

    logger.info(f"Batch complete: {records_processed} processed, {len(batch_item_failures)} failed")
    return {"batchItemFailures": batch_item_failures}


def _process_scam_report(payload: dict[str, Any]) -> None:
    """Write scam report to DynamoDB and update the collective ScamNetwork table."""
    now_iso = datetime.now(timezone.utc).isoformat()
    scam_id = payload.get("scam_id") or str(uuid.uuid4())
    ttl = int(time.time()) + (90 * 24 * 3600)  # 90-day TTL

    # 1. Write individual report
    item = {
        "scam_id": scam_id,
        "reported_at": now_iso,
        "scam_type": payload.get("scam_type", "Unknown"),
        "confidence": str(payload.get("confidence", 0.0)),
        "message_excerpt": payload.get("message_excerpt", "")[:500],
        "language": payload.get("language", "en"),
        "red_flags": payload.get("red_flags", []),
        "fingerprints": payload.get("fingerprints", {}),
        "user_id_hash": _hash(payload.get("user_id", "")),
        "ttl": ttl,
    }
    SCAM_TABLE.put_item(Item=item)

    # 2. Update ScamNetwork table for each fingerprint (phone, UPI, URL)
    fingerprints: dict[str, str] = payload.get("fingerprints", {})
    for fp_type, fp_value in fingerprints.items():
        if not fp_value:
            continue
        fingerprint_key = f"{fp_type}#{_hash(fp_value)}"
        try:
            NETWORK_TABLE.update_item(
                Key={"fingerprint": fingerprint_key},
                UpdateExpression=(
                    "SET fp_type = :fpt, fp_display = :fpd, scam_type = :st, "
                    "last_reported = :lr, #cnt = if_not_exists(#cnt, :zero) + :inc, "
                    "first_reported = if_not_exists(first_reported, :lr)"
                ),
                ExpressionAttributeNames={"#cnt": "report_count"},
                ExpressionAttributeValues={
                    ":fpt": fp_type,
                    ":fpd": _mask(fp_value),   # masked for privacy (e.g. "+91-98****3210")
                    ":st": payload.get("scam_type", "Unknown"),
                    ":lr": now_iso,
                    ":zero": 0,
                    ":inc": 1,
                },
            )
        except ClientError as exc:
            logger.warning(f"Failed to update ScamNetwork for {fingerprint_key}: {exc}")


def _hash(value: str) -> str:
    """SHA-256 hash of value for privacy-preserving lookup."""
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:16]


def _mask(value: str) -> str:
    """Mask middle digits of phone/UPI for display (privacy)."""
    if not value:
        return ""
    if len(value) <= 6:
        return value[:2] + "****"
    return value[:4] + "****" + value[-4:]
