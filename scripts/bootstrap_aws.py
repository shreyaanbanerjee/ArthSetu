#!/usr/bin/env python3
"""
ArthSetu — AWS Infrastructure Bootstrap
Creates SQS queue, DynamoDB tables, and verifies connectivity.
Run this before deploying via SAM CLI.

Usage:
    python scripts/bootstrap_aws.py
"""

from __future__ import annotations
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REGION = "ap-south-1"

def main():
    import boto3
    from botocore.exceptions import ClientError

    print("🚀 ArthSetu AWS Bootstrap — ap-south-1")
    print("=" * 50)

    # ── SQS ─────────────────────────────────────────────────────────────────
    print("\n1️⃣  Creating SQS queue...")
    sqs = boto3.client("sqs", region_name=REGION)
    try:
        resp = sqs.create_queue(
            QueueName="ArthSetu-ScamReportQueue",
            Attributes={
                "VisibilityTimeout": "60",
                "MessageRetentionPeriod": "86400",
            },
            tags={"Project": "ArthSetu", "Track": "ShipIt"},
        )
        queue_url = resp["QueueUrl"]
        print(f"   ✅ SQS Queue created: {queue_url}")
    except ClientError as e:
        if "QueueAlreadyExists" in str(e) or "AlreadyExists" in str(e):
            resp = sqs.get_queue_url(QueueName="ArthSetu-ScamReportQueue")
            queue_url = resp["QueueUrl"]
            print(f"   ✅ SQS Queue already exists: {queue_url}")
        else:
            print(f"   ❌ SQS error: {e}")
            queue_url = ""

    # ── DynamoDB: ScamReports ────────────────────────────────────────────────
    print("\n2️⃣  Creating DynamoDB table: ArthSetu-ScamReports...")
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    try:
        dynamodb.create_table(
            TableName="ArthSetu-ScamReports",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "scam_id", "AttributeType": "S"},
                {"AttributeName": "reported_at", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "scam_id", "KeyType": "HASH"},
                {"AttributeName": "reported_at", "KeyType": "RANGE"},
            ],
        )
        print("   ✅ ScamReports table created (waiting for ACTIVE...)")
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName="ArthSetu-ScamReports")
        print("   ✅ ScamReports table ACTIVE")
    except ClientError as e:
        if "ResourceInUseException" in str(e):
            print("   ✅ ScamReports table already exists")
        else:
            print(f"   ❌ DynamoDB error: {e}")

    # ── DynamoDB: ScamNetwork ────────────────────────────────────────────────
    print("\n3️⃣  Creating DynamoDB table: ArthSetu-ScamNetwork...")
    try:
        dynamodb.create_table(
            TableName="ArthSetu-ScamNetwork",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "fingerprint", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "fingerprint", "KeyType": "HASH"},
            ],
        )
        print("   ✅ ScamNetwork table created (waiting for ACTIVE...)")
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName="ArthSetu-ScamNetwork")
        print("   ✅ ScamNetwork table ACTIVE")
    except ClientError as e:
        if "ResourceInUseException" in str(e):
            print("   ✅ ScamNetwork table already exists")
        else:
            print(f"   ❌ DynamoDB error: {e}")

    # ── Test SQS round-trip ──────────────────────────────────────────────────
    if queue_url:
        print("\n4️⃣  Testing SQS round-trip...")
        try:
            test_payload = {
                "scam_id": "test-bootstrap",
                "scam_type": "BootstrapTest",
                "confidence": 0.99,
                "message_excerpt": "Bootstrap test message",
                "language": "en",
                "red_flags": ["test"],
                "fingerprints": {},
            }
            send_resp = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(test_payload),
            )
            print(f"   ✅ Test message sent: {send_resp['MessageId']}")

            # Receive and delete test message
            time.sleep(1)
            recv_resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=2)
            messages = recv_resp.get("Messages", [])
            if messages:
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=messages[0]["ReceiptHandle"])
                print("   ✅ Test message received and deleted")
        except Exception as e:
            print(f"   ⚠️  SQS test failed (non-critical): {e}")

    # ── Write queue URL to .env ──────────────────────────────────────────────
    if queue_url:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        try:
            with open(env_path, "r") as f:
                content = f.read()
            if "SQS_QUEUE_URL=" not in content:
                with open(env_path, "a") as f:
                    f.write(f"\n# AWS Infrastructure (bootstrapped)\n")
                    f.write(f"SQS_QUEUE_URL={queue_url}\n")
                    f.write(f"DYNAMODB_SCAM_TABLE=ArthSetu-ScamReports\n")
                    f.write(f"DYNAMODB_NETWORK_TABLE=ArthSetu-ScamNetwork\n")
                    f.write(f"AWS_DEFAULT_REGION={REGION}\n")
                print(f"   ✅ Queue URL written to .env")
            else:
                print(f"   ℹ️  SQS_QUEUE_URL already in .env")
        except Exception as e:
            print(f"   ⚠️  Could not update .env: {e}")
            print(f"   👉 Manually add to .env: SQS_QUEUE_URL={queue_url}")

    print("\n" + "=" * 50)
    print("✅ Bootstrap complete!")
    print("\nNext steps:")
    print("  1. Install SAM CLI: brew install aws-sam-cli")
    print("  2. Deploy Lambda: sam build && sam deploy")
    print("  3. Start server: uvicorn main:app --reload")

if __name__ == "__main__":
    main()
