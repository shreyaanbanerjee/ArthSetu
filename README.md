# ArthSetu

ArthSetu is a vernacular financial assistant, scam defense engine, and transaction authorization proxy built for informal-sector workers and underbanked populations in India. The system processes voice and text queries in regional Indian languages (Hindi, Marathi, Tamil, Telugu, Kannada, Bengali, Gujarati, Punjabi, and English), screens incoming communications for fraudulent patterns and predatory lending terms, gates sensitive actions through deterministic Cedar policies, and matches users with eligible welfare programs.

---

## Architecture

```
User Query (Voice / Text / Document / WhatsApp / Telegram)
                       │
                       ▼
            [ Layer 1: Input Guardrails ]
              • Indian PII masking (Aadhaar, PAN, UPI PIN, IFSC, Card numbers)
              • Prompt injection and jailbreak screening
              • Input length truncation (2,000 characters)
                       │
                       ▼
            [ Router: Sutradhar ]
              • Language detection (9 regional languages)
              • Intent classification (16 supported intents)
              • Multi-turn dialogue memory (last 5 turns)
                       │
         ┌─────────────┼─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
    [ Prahari ]   [ Bodhak ]    [ Shilpi ]    [ Vivek ]
    Scam Sentinel  Document OCR  Welfare Plans Financial Score
    Dual scoring   Contract APR  Scheme match  Resilience gauge
    SQS threat bus Jargon strip  Budget flex   Habit tracking
         │             │             │             │
         └─────────────┴──────┬──────┴─────────────┘
                              │
                              ▼
            [ Cedar Policy Firewall ]
              • 5 deterministic authorization rules
              • Pure-Python evaluation (<1ms latency)
              • SQLite compliance audit trail
                              │
                              ▼
            [ Layer 2: Output Guardrails & Synthesis ]
              • Anti-guarantee and anti-speculation filters
              • Regulatory disclaimers (SEBI, IRDAI, RBI)
              • Automated AI response evaluation (6-point rubric)
                              │
                              ▼
    Response Delivery (Web UI / Voice Audio / WhatsApp / Telegram)
```

### Agent Pipeline

- **Sutradhar (Orchestrator)**: Manages dialogue state, detects the user's language and emotional register (calm, stressed, urgent), coordinates specialist agents, and synthesizes technical findings into plain vernacular language.
- **Prahari (Fraud Sentinel)**: Runs dual-scoring analysis on every inbound message using 30 weighted regex pattern signatures combined with LLM triage. High-confidence scams trigger threat reports sent to an AWS SQS queue and cross-reference phone, UPI, and URL fingerprints against the DynamoDB collective intelligence network.
- **Bodhak (Document Decoder)**: Extracts terms from financial documents (loan sanction letters, payslips, passbooks, Form 16) via OCR, identifies hidden charges or variable fee clauses, and computes true Annual Percentage Rates (APR).
- **Shilpi (Budget & Welfare Program Matcher)**: Matches user profile attributes (occupation, income bracket, land ownership, dependents) against central and state government schemes (e.g. PM SVANidhi, PM-KISAN, PMSBY, PMJJBY, Mudra, Sukanya Samriddhi).
- **Vivek (Financial Resilience Coach)**: Calculates the multi-dimensional Arth Score (0 to 100) across liquidity buffers, debt servicing ratios, emergency savings runway, and insurance coverage.

---

## AWS Cloud Infrastructure (ap-south-1)

ArthSetu is structured around serverless AWS components designed for low operating overhead, pay-per-request pricing, and automatic horizontal scaling:

