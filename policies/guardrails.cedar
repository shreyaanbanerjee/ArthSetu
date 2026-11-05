// Financial action authorization policies for ArthSetu.
// Evaluated deterministically before sensitive financial operations.

// Rule 1: Forbid UPI payments if a critical fraud threat was detected
forbid (
  principal,
  action == Action::"InitiateUPILitePayment",
  resource
)
when {
  context.threat_level == "CRITICAL"
};

// Rule 2: Forbid loan applications for accounts under acute debt distress
forbid (
  principal is User,
  action == Action::"ApplyForLoan",
  resource
)
when {
  principal.arth_score < 30 &&
  context.debt_ratio > 60
};

// Rule 3: Forbid sharing KYC documents with unverified third parties
forbid (
  principal,
  action == Action::"ShareKYCDocument",
  resource
)
unless {
  context.requestor_type == "verified_bank" ||
  context.requestor_type == "government_portal"
};

// Rule 4: Unconditionally permit government scheme discovery and claims
permit (
  principal,
  action == Action::"ClaimGovernmentScheme",
  resource
);

// Rule 5: Block high-value transfers during active high-threat warnings for fragile accounts
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

// Default policy: permit actions that are not explicitly forbidden
permit (
  principal,
  action,
  resource
);
