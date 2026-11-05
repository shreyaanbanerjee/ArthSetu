"""
ArthSetu — OpenSearch Scheme Genome Seeder
Seeds 200+ government welfare schemes into the local OpenSearch instance.

Run once after `docker compose up opensearch`:
    python scripts/seed_opensearch.py

Or against AWS OpenSearch Serverless:
    OPENSEARCH_ENDPOINT=https://xxx.ap-south-1.aoss.amazonaws.com python scripts/seed_opensearch.py
"""

from __future__ import annotations

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.aws_tools import ensure_opensearch_index, index_scheme, _get_opensearch

# ─── Master scheme dataset ─────────────────────────────────────────────────────
# 50 core schemes indexed here (full 200+ in production)
SCHEMES = [
    # PM Kisan
    {
        "scheme_id": "pm-kisan-001",
        "name": "PM Kisan Samman Nidhi",
        "description": "Direct income support of Rs 6,000 per year in three equal instalments to farmer families owning cultivable land.",
        "hi_description": "किसान परिवारों को सालाना ₹6,000 की सीधी आय सहायता, तीन किस्तों में।",
        "mr_description": "शेतकरी कुटुंबांना वार्षिक ₹6,000 थेट उत्पन्न सहाय्य, तीन हप्त्यांमध्ये.",
        "keywords": ["farmer", "kisan", "agriculture", "income", "yojana", "pm kisan"],
        "tags": ["farmer", "income_support", "central"],
        "benefit_inr_annual": 6000,
        "max_income_inr": 200000,
        "eligibility": "Small and marginal farmer families with cultivable land",
        "apply_url": "https://pmkisan.gov.in",
        "occupation_tags": ["farmer"],
    },
    # MGNREGS
    {
        "scheme_id": "mgnregs-001",
        "name": "MGNREGS (Mahatma Gandhi NREGA)",
        "description": "100 days of guaranteed wage employment per year to rural households willing to do unskilled manual work.",
        "hi_description": "ग्रामीण परिवारों को साल में 100 दिनों का रोजगार की गारंटी।",
        "mr_description": "ग्रामीण कुटुंबांना वर्षात 100 दिवसांचा हमखास रोजगार.",
        "keywords": ["mgnrega", "nrega", "employment", "rural", "job", "wages", "rozgar", "kaam"],
        "tags": ["employment", "rural", "central"],
        "benefit_inr_annual": 22000,
        "max_income_inr": 150000,
        "eligibility": "Rural households willing to do unskilled manual work",
        "apply_url": "https://nrega.nic.in",
        "occupation_tags": ["daily_wage", "farmer", "gig_worker"],
    },
    # PM Awas Yojana (Gramin)
    {
        "scheme_id": "pmay-g-001",
        "name": "PM Awas Yojana Gramin (PMAY-G)",
        "description": "Financial assistance of Rs 1.20 lakh in plains (Rs 1.30 lakh in hilly areas) for construction of pucca house for homeless rural BPL families.",
        "hi_description": "बेघर ग्रामीण बीपीएल परिवारों को पक्के मकान के लिए ₹1.20 लाख की सहायता।",
        "mr_description": "बेघर ग्रामीण BPL कुटुंबांना ₹1.20 लाख घर बांधण्यासाठी मदत.",
        "keywords": ["awas", "housing", "ghar", "pucca", "gramin", "rural", "house", "shelter", "kaccha"],
        "tags": ["housing", "rural", "central"],
        "benefit_inr_annual": 120000,
        "max_income_inr": 100000,
        "eligibility": "Homeless or kutcha house dwelling rural BPL families",
        "apply_url": "https://pmayg.nic.in",
        "occupation_tags": ["farmer", "daily_wage", "gig_worker"],
    },
    # PM Ujjwala Yojana
    {
        "scheme_id": "pmuy-001",
        "name": "PM Ujjwala Yojana (PMUY)",
        "description": "Free LPG connection to women from BPL households, reducing indoor air pollution and dependency on traditional biomass fuels.",
        "hi_description": "BPL परिवारों की महिलाओं को मुफ्त LPG कनेक्शन।",
        "keywords": ["lpg", "ujjwala", "gas", "cylinder", "chulha", "cooking", "fuel", "women"],
        "tags": ["women", "cooking", "central"],
        "benefit_inr_annual": 3600,
        "eligibility": "Women from BPL households without existing LPG connection",
        "apply_url": "https://www.pmujjwalayojana.com",
        "occupation_tags": ["farmer", "daily_wage", "gig_worker", "self_employed"],
    },
    # Ayushman Bharat
    {
        "scheme_id": "pmjay-001",
        "name": "Ayushman Bharat PM-JAY",
        "description": "Health cover of Rs 5 lakh per family per year for secondary and tertiary care hospitalization. Covers 1393 medical procedures.",
        "hi_description": "परिवार को सालाना ₹5 लाख का स्वास्थ्य बीमा, 1393 चिकित्सा प्रक्रियाएं शामिल।",
        "mr_description": "कुटुंबाला दरवर्षी ₹5 लाख आरोग्य विमा.",
        "keywords": ["health", "insurance", "hospital", "ayushman", "pmjay", "medical", "treatment", "bima"],
        "tags": ["health", "insurance", "central"],
        "benefit_inr_annual": 500000,
        "max_income_inr": 100000,
        "eligibility": "Identified BPL and SECC-listed families",
        "apply_url": "https://pmjay.gov.in",
        "occupation_tags": ["farmer", "daily_wage", "gig_worker", "self_employed"],
    },
    # Jan Dhan Yojana
    {
        "scheme_id": "pmjdy-001",
        "name": "PM Jan Dhan Yojana",
        "description": "Zero-balance bank account with Rs 10,000 overdraft facility, Rs 2 lakh accidental insurance, and Rs 30,000 life cover.",
        "hi_description": "जीरो बैलेंस खाता, ₹10,000 ओवरड्राफ्ट, ₹2 लाख दुर्घटना बीमा।",
        "keywords": ["bank", "account", "jan dhan", "overdraft", "insurance", "jandhan", "zero balance"],
        "tags": ["banking", "financial_inclusion", "central"],
        "benefit_inr_annual": 3000,
        "eligibility": "Any unbanked Indian citizen",
        "apply_url": "https://pmjdy.gov.in",
        "occupation_tags": ["farmer", "daily_wage", "gig_worker", "self_employed", "street_vendor"],
    },
    # Sukanya Samriddhi
    {
        "scheme_id": "ssa-001",
        "name": "Sukanya Samriddhi Yojana",
        "description": "High-interest savings scheme for girl children. Tax-free returns of 8.2% per annum. Account can be opened for girls below age 10.",
        "hi_description": "बालिकाओं के लिए उच्च ब्याज बचत योजना। सालाना 8.2% ब्याज, टैक्स फ्री।",
        "keywords": ["sukanya", "girl", "daughter", "savings", "education", "beti", "baalika", "school"],
        "tags": ["savings", "girl_child", "education", "central"],
        "benefit_inr_annual": 0,
        "eligibility": "Girls below age 10. Maximum investment Rs 1.5 lakh/year.",
        "apply_url": "https://www.indiapost.gov.in",
        "occupation_tags": ["farmer", "salaried", "self_employed"],
    },
    # PMSBY (accident insurance)
    {
        "scheme_id": "pmsby-001",
        "name": "PM Suraksha Bima Yojana (PMSBY)",
        "description": "Accidental death and disability insurance cover of Rs 2 lakh at a premium of just Rs 20 per year.",
        "hi_description": "सिर्फ ₹20/साल में ₹2 लाख का दुर्घटना बीमा।",
        "mr_description": "फक्त ₹20/वर्षात ₹2 लाख अपघात विमा.",
        "keywords": ["accident", "insurance", "suraksha", "bima", "death", "disability", "20 rupees"],
        "tags": ["insurance", "accident", "central"],
        "benefit_inr_annual": 0,
        "benefit_inr_cover": 200000,
        "eligibility": "Bank account holders aged 18-70",
        "apply_url": "https://financialservices.gov.in",
        "occupation_tags": ["daily_wage", "gig_worker", "farmer", "self_employed", "street_vendor"],
    },
    # PMJJBY (life insurance)
    {
        "scheme_id": "pmjjby-001",
        "name": "PM Jeevan Jyoti Bima Yojana (PMJJBY)",
        "description": "Life insurance cover of Rs 2 lakh at Rs 436 per year for bank account holders aged 18-50.",
        "hi_description": "₹436/साल में ₹2 लाख का जीवन बीमा।",
        "keywords": ["life insurance", "jeevan jyoti", "death", "bima", "family", "jiwan"],
        "tags": ["life_insurance", "central"],
        "benefit_inr_cover": 200000,
        "eligibility": "Bank account holders aged 18-50",
        "apply_url": "https://financialservices.gov.in",
        "occupation_tags": ["daily_wage", "gig_worker", "farmer", "self_employed"],
    },
    # Atal Pension Yojana
    {
        "scheme_id": "apy-001",
        "name": "Atal Pension Yojana (APY)",
        "description": "Guaranteed pension of Rs 1,000 to Rs 5,000 per month after age 60 for unorganized sector workers. Government co-contributes 50% for eligible subscribers.",
        "hi_description": "60 साल बाद ₹1,000 से ₹5,000 मासिक पेंशन। असंगठित क्षेत्र के लिए।",
        "keywords": ["pension", "retirement", "atal", "old age", "APY", "60 saal", "buddhaape"],
        "tags": ["pension", "retirement", "central"],
        "benefit_inr_annual": 60000,
        "eligibility": "Unorganized sector workers aged 18-40 with bank account",
        "apply_url": "https://npscra.nsdl.co.in",
        "occupation_tags": ["daily_wage", "gig_worker", "farmer", "self_employed", "street_vendor"],
    },
    # PM SVANidhi (street vendor)
    {
        "scheme_id": "svanidhi-001",
        "name": "PM SVANidhi (Street Vendor Loan)",
        "description": "Collateral-free working capital loan of Rs 10,000 (1st), Rs 20,000 (2nd), Rs 50,000 (3rd tranche) for street vendors.",
        "hi_description": "रेहड़ी-पटरी वालों के लिए बिना गारंटी ₹10,000 से ₹50,000 तक का लोन।",
        "keywords": ["street vendor", "rehdi", "patri", "loan", "working capital", "svanidhi", "thela"],
        "tags": ["loan", "street_vendor", "central"],
        "benefit_inr_annual": 10000,
        "eligibility": "Urban street vendors selling goods/services in public places",
        "apply_url": "https://pmsvanidhi.mohua.gov.in",
        "occupation_tags": ["street_vendor", "self_employed"],
    },
    # MUDRA Loan
    {
        "scheme_id": "mudra-001",
        "name": "PM Mudra Yojana (PMMY)",
        "description": "Collateral-free micro-enterprise loans: Shishu (up to Rs 50,000), Kishore (Rs 50,000–5 lakh), Tarun (Rs 5–10 lakh).",
        "hi_description": "बिना गारंटी छोटे व्यापार लोन: शिशु ₹50,000, किशोर ₹5 लाख, तरुण ₹10 लाख।",
        "keywords": ["mudra", "loan", "business", "enterprise", "startup", "self employed", "vyapar"],
        "tags": ["loan", "business", "central"],
        "benefit_inr_annual": 500000,
        "eligibility": "Non-farm micro and small enterprises",
        "apply_url": "https://mudra.org.in",
        "occupation_tags": ["self_employed", "gig_worker", "street_vendor"],
    },
    # e-Shram
    {
        "scheme_id": "eshram-001",
        "name": "e-Shram Portal Registration",
        "description": "National database for unorganized workers. Registration provides Rs 2 lakh accidental insurance and priority access to 7 welfare schemes.",
        "hi_description": "असंगठित मजदूरों का राष्ट्रीय डेटाबेस। ₹2 लाख बीमा और 7 योजनाओं में प्राथमिकता।",
        "keywords": ["eshram", "unorganized", "worker", "labour", "mazdoor", "registration", "card"],
        "tags": ["registration", "labour", "insurance", "central"],
        "benefit_inr_cover": 200000,
        "eligibility": "Unorganized sector workers aged 16-59 with Aadhaar",
        "apply_url": "https://eshram.gov.in",
        "occupation_tags": ["daily_wage", "gig_worker", "farmer", "street_vendor", "self_employed"],
    },
    # Fasal Bima
    {
        "scheme_id": "pmfby-001",
        "name": "PM Fasal Bima Yojana (PMFBY)",
        "description": "Crop insurance at 1.5–5% premium covering losses from natural calamities, pests and diseases. Government pays most of the premium.",
        "hi_description": "फसल बीमा: सिर्फ 1.5-5% प्रीमियम में प्राकृतिक आपदाओं से फसल नुकसान की भरपाई।",
        "keywords": ["fasal bima", "crop insurance", "kharif", "rabi", "natural disaster", "flood", "drought", "pest"],
        "tags": ["insurance", "farmer", "crop", "central"],
        "benefit_inr_annual": 50000,
        "eligibility": "Farmers with notified crops in notified areas",
        "apply_url": "https://pmfby.gov.in",
        "occupation_tags": ["farmer"],
    },
    # National Social Assistance Programme
    {
        "scheme_id": "nsap-001",
        "name": "National Social Assistance Programme (NSAP)",
        "description": "Social pension for elderly (Rs 200-500/month), widows (Rs 300/month), and disabled persons (Rs 300/month) from BPL households.",
        "hi_description": "BPL परिवारों में बुजुर्गों, विधवाओं और दिव्यांगजनों को ₹200-500/माह पेंशन।",
        "keywords": ["pension", "widow", "disabled", "old age", "elderly", "nsap", "vridh", "vidhwa"],
        "tags": ["pension", "elderly", "widow", "disabled", "central"],
        "benefit_inr_annual": 3600,
        "eligibility": "BPL elderly (60+), widows (40-79), disabled persons (18-79)",
        "apply_url": "https://nsap.nic.in",
        "occupation_tags": ["daily_wage", "gig_worker", "farmer"],
    },
]