```
                  ┌──────────────────────────────────────────────┐
                  │            AWS Region: ap-south-1            │
                  │                                              │
Inbound Scam ────▶│  SQS: ArthSetu-ScamReportsQueue              │
Report            │         │                                    │
                  │         ▼                                    │
                  │  Lambda: FraudParserFunction (256MB)         │
                  │         │                                    │
                  │         ├──────────────────────────┐         │
                  │         ▼                          ▼         │
                  │  DynamoDB:               DynamoDB:           │
                  │  ArthSetu-ScamReports    ArthSetu-ScamNetwork│
                  │  (Raw reports, 24h TTL)  (Aggregated hashes) │
                  │                                    ▲         │
                  │  EventBridge: rate(1 hour)         │         │
                  │         │                          │         │
                  │         ▼                          │         │
                  │  Lambda: ScamAggregatorFunction ───┘         │
                  │                                              │
                  │  OpenSearch: arthsetu-schemes                │
                  │  (Vector index for scheme eligibility)       │
                  └──────────────────────────────────────────────┘
```

### Offline Graceful Degradation

Every cloud integration implements local fallbacks:
- **DynamoDB & SQS**: When AWS credentials are not configured or the network is unavailable, scam reports are written directly to local SQLite tables (`.arthsetu_data/arthsetu.db`) and memory queues.
- **OpenSearch**: Falls back to the in-memory deterministic scheme matching engine in `tools/scheme_matcher.py`.
- **LLM Providers**: Primary inference uses Groq (`llama-3.1-8b-instant`); falls back to Gemini 2.5 Flash, and ultimately to local rule-based responses if all external providers are offline.

---

## Deterministic Policy Enforcement (Cedar)

Financial authorization logic is enforced by deterministic Cedar policies (`policies/guardrails.cedar`) rather than generative model outputs:

```cedar
// Rule 1: Block UPI transfers when scam threat is critical
forbid (principal, action == Action::"InitiateUPILitePayment", resource)
when { context.threat_level == "CRITICAL" };

// Rule 2: Block high-interest debt when user is in financial distress
forbid (principal is User, action == Action::"ApplyForLoan", resource)
when { principal.arth_score < 30 && context.debt_ratio > 60 };

// Rule 3: Restrict KYC sharing to verified institutions
forbid (principal, action == Action::"ShareKYCDocument", resource)
unless { context.requestor_type == "verified_bank" || context.requestor_type == "government_portal" };

// Rule 4: Government welfare claims are always permitted
permit (principal, action == Action::"ClaimGovernmentScheme", resource);

// Rule 5: Limit high-value transfers (>Rs 5,000) for vulnerable users under threat
forbid (principal is User, action == Action::"ApproveHighValueTransfer", resource is Transfer)
when { principal.arth_score < 40 && resource.amount_inr > 5000 && context.threat_level != "SAFE" };
```

Every decision produces an audit log entry recorded in SQLite with the policy identifier, action, principal, timestamp, contextual snapshot, and latency in milliseconds.

---

## Automated AI Response Validation (LLM-as-a-Judge)

Generated financial advice is validated via an automated evaluation engine (`core/ai_evaluator.py`) before delivery. Responses are scored against a 6-dimension evaluation rubric:

| Dimension | Weight | Pass Criteria | Target Violations Flagged |
|---|---|---|---|
| **Financial Safety** | 25% | Requires SEBI/IRDAI/RBI disclaimers on formal products. Prohibits guaranteed returns and speculative assets. | "100% safe profit", "double money", unvetted crypto/options tips. |
| **PII Containment** | 20% | Zero reflection or extraction of user credentials. | 12-digit Aadhaar, 10-character PAN, 4-6 digit UPI PINs. |
| **Cedar Alignment** | 20% | Text advice must directly reflect policy enforcement decisions. | Instructing payments when Cedar denied an action or Prahari detected a threat. |
| **Actionability** | 15% | Requires specific, ordered next steps or official portal references. | Vague platitudes without actionable procedural guidance. |
| **Empathy & Tone** | 10% | Calms distressed users facing moneylender threats or sudden loss. | Dismissive tone, robotic refusals, or compounding panic. |
| **Factual Faithfulness** | 10% | Scheme terms, interest rates, and loan caps must match official programs. | Fabricated subsidy amounts or hallucinated welfare programs. |

---

## Frontend User Interface

