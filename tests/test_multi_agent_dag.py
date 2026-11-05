"""Unit tests for the Multi-Agent DAG components and orchestration."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agents.sutradhar import _classify_locally
from agents.shilpi import _plan_locally
from tools.scheme_matcher import match_schemes
from tools.arth_score import calculate_arth_score
from core.memory import get_recent_context


class TestMultiAgentDAG(unittest.TestCase):
    def test_sutradhar_intent_classification(self):
        """Classify user intent with deterministic keyword fallbacks."""
        cases = [
            ("I received a suspicious OTP request", "scam_check"),
            ("Please decode this insurance policy document", "document"),
            ("Which government yojana can I apply for?", "scheme"),
            ("Help me plan my monthly budget and expenses", "budget"),
            ("My crops failed, need kisan help", "fasal"),
            ("What is my Arth Score today?", "score"),
            ("Explain how mutual funds work", "paisa_padhai"),
        ]
        for text, expected in cases:
            res = _classify_locally(text, "en")
            self.assertEqual(res["intent"], expected, f"Failed for text: {text}")

    def test_sutradhar_emotion_detection(self):
        """Detect urgent, stressed, and curious emotional registers."""
        urgent = _classify_locally("URGENT: Someone is stealing my money right now!", "en")
        self.assertEqual(urgent["emotional_register"], "urgent")

        stressed = _classify_locally("I am worried and scared about my family's debts", "en")
        self.assertEqual(stressed["emotional_register"], "stressed")

        curious = _classify_locally("How does a fixed deposit calculate compound interest?", "en")
        self.assertEqual(curious["emotional_register"], "curious")

    def test_shilpi_scheme_matching_farmer(self):
        """Match farming schemes (PM-KISAN, Crop Insurance, KCC) for farmers."""
        profile = {
            "occupation": "farmer",
            "land_ownership": True,
            "monthly_income_inr": 15000,
        }
        schemes = match_schemes(profile)
        matched_ids = [s["scheme_id"] for s in schemes]
        self.assertIn("PM_KISAN", matched_ids)
        self.assertIn("PMFBY", matched_ids)
        self.assertIn("KCC", matched_ids)

    def test_shilpi_scheme_matching_informal_worker(self):
        """Match unorganised sector welfare (e-Shram) for daily wage workers."""
        profile = {
            "occupation": "daily_wage",
            "not_epf_member": True,
            "monthly_income_inr": 12000,
        }
        schemes = match_schemes(profile)
        matched_ids = [s["scheme_id"] for s in schemes]
        self.assertIn("E_SHRAM", matched_ids)

    def test_shilpi_plan_locally_deterministic(self):
        """Generate deterministic budget plan when offline."""
        profile = {
            "monthly_income_inr": 20000,
            "monthly_expenses_inr": 12000,
            "occupation": "carpenter",
        }
        schemes = match_schemes(profile)
        plan = _plan_locally("Help with budget", profile, schemes)
        self.assertIn("monthly_plan", plan)
        self.assertIn("action_roadmap", plan)
        self.assertGreater(len(plan["action_roadmap"]), 0)

    def test_vivek_arth_score_resilient_profile(self):
        """Calculate high Arth Score for financially resilient profiles."""
        profile = {
            "monthly_income_inr": 50000,
            "monthly_expenses_inr": 20000,
            "emergency_fund_inr": 120000,
            "monthly_debt_emi_inr": 0,
            "has_bank_account": True,
            "has_informal_debt": False,
            "occupation": "electrician",
            "age": 32,
        }
        score_res = calculate_arth_score(profile)
        self.assertGreater(score_res["score"], 60)
        self.assertIn("cashflow_stability", score_res["dimensions"])
        self.assertIn("risk_protection", score_res["dimensions"])
        self.assertIn("debt_health", score_res["dimensions"])

    def test_vivek_arth_score_vulnerable_profile(self):
        """Calculate low Arth Score for high-debt distressed profiles."""
        profile = {
            "monthly_income_inr": 10000,
            "monthly_expenses_inr": 9000,
            "emergency_fund_inr": 0,
            "monthly_debt_emi_inr": 7000,
            "has_bank_account": False,
            "has_informal_debt": True,
        }
        score_res = calculate_arth_score(profile)
        self.assertLess(score_res["score"], 40)

    def test_vivek_arth_score_scam_penalty(self):
        """Apply awareness penalty when a scam is detected."""
        profile = {"monthly_income_inr": 30000, "monthly_expenses_inr": 20000, "has_bank_account": True}
        clean_res = calculate_arth_score(profile, latest_state={"scam_detected": False})
        scam_res = calculate_arth_score(profile, latest_state={"scam_detected": True})
        self.assertGreater(clean_res["score"], scam_res["score"])

    def test_multi_turn_memory_context_retrieval(self):
        """Verify context window retrieval returns formatted string or empty gracefully."""
        ctx = get_recent_context("non_existent_user_123", limit=3)
        self.assertIsInstance(ctx, str)


if __name__ == "__main__":
    unittest.main()
