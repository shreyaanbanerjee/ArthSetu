// ═══════════════════════════════════════════════════════════════════════════
// ArthSetu — Financial Constitution (Cedar Policy File)
// Evaluated locally via cedar-policy Python SDK in < 1ms, zero API calls.
// This is the "Financial Firewall" — every action passes through these rules.
//
// Actions Covered:
//   1. InitiateUPILitePayment   — small UPI transfer
//   2. ApplyForLoan             — loan application
//   3. ShareKYCDocument         — share Aadhaar/PAN with third party
//   4. ClaimGovernmentScheme    — apply for welfare scheme
//   5. ApproveHighValueTransfer — transfer > ₹5,000
// ═══════════════════════════════════════════════════════════════════════════

// ─── Rule 1: Block UPI payment when scam threat is CRITICAL ───────────────
// "If Prahari detected a critical threat, the payment MUST not go through."
forbid (
  principal,
  action == Action::"InitiateUPILitePayment",
  resource
)
when {
  context.threat_level == "CRITICAL"
};

// ─── Rule 2: Block loan applications with dangerous debt + low Arth Score ─
// "Protect vulnerable users from predatory loans when they are already in distress."
forbid (
  principal is User,
  action == Action::"ApplyForLoan",
  resource
)
when {
  principal.arth_score < 30 &&
  context.debt_ratio > 60
};

// ─── Rule 3: Block KYC sharing with unverified requestors ─────────────────
// "Never share Aadhaar or PAN with anyone except a verified, regulated bank."
forbid (
  principal,
  action == Action::"ShareKYCDocument",
  resource
)
unless {
  context.requestor_type == "verified_bank" ||
  context.requestor_type == "government_portal"
};

// ─── Rule 4: Government scheme applications are ALWAYS permitted ──────────
// "Never block access to welfare that users are entitled to."
permit (
  principal,
  action == Action::"ClaimGovernmentScheme",
  resource
);

// ─── Rule 5: Block high-value transfers for low-score users ───────────────
// "Protect users with Arth Score < 40 from making large impulsive transfers."
forbid (
  principal is User,
  action == Action::"ApproveHighValueTransfer",
  resource is Transfer
)
when {
  principal.arth_score < 40 &&
  resource.amount_inr > 5000 &&
  context.threat_level != "SAFE"
};

// ─── Default: Permit all other actions ────────────────────────────────────
permit (
  principal,
  action,
  resource
);
