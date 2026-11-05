# ArthSetu

ArthSetu is a vernacular financial assistant and transaction guardrail service designed for informal-sector workers and underbanked individuals in India. It accepts natural-language and voice queries in regional languages (Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Punjabi, Urdu, and English), parses incoming financial communications for fraud or predatory lending patterns, evaluates high-risk actions against deterministic authorization policies, and matches users with eligible central and state welfare programs.

## Architecture

```
User Query (Voice / Text / Document)
         │
         ▼
[ Layer 1: Input Guardrails ]
  - PII masking (Aadhaar, PAN, UPI PIN, IFSC, Card numbers)
  - Prompt injection detection
  - Input truncation
         │
         ▼
[ Router: Sutradhar ]
  - Language identification (13 regional languages)
  - Intent classification (16 intents)
         │
    ┌────┴────────────────────────┬──────────────────────┐
    ▼                             ▼                      ▼
[ Prahari ]                  [ Bodhak ]             [ Shilpi & Vivek ]
  - Dual scam scoring          - Document OCR         - Scheme matching
  - APR calculation            - Clause breakdown     - Arth credit score
  - SQS threat queue
    │
    └─────────────────────────────┬──────────────────────┘
                                  │
                                  ▼
[ Cedar Policy Engine ]
  - 5 deterministic authorization rules
  - SQLite audit trail logging
                                  │
                                  ▼
[ Layer 2: Output Guardrails & Synthesis ]
  - Anti-guarantee validation
  - Auto-disclaimer injection (SEBI / IRDAI)
  - Automated AI response evaluation (6-point rubric)
                                  │
                                  ▼
Response Delivery (Web UI / WhatsApp / Telegram)
```

### Core Components

1. **Sutradhar (Orchestrator)**: Classifies user intent and language, manages conversation history (last 5 turns), and synthesizes agent outputs into plain language.
2. **Prahari (Fraud Sentinel)**: Scans incoming messages using a combination of 30 regex patterns and LLM triage. Flagged threats are pushed to AWS SQS and checked against cached phone and UPI fingerprints in DynamoDB.
3. **Bodhak (Document Decoder)**: Parses loan contracts, payslips, and bank notices to extract effective interest rates, hidden charges, and mandatory obligations.
4. **Shilpi (Budget & Welfare Programs)**: Matches user profile attributes (income, occupation, state, landholding) against central and state government schemes (e.g. PM SVANidhi, Mudra, PMSBY, PMJJBY).
5. **Vivek (Financial Resilience Coach)**: Calculates the Arth Score (0 to 100) across liquidity, emergency buffers, debt burden, and insurance coverage.
6. **Cedar Policy Engine**: Evaluates financial operations against explicit, deterministic policies. Actions such as initiating UPI payments during high-risk conditions or applying for high-interest loans with severe debt ratios are denied at the policy level before reaching fulfillment APIs.
7. **Automated AI Response Evaluator**: A 6-dimension evaluation engine (`core/ai_evaluator.py`) that inspects generated advice against regulatory standards, PII leak rules, policy decisions, and scheme validity.

## Getting Started

### Prerequisites

- Python 3.9+ (Python 3.10 or 3.11 recommended)
- Node.js 18+ and npm
- Optional: AWS CLI and AWS SAM CLI (for cloud deployment)
- Optional: Docker and Docker Compose (for local multi-service testing)

### Backend Setup

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
   # Edit .env with your API keys (GROQ_API_KEY, GEMINI_API_KEY, etc.)
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The service starts on `http://localhost:8000`.

### Frontend Setup

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

## API Reference

The backend exposes the following REST and streaming endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service health check greeting |
| `GET` | `/health` | Service health status and version |
| `POST` | `/api/v1/chat` | Main synchronous chat endpoint; runs the agent pipeline |
| `POST` | `/api/v1/chat/stream` | Server-Sent Events (SSE) streaming chat endpoint |
| `POST` | `/api/v1/chat/validate` | End-to-end chat execution with automated AI quality evaluation |
| `POST` | `/api/v1/eval/validate` | Standalone AI evaluation endpoint for arbitrary query/response pairs |
| `GET` | `/api/v1/profile/{user_id}` | Fetch user financial profile |
| `POST` | `/api/v1/profile/{user_id}` | Upsert user financial profile attributes |
| `GET` | `/api/v1/session/{user_id}` | Fetch latest user session state |
| `GET` | `/api/v1/history/{user_id}` | Fetch conversation turn history |
| `GET` | `/api/v1/scam-network/stats` | Aggregate scam intelligence statistics |
| `GET` | `/api/v1/cedar/audit` | Fetch Cedar authorization decision audit log |
| `GET` | `/api/v1/cedar/stats` | Aggregated Cedar policy enforcement metrics |
| `GET` | `/api/v1/system/status` | Runtime system status and feature availability |

