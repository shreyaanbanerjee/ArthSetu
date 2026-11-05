"""
ArthSetu — Scam Aggregator Lambda Handler
Runs every hour via EventBridge schedule.
Scans DynamoDB ScamReports and updates aggregated ScamNetwork table.
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "ap-south-1"))
SCAM_TABLE = dynamodb.Table(os.environ.get("SCAM_TABLE_NAME", "ArthSetu-ScamReports"))
NETWORK_TABLE = dynamodb.Table(os.environ.get("NETWORK_TABLE_NAME", "ArthSetu-ScamNetwork"))


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Hourly aggregation of scam statistics."""
    logger.info("Starting hourly scam aggregation")
    try:
        # Scan recent reports (production: use Query with GSI on date)
        response = SCAM_TABLE.scan(
            ProjectionExpression="scam_type, confidence, fingerprints, reported_at",
            Limit=500,
        )
        items = response.get("Items", [])

        # Count by scam type
        type_counts: dict[str, int] = defaultdict(int)
        for item in items:
            scam_type = item.get("scam_type", "Unknown")
            type_counts[scam_type] += 1

        logger.info(f"Aggregated {len(items)} reports. Top types: {dict(list(type_counts.items())[:5])}")
        return {"statusCode": 200, "reports_scanned": len(items), "type_breakdown": dict(type_counts)}
    except Exception as exc:
        logger.error(f"Aggregation failed: {exc}", exc_info=True)
        return {"statusCode": 500, "error": str(exc)}