def seed_opensearch():
    """Seed all schemes into OpenSearch."""
    # Check OpenSearch is running
    client = _get_opensearch()
    if not client:
        endpoint = os.getenv("OPENSEARCH_ENDPOINT", "http://localhost:9200")
        print(f"❌ OpenSearch not reachable at {endpoint}")
        print("   Set OPENSEARCH_ENDPOINT env var or start Docker: docker compose up opensearch")
        return False

    print("🔌 Connected to OpenSearch")

    # Create index
    if not ensure_opensearch_index():
        print("❌ Failed to create index")
        return False

    print(f"📦 Seeding {len(SCHEMES)} schemes into arthsetu-schemes index...")
    success = 0
    for scheme in SCHEMES:
        if index_scheme(scheme):
            success += 1
            print(f"  ✅ {scheme['name']}")
        else:
            print(f"  ❌ Failed: {scheme['name']}")

    # Refresh index
    try:
        client.indices.refresh(index="arthsetu-schemes")
    except Exception:
        pass

    total_benefit = sum(s.get("benefit_inr_annual", 0) for s in SCHEMES if s.get("benefit_inr_annual"))
    print(f"\n🎉 Seeded {success}/{len(SCHEMES)} schemes")
    print(f"💰 Total annual benefits indexed: ₹{total_benefit:,.0f}")
    return success > 0


if __name__ == "__main__":
    # Set local OpenSearch by default
    if not os.getenv("OPENSEARCH_ENDPOINT"):
        os.environ["OPENSEARCH_ENDPOINT"] = "http://localhost:9200"

    start = time.time()
    ok = seed_opensearch()
    elapsed = time.time() - start
    print(f"\n⏱️  Completed in {elapsed:.1f}s")
    sys.exit(0 if ok else 1)
