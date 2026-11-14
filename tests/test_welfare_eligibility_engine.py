"""
ArthSetu — Welfare Scheme Eligibility Engine Test Suite
30 unique automated tests validating deterministic welfare scheme matching,
eligibility boundaries, document verification, and demographic constraints.
"""

from __future__ import annotations

import unittest
from tools.scheme_matcher import match_schemes, SCHEMES


class TestWelfareEligibilityEngine(unittest.TestCase):
    """30 unit tests covering Indian welfare schemes matching logic."""

    # -------------------------------------------------------------------------
    # 1. PM-KISAN, PMFBY & KCC (Farmers)
    # -------------------------------------------------------------------------
    def test_farmer_with_land_matches_pm_kisan_pmfby_kcc(self):
        profile = {"occupation": "farmer", "land_ownership": True, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PM_KISAN", ids)
        self.assertIn("PMFBY", ids)
        self.assertIn("KCC", ids)

    def test_farmer_without_land_matches_pmfby_but_not_pm_kisan(self):
        profile = {"occupation": "farmer", "land_ownership": False, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PMFBY", ids)
        self.assertNotIn("PM_KISAN", ids)
        self.assertNotIn("KCC", ids)

    def test_non_farmer_does_not_match_pm_kisan(self):
        profile = {"occupation": "street_vendor", "land_ownership": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("PM_KISAN", ids)

    # -------------------------------------------------------------------------
    # 2. PM SVANidhi (Street Vendors & Self Employed)
    # -------------------------------------------------------------------------
    def test_street_vendor_matches_pm_svanidhi(self):
        profile = {"occupation": "street_vendor", "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PM_SVANIDHI", ids)

    def test_self_employed_matches_pm_svanidhi(self):
        profile = {"occupation": "self_employed", "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PM_SVANIDHI", ids)

    def test_salaried_worker_does_not_match_pm_svanidhi(self):
        profile = {"occupation": "salaried", "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("PM_SVANIDHI", ids)

    # -------------------------------------------------------------------------
    # 3. Atal Pension Yojana (APY) Age & Taxpayer Boundaries
    # -------------------------------------------------------------------------
    def test_apy_eligible_at_age_18(self):
        profile = {"age": 18, "has_bank_account": True, "not_income_taxpayer": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("APY", ids)

    def test_apy_eligible_at_age_40(self):
        profile = {"age": 40, "has_bank_account": True, "not_income_taxpayer": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("APY", ids)

    def test_apy_ineligible_below_age_18(self):
        profile = {"age": 17, "has_bank_account": True, "not_income_taxpayer": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("APY", ids)

    def test_apy_ineligible_above_age_40(self):
        profile = {"age": 41, "has_bank_account": True, "not_income_taxpayer": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("APY", ids)

    def test_apy_ineligible_without_bank_account(self):
        profile = {"age": 25, "has_bank_account": False, "not_income_taxpayer": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("APY", ids)

    def test_apy_ineligible_for_income_taxpayer(self):
        profile = {"age": 28, "has_bank_account": True, "not_income_taxpayer": False}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("APY", ids)

    # -------------------------------------------------------------------------
    # 4. PMJJBY Life Insurance Age Boundaries (18 - 50)
    # -------------------------------------------------------------------------
    def test_pmjjby_eligible_at_age_18(self):
        profile = {"age": 18, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PMJJBY", ids)

    def test_pmjjby_eligible_at_age_50(self):
        profile = {"age": 50, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PMJJBY", ids)

    def test_pmjjby_ineligible_at_age_51(self):
        profile = {"age": 51, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("PMJJBY", ids)

    # -------------------------------------------------------------------------
    # 5. PMSBY Accident Insurance Age Boundaries (18 - 70)
    # -------------------------------------------------------------------------
    def test_pmsby_eligible_at_age_18(self):
        profile = {"age": 18, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PMSBY", ids)

    def test_pmsby_eligible_at_age_70(self):
        profile = {"age": 70, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("PMSBY", ids)

    def test_pmsby_ineligible_at_age_71(self):
        profile = {"age": 71, "has_bank_account": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("PMSBY", ids)

    # -------------------------------------------------------------------------
    # 6. Sukanya Samriddhi Yojana (Daughter Below 10)
    # -------------------------------------------------------------------------
    def test_sukanya_eligible_when_daughter_below_10(self):
        profile = {"has_daughter_below_10": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("SUKANYA", ids)

    def test_sukanya_ineligible_when_no_daughter_below_10(self):
        profile = {"has_daughter_below_10": False}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("SUKANYA", ids)

    # -------------------------------------------------------------------------
    # 7. NPS Vatsalya (Minor Child)
    # -------------------------------------------------------------------------
    def test_nps_vatsalya_eligible_with_child(self):
        profile = {"has_child": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("NPS_VATSALYA", ids)

    def test_nps_vatsalya_ineligible_without_child(self):
        profile = {"has_child": False}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("NPS_VATSALYA", ids)

    # -------------------------------------------------------------------------
    # 8. Disability Benefits (UDID & ADIP)
    # -------------------------------------------------------------------------
    def test_udid_eligible_with_disability(self):
        profile = {"has_disability": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("UDID", ids)

    def test_adip_eligible_with_disability_and_low_income(self):
        profile = {"has_disability": True, "monthly_income_inr": 15000}  # annual 180,000 <= 240,000
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("ADIP", ids)

    def test_adip_ineligible_with_disability_and_high_income(self):
        profile = {"has_disability": True, "monthly_income_inr": 25000}  # annual 300,000 > 240,000
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("ADIP", ids)
        self.assertIn("UDID", ids)  # UDID has no income cap

    # -------------------------------------------------------------------------
    # 9. e-Shram Registration (Informal / Unorganised Workers)
    # -------------------------------------------------------------------------
    def test_eshram_eligible_for_gig_worker_not_epf(self):
        profile = {"occupation": "gig_worker", "not_epf_member": True}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertIn("E_SHRAM", ids)

    def test_eshram_ineligible_if_epf_member(self):
        profile = {"occupation": "gig_worker", "not_epf_member": False}
        matches = match_schemes(profile)
        ids = [m["scheme_id"] for m in matches]
        self.assertNotIn("E_SHRAM", ids)

    # -------------------------------------------------------------------------
    # 10. Document Checklist & Robustness
    # -------------------------------------------------------------------------
    def test_matches_return_required_documents(self):
        profile = {"occupation": "farmer", "land_ownership": True, "has_bank_account": True}
        matches = match_schemes(profile)
        for m in matches:
            self.assertIn("documents", m)
            self.assertIsInstance(m["documents"], list)
            self.assertGreater(len(m["documents"]), 0)

    def test_empty_profile_does_not_crash_engine(self):
        matches = match_schemes({})
        self.assertIsInstance(matches, list)

    def test_all_schemes_have_valid_apply_urls(self):
        for s in SCHEMES:
            self.assertTrue(s["apply_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