The frontend (`frontend/app/page.tsx`, `frontend/app/globals.css`) is designed according to Indian public utility and fintech design conventions (BHIM, UMANG, DigiLocker, PhonePe):

- **Header Bar**: Displays the emblem branding, vernacular language selector, active user profile chip, connection status indicator, and audio mute/unmute control.
- **Top Navigation Tabs**:
  1. **संवाद सहायक (Assistant)**: Active conversational stream with speech synthesis audio controls (`🔊 सुनें`), Prahari threat indicators (`✓ सुरक्षित` or `🛡️ धोखाधड़ी चेतावनी`), and a voice input button with live recording waveform feedback.
  2. **सरकारी योजनाएं (Schemes)**: Curated welfare schemes with verified annual benefits, eligibility criteria, required documentation lists, and direct links to official government portals.
  3. **अर्थ स्कोर (Arth Score)**: Circular resilience gauge (0–100) with health band classification and a breakdown of 4 financial pillars (Savings Rate, Debt Servicing, Emergency Runway, Insurance Safety Net).
  4. **सुरक्षा कवच (Fraud Shield)**: Sentinel operational status, collective scam indicators, and direct 1-tap emergency action buttons (National Helpline `1930`, RBI Sachet portal, and National Cybercrime portal).
  5. **इतिहास (History)**: Chronological interaction timeline with query logs, assistant verdicts, and Cedar policy decisions.
- **Profile Configuration Modal**: Form enabling users to update income, occupation, expenses, existing loan EMIs, bank account status, and dependents. Attributes sync to `/api/v1/profile/{user_id}` and persist locally.

---

## API Reference

The backend exposes 14 REST and Server-Sent Events endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service greeting and status message |
| `GET` | `/health` | Service health status and runtime version |
| `POST` | `/api/v1/chat` | Main synchronous chat endpoint; runs the multi-agent graph |
| `POST` | `/api/v1/chat/stream` | Server-Sent Events (SSE) streaming endpoint with live agent status events |
| `POST` | `/api/v1/chat/validate` | End-to-end chat execution paired with automated AI evaluation report |
| `POST` | `/api/v1/eval/validate` | Standalone AI evaluation endpoint for arbitrary query/response pairs |
| `GET` | `/api/v1/profile/{user_id}` | Fetch user financial profile attributes |
| `POST` | `/api/v1/profile/{user_id}` | Upsert user financial profile attributes |
| `GET` | `/api/v1/session/{user_id}` | Retrieve latest session state and agent outputs |
| `GET` | `/api/v1/history/{user_id}` | Fetch stored multi-turn conversation history |
| `GET` | `/api/v1/scam-network/stats` | Aggregate scam intelligence statistics from local DB and DynamoDB |
| `GET` | `/api/v1/cedar/audit` | Retrieve Cedar authorization decision audit log |
| `GET` | `/api/v1/cedar/stats` | Aggregate Cedar policy evaluation metrics (total, blocked, permitted, latency) |
| `GET` | `/api/v1/system/status` | Runtime system status, active agents, and enabled security middleware |

### Example: Chat Request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_101",
    "message": "मुझे पीएम स्वनिधि योजना के बारे में बताएं",
    "language": "hi"
  }'
```

### Example: AI Response Evaluation Request

```bash
curl -X POST http://localhost:8000/api/v1/eval/validate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "They are asking for Rs 500 fee upfront to release a Rs 50,000 instant loan.",
    "response": "This is an advance-fee loan fraud. Legitimate banks never charge upfront release fees. Do not transfer any money. Report the incident to 1930.",
    "scam_detected": true
  }'