### Example: Chat Request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "मुझे पीएम स्वनिधि योजना के बारे में बताएं",
    "language": "hi",
    "user_id": "user_101"
  }'
```

### Example: AI Response Evaluation Request

```bash
curl -X POST http://localhost:8000/api/v1/eval/validate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Is this loan safe? They are asking for ₹500 fee first to release ₹50,000",
    "response": "This is a standard advance-fee scam. Do not pay any money. Report the caller to 1930.",
    "scam_detected": true
  }'
```

## Security & Policy Enforcement

### Cedar Policy Rules

Cedar policies are declared in `policies/guardrails.cedar` and evaluated deterministically by `core/cedar_engine.py`:

- **Rule 1 (`block_critical_scam_upi`)**: Forbids `InitiateUPILitePayment` whenever Prahari detects a `CRITICAL` scam threat.
- **Rule 2 (`block_distressed_user_loan`)**: Forbids `ApplyForLoan` when the user's Arth Score is below 30 and debt-to-income ratio exceeds 60%.
- **Rule 3 (`restrict_kyc_sharing`)**: Forbids `ShareKYCDocument` unless the requesting entity is a verified bank or government portal.
- **Rule 4 (`permit_welfare_schemes`)**: Permits all users to claim government welfare schemes regardless of score.
- **Rule 5 (`limit_high_value_transfers`)**: Forbids `ApproveHighValueTransfer` over ₹5,000 for users with an Arth Score below 40 unless threat level is `SAFE`.

All decisions are recorded in an SQLite audit database (`.arthsetu_data/arthsetu.db`) with timestamps, evaluation latencies, and contextual parameters.

### AI Response Evaluation Rubric

The evaluation engine tests responses against 6 weighted criteria:

1. **Financial Safety & Regulatory Compliance (25%)**: Prohibits guaranteed-return claims, unvetted stock tips, and cryptocurrency recommendations. Requires SEBI/IRDAI disclaimers on regulated products.
2. **PII Containment (20%)**: Verifies no Aadhaar, PAN, UPI PIN, or bank credentials appear in generated responses.
3. **Cedar Policy Alignment (20%)**: Ensures the text advice aligns with the Cedar engine verdict (e.g. clear warning on blocked actions).
4. **Actionability (15%)**: Requires concrete next steps, documentation requirements, or portal details.
5. **Tone & Empathy (10%)**: Checks for supportive language when user expressions indicate distress or anxiety.
6. **Factual Accuracy (10%)**: Ensures cited welfare schemes and interest rate caps reflect actual program guidelines.

## Running Tests

Execute the unified test suite:

```bash
python run_tests.py
```

The runner discovers all unit and integration tests across:
- `tests/test_cedar_engine.py`: Cedar policy evaluator and audit logger.
- `tests/test_ai_validation.py`: AI response evaluator and validation endpoints.
- `tests/test_scam_engine.py`: Pattern detection, loan APR calculations, and RBI reporting.
- `tests/test_guardrails.py`: PII redaction and input sanitization.
- `tests/test_aws_tools.py`: SQS and DynamoDB fallback behavior.
- `tests/test_multi_agent_dag.py`: Agent state transitions and multi-turn context retention.
- `tests/test_api_endpoints.py`: Starlette routing, rate limiting, and security headers.

To build and check frontend types:

```bash
cd frontend
npm run build
```

## AWS Deployment

### Serverless Application Model (SAM)

1. Ensure AWS CLI and SAM CLI are configured:
   ```bash
   aws configure --profile default
   ```

2. Build and deploy:
   ```bash
   sam build
   sam deploy --config-file samconfig.toml --config-env production
   ```

Resources provisioned:
- SQS Queue: `ArthSetu-ScamReportsQueue` (scam reports with 24-hour retention)
- DynamoDB Table: `ArthSetu-ScamReports` (raw reports with TTL)
- DynamoDB Table: `ArthSetu-ScamNetwork` (aggregated fingerprint indicators)
- Lambda Functions: `FraudParserFunction` (processes SQS queue) and `ScamAggregatorFunction` (hourly rollup)

## Configuration

Key settings in `config.py` (customizable via `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `""` | LLM inference backend |
| `GEMINI_API_KEY` | `""` | Secondary LLM inference backend |
| `AWS_REGION` | `ap-south-1` | Target AWS region |
| `SQS_QUEUE_URL` | `""` | SQS endpoint for scam queuing |
| `DYNAMODB_SCAM_TABLE` | `ArthSetu-ScamReports` | DynamoDB scam reports table |
| `DYNAMODB_NETWORK_TABLE` | `ArthSetu-ScamNetwork` | DynamoDB network intelligence table |
| `OPENSEARCH_ENDPOINT` | `""` | OpenSearch cluster endpoint for scheme search |
| `SCAM_CONFIDENCE_THRESHOLD` | `0.72` | Minimum confidence score to trigger scam warnings |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache and session store (falls back to SQLite) |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
