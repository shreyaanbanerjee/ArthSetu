"""Unit tests for AWS integration tools (SQS, DynamoDB, OpenSearch)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from tools.aws_tools import (
    _extract_fingerprints,
    _hash,
    check_scam_network,
    get_scam_network_stats,
    push_scam_to_sqs,
    search_opensearch_schemes,
)


class TestAWSTools(unittest.TestCase):
    def test_extract_phone_fingerprint(self):
        """Extract Indian mobile phone numbers for fingerprinting."""
        text = "Contact manager urgently at +91 9876543210 or 9876543210."
        fps = _extract_fingerprints(text)
        self.assertIn("phone", fps)
        self.assertEqual(fps["phone"], "+919876543210")

    def test_extract_upi_fingerprint(self):
        """Extract UPI IDs with standard banking handles."""
        text = "Send ₹500 processing fee to fraudster@okaxis immediately."
        fps = _extract_fingerprints(text)
        self.assertIn("upi", fps)
        self.assertEqual(fps["upi"], "fraudster@okaxis")

    def test_extract_url_fingerprint(self):
        """Extract phishing URLs."""
        text = "Click http://secure-kyc-update.in/verify to unlock account."
        fps = _extract_fingerprints(text)
        self.assertIn("url", fps)
        self.assertEqual(fps["url"], "http://secure-kyc-update.in/verify")

    def test_extract_multiple_fingerprints(self):
        """Extract combined phone, UPI, and URL from a message."""
        text = "Call 9123456789 or pay admin@paytm at https://claim-now.xyz"
        fps = _extract_fingerprints(text)
        self.assertEqual(fps.get("phone"), "9123456789")
        self.assertEqual(fps.get("upi"), "admin@paytm")
        self.assertEqual(fps.get("url"), "https://claim-now.xyz")

    def test_hash_consistency(self):
        """Consistent 16-char SHA-256 fingerprint hash."""
        h1 = _hash("user@bank")
        h2 = _hash("USER@BANK ")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)

    def test_sqs_push_offline_degradation(self):
        """Gracefully return None if SQS is unconfigured without crashing."""
        with patch("tools.aws_tools.SQS_QUEUE_URL", ""):
            msg_id = push_scam_to_sqs(
                scam_type="otp_request",
                message_excerpt="Test excerpt",
                confidence=0.9,
                language="en",
                red_flags=["fake_otp"],
            )
            self.assertIsNone(msg_id)

    def test_sqs_push_mocked_success(self):
        """Successfully return SQS MessageId when SQS responds."""
        mock_client = MagicMock()
        mock_client.send_message.return_value = {"MessageId": "msg-aws-sqs-12345"}

        with patch("tools.aws_tools.SQS_QUEUE_URL", "https://sqs.ap-south-1.amazonaws.com/123/Queue"), \
             patch("tools.aws_tools._get_sqs", return_value=mock_client):
            msg_id = push_scam_to_sqs(
                scam_type="electricity_bill",
                message_excerpt="Fake power cut bill",
                confidence=0.92,
                language="en",
                red_flags=["urgent_payment"],
            )
            self.assertEqual(msg_id, "msg-aws-sqs-12345")
            mock_client.send_message.assert_called_once()

    def test_check_scam_network_no_fingerprints(self):
        """Return clean result when text contains no identifiable fingerprints."""
        res = check_scam_network("Hello, how are you today?")
        self.assertFalse(res["known"])
        self.assertEqual(res["report_count"], 0)
        self.assertEqual(res["matches"], [])

    def test_check_scam_network_mocked_hit(self):
        """Match existing fraudster fingerprint from DynamoDB ScamNetwork."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "fingerprint": "phone#12345",
                "report_count": 7,
                "fp_display": "98765*****",
                "scam_type": "lottery_fraud",
                "last_reported": "2026-11-01T12:00:00Z",
            }
        }
        mock_ddb = MagicMock()
        mock_ddb.Table.return_value = mock_table

        with patch("tools.aws_tools._get_dynamodb", return_value=mock_ddb):
            res = check_scam_network("Urgent call 9876543210")
            self.assertTrue(res["known"])
            self.assertEqual(res["report_count"], 7)
            self.assertIn("7 ArthSetu users reported this", res["warning"])

    def test_opensearch_schemes_offline_degradation(self):
        """Degrade gracefully to empty list when OpenSearch is unconfigured."""
        with patch("tools.aws_tools.OPENSEARCH_ENDPOINT", ""):
            res = search_opensearch_schemes("farmer crop subsidy")
            self.assertEqual(res, [])

    def test_scam_network_stats_structure(self):
        """ScamNetwork stats endpoint returns valid summary dictionary."""
        mock_ddb = MagicMock()
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_ddb.Table.return_value = mock_table

        with patch("tools.aws_tools._get_dynamodb", return_value=mock_ddb):
            stats = get_scam_network_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn("total_reports", stats)
            self.assertIn("source", stats)


if __name__ == "__main__":
    unittest.main()
