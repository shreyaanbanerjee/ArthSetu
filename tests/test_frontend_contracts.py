"""Frontend API contract validation tests.

Verifies that Starlette backend responses match the exact schema and types
consumed by the Next.js frontend application.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient

from main import app


class TestFrontendContracts(unittest.TestCase):
    """Test API response contracts against frontend requirements."""

    def setUp(self):
        self.client = TestClient(app)

    def test_chat_response_contract(self):
        """Verify POST /api/v1/chat returns all fields required by page.tsx."""
        mock_graph_output = {
            "user_id": "test_contract_user",
            "final_response": "पीएम स्वनिधि योजना के अंतर्गत रेहड़ी-पटरी वालों को ₹10,000 का ऋण मिलता है।",
            "intent": "scheme",
            "scam_detected": False,
            "scheme_matches": [
                {
                    "name": "PM SVANidhi",
                    "benefit": "₹10,000 working capital loan",
                    "description": "Collateral-free working capital loan for street vendors.",
                    "apply_url": "https://pmsvanidhi.mohua.gov.in/",
                }
            ],
            "arth_score_update": {
                "score": 65,
                "band": "improving",
                "next_best_action": "Apply for PMSBY for accident protection",
            },
            "agent_outputs": {
                "prahari": {
                    "scam_detected": False,
                    "confidence": 0.05,
                    "verdict": "CLEAR",
                    "cedar_allowed": True,
                },
                "shilpi": {
                    "schemes_to_apply": [{"name": "PM SVANidhi"}],
                },
                "vivek": {
                    "arth_score": {"score": 65, "band": "improving"},
                },
            },
        }

        with patch("main.graph.invoke", return_value=mock_graph_output):
            payload = {
                "user_id": "test_contract_user",
                "message": "मुझे पीएम स्वनिधि योजना की जानकारी चाहिए",
                "language": "hi",
                "profile_updates": {
                    "name": "रमेश",
                    "occupation": "street_vendor",
                    "monthly_income_inr": 15000,
                },
            }
            resp = self.client.post("/api/v1/chat", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            # Fields expected by frontend
            self.assertIn("final_response", data)
            self.assertIsInstance(data["final_response"], str)
            self.assertTrue(len(data["final_response"]) > 0)

            self.assertIn("scam_detected", data)
            self.assertIsInstance(data["scam_detected"], bool)

            self.assertIn("intent", data)
            self.assertIsInstance(data["intent"], str)

            self.assertIn("agent_outputs", data)
            self.assertIsInstance(data["agent_outputs"], dict)

            self.assertIn("scheme_matches", data)
            self.assertIsInstance(data["scheme_matches"], list)
            self.assertEqual(len(data["scheme_matches"]), 1)
            self.assertEqual(data["scheme_matches"][0]["name"], "PM SVANidhi")

            self.assertIn("arth_score_update", data)
            self.assertEqual(data["arth_score_update"]["score"], 65)

    def test_scam_detection_response_contract(self):
        """Verify chat response when a scam is detected."""
        mock_graph_output = {
            "user_id": "test_scam_contract_user",
            "final_response": "चेतावनी: यह संदेश धोखाधड़ी प्रतीत होता है। किसी को OTP या UPI PIN न बताएं।",
            "intent": "scam_alert",
            "scam_detected": True,
            "scheme_matches": [],
            "arth_score_update": None,
            "agent_outputs": {
                "prahari": {
                    "scam_detected": True,
                    "confidence": 0.95,
                    "verdict": "SCAM",
                    "cedar_decision": {
                        "allowed": False,
                        "policy_id": "block_critical_scam_upi",
                        "reason": "Rule 1: UPI blocked due to critical scam threat",
                    },
                }
            },
        }

        with patch("main.graph.invoke", return_value=mock_graph_output):
            payload = {
                "user_id": "test_scam_contract_user",
                "message": "Send your OTP and UPI PIN immediately to avoid account block",
                "language": "en",
            }
            resp = self.client.post("/api/v1/chat", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertTrue(data.get("scam_detected"))
            prahari_output = data.get("agent_outputs", {}).get("prahari", {})
            self.assertTrue(prahari_output.get("scam_detected"))
            self.assertIn("cedar_decision", prahari_output)
            self.assertFalse(prahari_output["cedar_decision"]["allowed"])

    def test_profile_endpoints_contract(self):
        """Verify GET and POST /api/v1/profile/{user_id} contracts."""
        user_id = "test_profile_contract_user"
        profile_data = {
            "name": "दिनेश",
            "occupation": "farmer",
            "monthly_income_inr": 20000,
            "language": "hi",
            "has_bank_account": True,
        }

        # POST update
        post_resp = self.client.post(f"/api/v1/profile/{user_id}", json=profile_data)
        self.assertEqual(post_resp.status_code, 200)
        saved = post_resp.json()
        self.assertEqual(saved.get("name"), "दिनेश")

        # GET fetch
        get_resp = self.client.get(f"/api/v1/profile/{user_id}")
        self.assertEqual(get_resp.status_code, 200)
        fetched = get_resp.json()
        self.assertEqual(fetched.get("name"), "दिनेश")
        self.assertEqual(fetched.get("occupation"), "farmer")

    def test_scam_network_stats_contract(self):
        """Verify /api/v1/scam-network/stats contract."""
        with patch("tools.aws_tools._get_dynamodb", return_value=None):
            resp = self.client.get("/api/v1/scam-network/stats")
            self.assertEqual(resp.status_code, 200)
            stats = resp.json()

            self.assertIn("total_reports", stats)
            self.assertIn("top_scam_types", stats)
            self.assertIn("network_fingerprints", stats)
            self.assertIn("recent_alerts", stats)
            self.assertIsInstance(stats["top_scam_types"], list)
            self.assertIsInstance(stats["recent_alerts"], list)

    def test_cedar_audit_and_stats_contract(self):
        """Verify /api/v1/cedar/audit and /api/v1/cedar/stats contracts."""
        audit_resp = self.client.get("/api/v1/cedar/audit?limit=10")
        self.assertEqual(audit_resp.status_code, 200)
        audit_data = audit_resp.json()
        self.assertIn("audit_trail", audit_data)
        self.assertIn("count", audit_data)
        self.assertIsInstance(audit_data["audit_trail"], list)

        stats_resp = self.client.get("/api/v1/cedar/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.json()
        self.assertIn("total_evaluations", stats_data)
        self.assertIn("total_blocked", stats_data)
        self.assertIn("total_permitted", stats_data)
        self.assertIn("block_rate_pct", stats_data)

    def test_system_status_contract(self):
        """Verify /api/v1/system/status contract."""
        resp = self.client.get("/api/v1/system/status")
        self.assertEqual(resp.status_code, 200)
        status = resp.json()
        self.assertEqual(status.get("status"), "operational")
        self.assertIn("agents", status)
        self.assertIn("features", status)
        self.assertIn("cedar_firewall", status)

    def test_sse_streaming_endpoint_contract(self):
        """Verify /api/v1/chat/stream returns valid Server-Sent Events."""
        with patch("agents.extractor.extractor_node", side_effect=lambda s: s), \
             patch("agents.sutradhar.sutradhar_node", side_effect=lambda s: {**s, "intent": "general", "language": "hi", "final_response": "यहाँ सुरक्षित सुझाव हैं।"}), \
             patch("agents.prahari.prahari_node", side_effect=lambda s: {**s, "scam_detected": False}), \
             patch("agents.shilpi.shilpi_node", side_effect=lambda s: s), \
             patch("agents.vivek.vivek_node", side_effect=lambda s: s), \
             patch("core.guardrails.input_guardrail_node", side_effect=lambda s: s), \
             patch("core.guardrails.output_guardrail_node", side_effect=lambda s: s):

            payload = {
                "user_id": "test_stream_user",
                "message": "नमस्ते, मुझे बचत करने के उपाय बताएं",
                "language": "hi",
            }
            resp = self.client.post("/api/v1/chat/stream", json=payload)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/event-stream", resp.headers.get("content-type", ""))

            text = resp.text
            self.assertIn("event:", text)
            self.assertIn("data:", text)
            events = [line for line in text.split("\n") if line.startswith("data:")]
            self.assertTrue(len(events) >= 1)

            # Parse final event
            last_event_line = events[-1].replace("data:", "").strip()
            last_event = json.loads(last_event_line)
            self.assertTrue("response" in last_event or "agent" in last_event or "status" in last_event)


if __name__ == "__main__":
    unittest.main()