```

---

## Automated Test Suite (88 Tests, 100% Pass)

The unified test suite (`run_tests.py`) covers unit logic, integration boundaries, policy enforcement, vernacular patterns, and frontend API contracts:

| Test Module | Test Count | Scope |
|---|---|---|
| `tests/test_cedar_engine.py` | 11 tests | Cedar 5-rule financial firewall, SQLite audit log, and statistical aggregation. |
| `tests/test_ai_validation.py` | 9 tests | Automated AI response evaluation across all 6 rubric dimensions and validation endpoints. |
| `tests/test_ai_evaluator_edge_cases.py` | 6 tests | Adversarial prompt injection against the evaluator, empty strings, PII leakage, omitted warnings. |
| `tests/test_scam_engine.py` | 11 tests | 30 regex scam patterns, APR computation, predatory rate warnings (>36%), RBI Sachet packets. |
| `tests/test_vernacular_flows.py` | 7 tests | Hindi OTP theft, Marathi electricity disconnection scams, Hinglish fees, and Devanagari regexes. |
| `tests/test_frontend_contracts.py` | 7 tests | Schema and key validation for all API endpoints consumed by `page.tsx`, including SSE streaming. |
| `tests/test_guardrails.py` | 9 tests | PII masking (Aadhaar, PAN, IFSC, UPI PIN), prompt injection blocking, and disclaimer injection. |
| `tests/test_multi_agent_dag.py` | 9 tests | Multi-agent state orchestration, emotion recognition, multi-turn memory, and Arth score calculation. |
| `tests/test_aws_tools.py` | 11 tests | SQS push, DynamoDB fingerprint queries, OpenSearch fallbacks, and SHA-256 hash consistency. |
| `tests/test_api_endpoints.py` | 8 tests | Starlette HTTP routing, token-bucket rate limiting (30 req/min), and production security headers. |
| **Total** | **88 tests** | **100% pass rate in ~8 seconds.** |

### Running the Tests

```bash
# Run all 88 automated tests
python run_tests.py

# Run with verbose test-by-test reporting
python run_tests.py -v
```

---

## Getting Started

### Prerequisites

- Python 3.9+ (Python 3.10 or 3.11 recommended)
- Node.js 18+ and npm
- Optional: AWS CLI and AWS SAM CLI (for cloud deployment)

### Backend Installation

1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your keys (GROQ_API_KEY, GEMINI_API_KEY, etc.)
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

   Open `http://localhost:3000` in your browser.

---

## AWS Deployment

### Serverless Application Model (SAM)

1. Verify AWS CLI configuration:
   ```bash
   aws sts get-caller-identity
   ```

2. Build and deploy the SAM stack:
   ```bash
   sam build
   sam deploy --config-file samconfig.toml --config-env production
   ```

Provisioned AWS resources:
- `ArthSetu-ScamReportsQueue`: SQS queue for incoming fraud reports (24-hour retention).
- `ArthSetu-ScamReports`: DynamoDB table for raw scam reports with automated Time-To-Live (TTL).
- `ArthSetu-ScamNetwork`: DynamoDB table for deduplicated scammer phone, UPI, and URL fingerprints.
- `FraudParserFunction`: Lambda function triggered by SQS queue batches.
- `ScamAggregatorFunction`: Hourly Lambda function for cluster analysis.

---

## Configuration Reference

Key configuration parameters in `config.py` (customizable via `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `""` | Primary LLM inference API key |
| `GEMINI_API_KEY` | `""` | Secondary LLM inference API key |
| `AWS_REGION` | `ap-south-1` | Target AWS deployment region |
| `SQS_QUEUE_URL` | `""` | SQS queue endpoint for scam triage |
| `DYNAMODB_SCAM_TABLE` | `ArthSetu-ScamReports` | DynamoDB scam reports table name |
| `DYNAMODB_NETWORK_TABLE` | `ArthSetu-ScamNetwork` | DynamoDB scam intelligence table name |
| `OPENSEARCH_ENDPOINT` | `""` | OpenSearch cluster endpoint for scheme search |
| `SCAM_CONFIDENCE_THRESHOLD` | `0.72` | Minimum confidence score to trigger scam warnings |
| `APR_WARNING_THRESHOLD` | `36.0` | APR percentage above which loans are flagged as predatory |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache and session store (falls back to SQLite) |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
