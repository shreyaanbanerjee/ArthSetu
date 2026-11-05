"""Integration tests for Starlette ASGI REST and SSE endpoints."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from starlette.testclient import TestClient

from main import app


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_health_check(self):
        """GET /health returns 200 OK."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "arthsetu")

    def test_root_endpoint(self):
        """GET / returns project info and motto."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Paisa Samajho, Zindagi Badlo", data["message"])

    def test_security_headers_present(self):
        """Verify production security headers on HTTP responses."""
        response = self.client.get("/health")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-xss-protection"), "1; mode=block")
        self.assertEqual(response.headers.get("referrer-policy"), "strict-origin-when-cross-origin")

    def test_system_status(self):
        """GET /api/v1/system/status returns active agents and Cedar metrics."""
        response = self.client.get("/api/v1/system/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "operational")
        self.assertIn("agents", data)
        self.assertIn("sutradhar", data["agents"])
        self.assertIn("prahari", data["agents"])
        self.assertIn("cedar_firewall", data)
        self.assertEqual(data["cedar_firewall"]["rules_loaded"], 5)

    def test_cedar_stats_and_audit(self):
        """GET /api/v1/cedar/stats and /audit return compliance audit trail."""
        stats_resp = self.client.get("/api/v1/cedar/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertIn("total_evaluations", stats)

        audit_resp = self.client.get("/api/v1/cedar/audit?limit=10")
        self.assertEqual(audit_resp.status_code, 200)
        audit = audit_resp.json()
        self.assertIn("audit_trail", audit)
        self.assertIsInstance(audit["audit_trail"], list)

    def test_scam_network_stats_endpoint(self):
        """GET /api/v1/scam-network/stats returns network threat telemetry."""
        with patch("tools.aws_tools._get_dynamodb", return_value=None):
            resp = self.client.get("/api/v1/scam-network/stats")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("total_reports", data)
            self.assertIn("top_scam_types", data)

    def test_user_profile_crud(self):
        """GET and POST /api/v1/profile/{user_id} manages user profile."""
        user_id = "test_api_user"
        update_payload = {"occupation": "carpenter", "monthly_income_inr": 22000}
        post_resp = self.client.post(f"/api/v1/profile/{user_id}", json=update_payload)
        self.assertEqual(post_resp.status_code, 200)

        get_resp = self.client.get(f"/api/v1/profile/{user_id}")
        self.assertEqual(get_resp.status_code, 200)
        profile = get_resp.json()
        self.assertEqual(profile.get("occupation"), "carpenter")

    def test_chat_endpoint_schema(self):
        """POST /api/v1/chat processes query and returns full agent responses."""
        mock_result = {
            "user_id": "test_chat_user",
            "final_response": "Here are the welfare schemes you can apply for.",
            "intent": "scheme",
            "scam_detected": False,
            "scheme_matches": [{"scheme_id": "PM_KISAN", "name": "PM-KISAN"}],
            "agent_outputs": {"prahari": {"cedar_allowed": True, "verdict": "CLEAR"}},
        }
        with patch("main.graph.invoke", return_value=mock_result):
            resp = self.client.post(
                "/api/v1/chat",
                json={
                    "user_id": "test_chat_user",
                    "message": "Which schemes are available for farmers?",
                },
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("final_response", data)
            self.assertEqual(data["intent"], "scheme")
            self.assertFalse(data["scam_detected"])


if __name__ == "__main__":
    unittest.main()
