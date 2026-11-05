<p align="center">
  <img src="https://img.shields.io/badge/ArthSetu-Financial_Guardian-00C9A7?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTEyIDJ2MjBNMTcgNUg5LjVhMy41IDMuNSAwIDAgMCAwIDdoNWEzLjUgMy41IDAgMCAxIDAgN0g2Ii8+PC9zdmc+" alt="ArthSetu"/>
  <br/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/AWS-Strands_SDK-FF9900?style=flat-square&logo=amazon-aws&logoColor=white" alt="AWS"/>
  <img src="https://img.shields.io/badge/Cedar-Policy_Engine-232F3E?style=flat-square&logo=amazon-aws&logoColor=white" alt="Cedar"/>
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/NeMo-Guardrails-76B900?style=flat-square&logo=nvidia&logoColor=white" alt="NeMo"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Tests-68_Passed-2ea44f?style=flat-square&logo=githubactions&logoColor=white" alt="Tests"/>
</p>

<h1 align="center">
  🏦 ArthSetu — अर्थसेतु
</h1>

<h3 align="center">
  <em>Voice-First, Multi-Agent AI Financial Guardian for Bharat</em>
</h3>

<p align="center">
  <strong>Paisa Samajho, Zindagi Badlo</strong> — <em>Understand Money, Transform Life</em>
</p>

<p align="center">
  A deterministic multi-agent financial security system powered by AWS Strands Agents SDK, Cedar Policy Engine, and NeMo Guardrails — designed for India's 400M+ underbanked population. Every financial action passes through a <strong>5-rule Cedar "Financial Constitution"</strong> evaluated in <strong>&lt;1ms</strong>, zero API calls, and all AI responses are verified by an <strong>Automated AI Evaluation Engine (LLM-as-a-Judge)</strong>.
</p>

---

## 📊 Architecture at a Glance

| Metric | Value |
|---|---|
| **Total Source Files** | **57+ files** across Python, TypeScript, CSS, Cedar, YAML, Bash |
| **Total Lines of Code** | **9,800+ LoC** (hand-written, zero boilerplate) |
| **Automated Test Suite** | **68 comprehensive unit, integration & AI validation tests** (100% pass, 0.10s runtime) |
| **AI Response Validator** | **6-dimension automated evaluation engine** (LLM-as-a-judge + deterministic rubric) |
| **AI Agents** | **5 specialized agents** + 1 orchestrator in a deterministic DAG |
| **REST & SSE Endpoints** | **14 endpoints** including SSE real-time streaming, Cedar audit trail, scam network, AI validation |
| **Cedar Policy Rules** | **5 deterministic financial firewall rules** with audit trail & stats |
| **NeMo Guardrail Layers** | **2 layers** (input + output) with **8 safety & injection patterns** |
| **PII Detection Patterns** | **6 Indian PII regex patterns** (Aadhaar, PAN, IFSC, UPI PIN, bank account, credit card) |
| **Scam Detection Patterns** | **30 weighted regex rules** + LLM dual-scoring (0.72 threshold) |
| **Government Schemes DB** | **15+ welfare schemes** with eligibility matching & OpenSearch vector search |
| **Intent Classifications** | **16 distinct intents** with hybrid LLM + keyword fallback |
| **Supported Languages** | **13 Indian languages** with speech biofeedback and native TTS fallbacks |
| **Omnichannel Delivery** | **4 channels** — OLED PWA, WhatsApp (Twilio), Telegram, Voice |
| **AWS Cloud Services** | **SQS, DynamoDB (Pay-Per-Request + TTL), Lambda, OpenSearch, SAM CloudFormation** |
| **Infrastructure Containers** | **7 Docker services** (API, Worker, Beat, Redis, RabbitMQ, LocalStack, OpenSearch) |
| **Cedar Policy Eval Latency** | **< 1ms** (pure-Python, zero external calls) |
| **Predatory Loan APR Alert** | **> 36% APR** auto-flagged with True Cost computation |
| **Conversation Memory** | **5-turn context window** for multi-turn dialogue continuity |
| **Rate Limiting** | **30 req/min** per IP (token bucket middleware) |
| **Security Headers** | **6 headers** (HSTS, X-Frame-Options, CSP, XSS-Protection, Permissions-Policy) |

---

## 🧠 Multi-Agent Graph Architecture

ArthSetu runs a **deterministic directed acyclic graph (DAG)** where every user message flows through specialized AI agents. Prahari (fraud sentinel) fires on **every single message** — no scam goes unchecked.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│              (Voice / Text / Document / WhatsApp)                    │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   INPUT         │  Layer 1: PII Redaction (Aadhaar, PAN, UPI PIN, IFSC)
              │   GUARDRAILS    │  Prompt Injection Detection (8 rules)
              │   (NeMo)        │  Toxicity Filter + Length Cap (2,000 chars)
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   SUTRADHAR     │  Pass 1: Intent Classification
              │   (Orchestrator)│  16 intents × 4 emotions × 13 languages
              │   Gemini 2.5    │  Hybrid: LLM + deterministic keyword fallback
              └────────┬────────┘
                       │
           ┌───────────┼───────────┬───────────┐
           ▼           ▼           ▼           ▼
    ┌────────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │  PRAHARI   │ │ BODHAK │ │ SHILPI │ │ VIVEK  │
    │  (Fraud    │ │ (Doc   │ │ (Budget│ │ (Score │
    │  Sentinel) │ │ Decode)│ │ Planner│ │ Coach) │
    │ ALWAYS ON  │ │        │ │ +Scheme│ │        │
    └─────┬──────┘ └───┬────┘ └───┬────┘ └───┬────┘
          │            │          │           │
          │     ┌──────┴──────────┴───────────┘
          │     │
          ▼     ▼
    ┌─────────────────┐      ┌──────────────────┐
    │  CEDAR POLICY   │      │   SUTRADHAR       │
    │  FIREWALL       │◄─────│   Pass 2:         │
    │  5 Rules, <1ms  │      │   Response         │
    └─────────────────┘      │   Synthesis        │
                             └────────┬───────────┘
                                      │
                                      ▼
                             ┌─────────────────┐
                             │   OUTPUT         │  Layer 2: Hallucination Check
                             │   GUARDRAILS     │  Financial Safety Regex (Anti-guarantee)
                             │   (NeMo)         │  PII Echo Prevention
                             └────────┬─────────┘  Auto-Disclaimer Injection (SEBI/IRDAI)
                                      │
                                      ▼
                             ┌─────────────────┐
                             │  AUTOMATED AI   │  LLM-as-a-Judge Evaluation Engine
                             │  EVALUATION     │  Validates across 6 safety dimensions
                             └────────┬────────┘
                                      │
                                      ▼
                             ┌─────────────────┐
                             │   RESPONSE       │
                             │   (PWA/WhatsApp/ │
                             │    Telegram/TTS) │
                             └─────────────────┘
```

### Agent Breakdown

| Agent | Role | Model | Key Capabilities |
|---|---|---|---|
| **Sutradhar** (सूत्रधार) | Orchestrator | Gemini 2.5 Flash | Intent classification (16 labels), language detection (13 langs), multi-turn memory injection (5 turns), response synthesis, emotional register detection |
| **Prahari** (प्रहरी) | Fraud Sentinel | Gemini 2.5 Flash | Scam detection (LLM + rule-based dual scoring), Cedar policy gate, SQS scam reporting, predatory loan APR calculation, RBI Sachet reporting |
| **Bodhak** (बोधक) | Document Decoder | Gemini 2.5 Flash | Financial document simplification, jargon elimination, key clause extraction, one-action-now recommendations |
| **Shilpi** (शिल्पी) | Budget Planner | Gemini 2.5 Flash | Income-aware budget plans, government scheme matching (15+ schemes), seasonal income flex, action roadmaps |
| **Vivek** (विवेक) | Score Coach | Gemini 2.5 Flash | Arth Score computation (0–100, 5 dimensions), financial habit tracking, personalized nudges, myth busting |
| **Extractor** | Profile Learner | Deterministic | Dynamic profile extraction from conversations, auto-updates income/occupation/family data |

---

## 🤖 Automated AI Response Validation (LLM-as-a-Judge)

ArthSetu introduces an automated evaluation and validation layer (`core/ai_evaluator.py`) ensuring that every AI-generated advice adheres to strict ethical, regulatory, and constitutional standards before reaching users.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AUTOMATED AI VALIDATION ENGINE                       │
│           (LLM-as-a-Judge with Deterministic Rubric Fallback)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
  │Financial Safety │      │PII Containment  │      │Cedar Alignment  │
  │• Anti-guarantee │      │• Zero Aadhaar   │      │• Block compliance│
  │• No crypto push │      │• Zero PAN leak  │      │• Scam warnings  │
  │• Disclaimers    │      │• Zero UPI PIN   │      │• Threat triage  │
  └─────────────────┘      └─────────────────┘      └─────────────────┘
           │                        │                        │
           ▼                        ▼                        ▼
  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
  │ Actionability   │      │Empathy & Tone   │      │ Factual Faith   │
  │• Concrete steps │      │• De-escalation  │      │• Valid schemes  │
  │• Plain language │      │• Calm register  │      │• Accurate rates │
  │• Sequential flow│      │• Reassurance    │      │• No hallucination│
  └─────────────────┘      └─────────────────┘      └─────────────────┘
```

### The 6 Evaluation Dimensions

1. **Financial Safety & Regulatory Compliance (25% weight)**:
   - Bans deceptive claims of "100% guaranteed returns", "risk-free profits", and "doubling money".
   - Bans promotion of high-risk speculative instruments (crypto, futures, options).
   - Enforces regulatory disclosures (SEBI / IRDAI / RBI) whenever formal products are discussed.

2. **PII Containment & Zero-Leakage (20% weight)**:
   - Prohibits reflecting or leaking Aadhaar numbers, PAN identifiers, UPI PINs, or bank passwords.

3. **Cedar Policy & Threat Alignment (20% weight)**:
   - Verifies that when Prahari detects a scam, the AI response explicitly issues a fraud warning and does **not** instruct the user to proceed with payment.
   - Confirms that actions blocked by Cedar Constitution rules reflect explicit lockdown notices.

4. **Actionability & Practical Guidance (15% weight)**:
   - Evaluates whether the advice gives tangible, sequence-based next steps (e.g. portal URLs, document lists) rather than vague advice.

5. **Empathy & Emotional Register (10% weight)**:
   - Analyzes user distress cues (fear, moneylender threats, panic) and ensures the tone provides calming, empathetic de-escalation.

6. **Factual Faithfulness & Anti-Hallucination (10% weight)**:
   - Validates that recommended government welfare schemes match official canonical schemes (PM-KISAN, PM SVANidhi, PMJJBY, PMSBY, APY, etc.) without fabricated schemes.

---

## 🔒 Security Architecture — The Financial Firewall

### Cedar Policy Engine (5 Constitutional Rules)

ArthSetu enforces a **"Financial Constitution"** — a set of deterministic Cedar policies that **cannot be bypassed** by any LLM or agent. Every financial action is evaluated in **< 1ms** with zero external API calls.

```cedar
// Rule 1: Block UPI payment when scam threat is CRITICAL
forbid (principal, action == Action::"InitiateUPILitePayment", resource)
when { context.threat_level == "CRITICAL" };

// Rule 2: Block loans when user is in financial distress
forbid (principal is User, action == Action::"ApplyForLoan", resource)
when { principal.arth_score < 30 && context.debt_ratio > 60 };

// Rule 3: Never share KYC with unverified parties
forbid (principal, action == Action::"ShareKYCDocument", resource)
unless { context.requestor_type == "verified_bank" || context.requestor_type == "government_portal" };

// Rule 4: Government scheme access is ALWAYS permitted
permit (principal, action == Action::"ClaimGovernmentScheme", resource);

// Rule 5: Block high-value transfers for vulnerable users
forbid (principal is User, action == Action::"ApproveHighValueTransfer", resource is Transfer)
when { principal.arth_score < 40 && resource.amount_inr > 5000 && context.threat_level != "SAFE" };
```

### NeMo Guardrails (Dual-Layer)

| Layer | Stage | Protections |
|---|---|---|
| **Input Guardrails** | Pre-Agent | PII redaction (Aadhaar, PAN, IFSC, UPI PIN, bank account, credit card), prompt injection detection (8 patterns), toxicity filter, input length cap (2,000 chars) |
| **Output Guardrails** | Post-Synthesis | Hallucination check (via NeMo LLMRails), financial safety regex (blocks guaranteed return claims, brand endorsements, direct buy recommendations), PII echo prevention, auto-disclaimer injection, response length cap (1,500 chars for WhatsApp) |

---

## ☁️ AWS Cloud Architecture (Ship It Track)

ArthSetu leverages AWS serverless and managed services optimally configured for high availability, zero idle costs, and low latency:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS ap-south-1 (Mumbai)                      │
│                                                                  │
│  ┌──────────────┐     ┌──────────────────┐    ┌──────────────┐  │
│  │    SQS        │────▶│  Lambda           │───▶│  DynamoDB    │  │
│  │  ScamReport   │     │  FraudParser      │    │  ScamReports │  │
│  │  Queue        │     │  (batch=10)       │    │  (TTL: 24h)  │  │
│  │  (24h retain) │     │  256MB, 30s       │    │              │  │
│  └──────────────┘     └──────────────────┘    │  ScamNetwork │  │
│                                                │  (fingerprint│  │
│  ┌──────────────┐     ┌──────────────────┐    │   dedup)     │  │
│  │  EventBridge  │────▶│  Lambda           │    └──────────────┘  │
│  │  rate(1 hour) │     │  ScamAggregator   │                     │
│  └──────────────┘     └──────────────────┘    ┌──────────────┐  │
│                                                │  OpenSearch   │  │
│  ┌──────────────┐                              │  arthsetu-    │  │
│  │    S3         │                              │  schemes      │  │
│  │  (artifacts)  │                              │  (vector)     │  │
│  └──────────────┘                              └──────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| AWS Service | Resource Name / Config | Purpose & Cost Optimization |
|---|---|---|
| **Amazon SQS** | `ArthSetu-ScamReportQueue` | Asynchronous decoupled scam ingestion queue; 24h retention, 60s visibility timeout. Zero user latency during chat. |
| **AWS Lambda** | `ArthSetu-FraudParser` | Triggered by SQS batch (batch size 10), extracts fraud fingerprints, updates DynamoDB tables. Memory: 256MB, 30s timeout. |
| **AWS Lambda** | `ArthSetu-ScamAggregator` | Hourly fingerprint aggregation triggered by EventBridge `rate(1 hour)`. Identifies scam waves. |
| **Amazon DynamoDB** | `ArthSetu-ScamReports` | Individual scam reports; `PAY_PER_REQUEST` billing (zero idle costs), TTL-enabled (24h retention) to minimize storage. |
| **Amazon DynamoDB** | `ArthSetu-ScamNetwork` | Aggregated scam intelligence network; keyed by SHA256 fingerprint hash (`phone#<hash>`, `upi#<hash>`, `url#<hash>`). |
| **Amazon OpenSearch** | `arthsetu-schemes` (2.11) | Semantic vector & text search for 15+ welfare schemes matched against user profile constraints. |
| **AWS SAM CLI** | `template.yaml` + `samconfig.toml` | Infrastructure as Code (IaC) defining IAM least-privilege roles, queues, tables, and serverless functions. |
| **LocalStack** | Docker service (`4566:4566`) | Complete local AWS emulation of SQS, DynamoDB, S3, and Lambda for zero-cost local development and testing. |

---

## 🧪 Automated Testing Framework & Verification

ArthSetu includes an extensive automated test suite with **68 test cases** across 7 specialized modules, achieving a **100% pass rate** in ~**0.10 seconds**.

```
======================================================================
  🏦 ArthSetu Automated Test Suite
  Evaluating Multi-Agent DAG, Cedar Policy Firewall & AWS Integrations
======================================================================

📦 Discovered 68 automated tests across test modules.
....................................................................
----------------------------------------------------------------------
Ran 68 tests in 0.097s — OK

======================================================================
  📊 Test Execution Summary
======================================================================
  • Total Tests Run : 68
  • Passed          : 68 (100%)
  • Failures        : 0
  • Errors          : 0
  • Execution Time  : 0.10 seconds
======================================================================
  ✅ ALL TESTS PASSED PERFECTLY!
```

### Test Suite Breakdown

| Test Suite | File | Tests | Coverage Scope |
|---|---|:---:|---|
| **AI Response Validation** | `tests/test_ai_validation.py` | 9 | Evaluates phishing fraud alerts, predatory loan true cost warnings, street vendor scheme accuracy, distressed worker empathy, PII containment failures, illegal guaranteed return rejections, and live `/api/v1/eval/validate` & `/api/v1/chat/validate` endpoints. |
| **Cedar Policy Engine** | `tests/test_cedar_engine.py` | 11 | All 5 Financial Constitution rules (UPI critical block, loan distress block, KYC unverified block, scheme permit, high value transfer block), audit logging, audit stats aggregation, Prahari decision integration |
| **Scam Detection & APR** | `tests/test_scam_engine.py` | 11 | OTP & UPI PIN theft detection, electricity disconnect fraud, fake KYC expiry, AnyDesk remote access, 100% guaranteed return scams, clean query safety, APR true-cost calculator (>36% predatory loans), loan term extraction, RBI Sachet packet generation |
| **Dual-Layer Guardrails** | `tests/test_guardrails.py` | 9 | Layer 1 PII redaction (Aadhaar, PAN, UPI PIN, IFSC), prompt injection defenses (DAN, jailbreaks, system prompt leak), abuse filters, input character truncation (2,000 char cap), Layer 2 auto-disclaimer injection (SEBI/IRDAI), financial guarantee cleanup |
| **AWS Cloud Tools** | `tests/test_aws_tools.py` | 11 | Phone, UPI ID, and URL fingerprint extraction, SHA-256 fingerprint hashing, SQS push with graceful offline degradation, DynamoDB ScamNetwork collective intelligence lookup, OpenSearch vector search fallback, threat telemetry stats |
| **Multi-Agent DAG** | `tests/test_multi_agent_dag.py` | 9 | Sutradhar intent classification (16 intents), emotional register detection (urgent, stressed, curious), Shilpi scheme matching (farmers, daily wage workers), deterministic budget roadmap generation, Vivek Arth Score computation (0-100, 5 dimensions, scam penalty), multi-turn memory retrieval |
| **ASGI API & Middleware** | `tests/test_api_endpoints.py` | 8 | Health check (`/health`), Root (`/`), System status (`/api/v1/system/status`), Cedar audit & stats (`/api/v1/cedar/*`), Scam Network stats (`/api/v1/scam-network/stats`), User Profile CRUD, Chat endpoint schema, Security headers verification (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, etc.) |

### Running the Tests

```bash
# Run the complete test suite with formatted summary
python run_tests.py

# Run in verbose mode
python run_tests.py --verbose

# Run via unittest discovery
python -m unittest discover tests

# Run via pytest (if installed)
pytest tests/ -v
```

---

## 🌐 REST & Streaming API Reference

ArthSetu exposes **14 production ASGI endpoints** with built-in token-bucket rate limiting (30 req/min per IP) and strict security headers:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status, version, and active features |
| `GET` | `/` | API overview and service motto |
| `POST` | `/api/v1/chat` | Main multi-agent chat endpoint with multi-turn memory (5 turns) |
| `POST` | `/api/v1/chat/stream` | **Server-Sent Events (SSE)** streaming real-time agent execution status |
| `POST` | `/api/v1/chat/validate` | **End-to-end chat execution with automated AI validation report** |
| `POST` | `/api/v1/eval/validate` | **Validate any AI response along the 6-dimension evaluation rubric** |
| `GET` | `/api/v1/system/status` | Comprehensive status of all 5 agents, Cedar firewall, and features |
| `GET` | `/api/v1/cedar/stats` | Aggregated Cedar policy metrics (total evaluations, block rate, top blocked actions) |
| `GET` | `/api/v1/cedar/audit` | Compliance-grade audit trail of all policy evaluations with filter by `user_id` |
| `GET` | `/api/v1/scam-network/stats`| Collective intelligence threat telemetry from DynamoDB & local stores |
| `GET` | `/api/v1/profile/{user_id}` | Retrieve financial profile for a user |
| `POST` | `/api/v1/profile/{user_id}` | Upsert user profile data (occupation, income, expenses, debt) |
| `GET` | `/api/v1/session/{user_id}` | Retrieve active conversation session and agent states |
| `GET` | `/api/v1/history/{user_id}` | Retrieve full historical conversation turns |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ (Python 3.11 recommended)
- Node.js 18+
- Docker & Docker Compose
- AWS CLI & SAM CLI (`brew install awscli aws-sam-cli`)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/shreyaanbanerjee/ArthSetu.git
cd ArthSetu

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY and GROQ_API_KEY to .env
```

### 2. Run Automated Tests

```bash
python run_tests.py
```

### 3. Start Infrastructure (Docker)

```bash
# Starts Redis, RabbitMQ, LocalStack (AWS emulation), and OpenSearch
docker compose up -d redis rabbitmq localstack opensearch
```

### 4. Bootstrap AWS Resources & Seed OpenSearch

```bash
python scripts/bootstrap_aws.py
python scripts/seed_opensearch.py
```

### 5. Run the ASGI Server

```bash
uvicorn main:app --reload --port 8000
```

### 6. Run the Voice-First Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## ☁️ Optimal AWS Cloud Deployment Guide

### Automated One-Click Deployment

We provide an automated deployment script that runs the test suite, verifies credentials, bootstraps tables, and builds/deploys the SAM application:

```bash
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh
```

### Manual SAM CLI Deployment

```bash
# 1. Configure AWS credentials
aws configure
# Region: ap-south-1

# 2. Build SAM application
sam build

# 3. Deploy to production
sam deploy --config-file samconfig.toml --config-env production --no-confirm-changeset

# 4. Inspect stack outputs
sam list stack-outputs --stack-name arthsetu-stack --region ap-south-1
```

### GitHub Actions CI/CD Pipeline

The repository includes an enterprise-grade GitHub Actions workflow (`.github/workflows/deploy.yml`):
1. **Automated Testing:** Runs all 68 tests on Python 3.10 and 3.11 on every push and PR.
2. **Frontend Verification:** Builds and verifies the Next.js 15 PWA.
3. **Continuous Deployment:** Automatically builds SAM and deploys the CloudFormation stack to AWS `ap-south-1` on pushes to `main`.

---

## 📁 Project Structure

```
ArthSetu/
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions CI/CD & AWS SAM deployment
│
├── agents/                    # 5 Specialized AI Agents (775 LoC)
│   ├── sutradhar.py           #   Orchestrator — intent classification + multi-turn synthesis
│   ├── prahari.py             #   Fraud sentinel — scam detection + Cedar gate + SQS push
│   ├── bodhak.py              #   Document decoder — simplifies financial documents
│   ├── shilpi.py              #   Budget planner — income-aware plans + scheme matching
│   ├── vivek.py               #   Score coach — Arth Score computation + nudges
│   └── extractor.py           #   Profile learner — dynamic profile extraction
│
├── core/                      # Engine Layer (1,450 LoC)
│   ├── graph.py               #   DAG runner — deterministic agent orchestration
│   ├── ai_evaluator.py        #   Automated AI response evaluation engine (6 dimensions)
│   ├── llm.py                 #   Unified LLM interface (Gemini REST + Groq)
│   ├── cedar_engine.py        #   Pure-Python Cedar policy evaluator (<1ms, 5 rules)
│   ├── guardrails.py          #   NeMo Guardrails — dual-layer safety & PII redaction
│   ├── memory.py              #   Multi-turn context memory & persistence (SQLite/Redis)
│   ├── strands_agents.py      #   AWS Strands SDK agent interface
│   └── dpi.py                 #   India DPI integration (NPCI, UPI)
│
├── tools/                     # Shared Tool Library (850 LoC)
│   ├── aws_tools.py           #   SQS, DynamoDB ScamNetwork, OpenSearch operations
│   ├── scam_engine.py         #   30 scam patterns + APR true-cost calculator
│   ├── scheme_matcher.py      #   15+ government welfare schemes eligibility engine
│   ├── arth_score.py          #   5-dimension financial resilience score (0–100)
│   ├── ocr.py                 #   Document OCR pipeline
│   └── stt_tts.py             #   Speech-to-text / text-to-speech
│
├── tests/                     # Automated Test Suite (68 Tests, 100% Pass)
│   ├── test_ai_validation.py  #   Elaborate automated AI response evaluation tests
│   ├── test_cedar_engine.py   #   Cedar policy 5-rule financial firewall tests
│   ├── test_scam_engine.py    #   Prahari fraud detection & APR calculator tests
│   ├── test_guardrails.py     #   Input & output guardrails & PII redaction tests
│   ├── test_aws_tools.py      #   AWS SQS, DynamoDB, OpenSearch mock & fallback tests
│   ├── test_multi_agent_dag.py#   Multi-agent DAG orchestration & memory tests
│   └── test_api_endpoints.py  #   Starlette REST & security middleware tests
│
├── channels/                  # Omnichannel Delivery (380 LoC)
│   ├── whatsapp_twilio.py     #   WhatsApp via Twilio API
│   └── telegram.py            #   Telegram Bot integration
│
├── lambda/                    # Serverless Functions (160 LoC)
│   └── fraud_parser/
│       ├── handler.py         #   SQS → DynamoDB scam report parser
│       └── aggregator.py      #   Hourly scam fingerprint aggregation
│
├── policies/
│   └── guardrails.cedar       # 5-Rule Financial Constitution (75 LoC)
│
├── scripts/
│   ├── bootstrap_aws.py       # Automated AWS resource provisioning (SQS, DynamoDB)
│   ├── seed_opensearch.py     # Government scheme vector indexing
│   └── deploy_aws.sh          # One-click verification & SAM deployment script
│
├── frontend/                  # Next.js 15 PWA (2,800 LoC)
│   ├── app/
│   │   ├── page.tsx           #   Voice-first hub with pulsating orb visualizer
│   │   ├── globals.css        #   OLED dark theme + glassmorphism
│   │   ├── schemes/page.tsx   #   Government scheme explorer
│   │   ├── score/page.tsx     #   Arth Score dashboard
│   │   └── educator/page.tsx  #   Financial literacy module
│   └── server.js              #   Standalone static server
│
├── run_tests.py               # Unified test runner with formatted reporting
├── main.py                    # Production Starlette ASGI server (14 endpoints + SSE)
├── config.py                  # Centralized configuration (96 env vars)
├── template.yaml              # AWS SAM CloudFormation template (ap-south-1)
├── samconfig.toml             # SAM CLI deployment parameters
├── docker-compose.yml         # 7-service Docker stack (including LocalStack & OpenSearch)
├── Dockerfile                 # Container build definition
└── requirements.txt           # Python dependencies
```

---

## 🔑 Key Design Decisions

1. **Prahari Fires on Every Message** — Unlike systems that only check flagged content, Prahari runs on 100% of messages. This ensures no scam slips through, even if disguised as a benign query.

2. **Cedar > LLM for Authorization** — Financial actions (UPI payments, loan applications, KYC sharing) are gated by deterministic Cedar policies, not LLM reasoning. This makes the security layer unhackable by prompt injection. Every decision is logged to a compliance-grade audit trail.

3. **Automated AI Response Validation** — Every synthesized financial response can be verified through the automated evaluation judge (`/api/v1/chat/validate`) across 6 regulatory and safety dimensions.

4. **Dual-Scoring Scam Detection** — Every message gets both an LLM-based probability score AND a rule-based pattern match score (30 weighted regex patterns). The final confidence is `max(llm_score, rule_score)`, eliminating blind spots of either approach.

5. **Graceful Degradation** — Every external dependency (Redis, SQS, DynamoDB, OpenSearch, Gemini API) has a local fallback. The system runs fully offline with SQLite + JSON file storage + keyword-based classification.

6. **Voice-First, Not Voice-Also** — The Web Speech API integration is a first-class citizen, not an afterthought. In 13 Indian languages, users can speak naturally and receive spoken responses.

7. **Multi-Turn Conversation Memory** — The system injects the last 5 conversation turns into the synthesis prompt, enabling follow-up questions like "tell me more" or "explain the second point" without losing context.

8. **SSE Streaming for Real-Time UX** — Instead of a single JSON response after all agents finish, the `/api/v1/chat/stream` endpoint streams agent status updates in real-time via Server-Sent Events: `"🛡️ Scanning for scams..."` → `"📄 Decoding document..."` → `"✨ Final response"`.

9. **Scam Intelligence Network** — Every detected scam feeds into an aggregated intelligence network (SQS → Lambda → DynamoDB). The `/api/v1/scam-network/stats` endpoint surfaces collective patterns so the system gets smarter with every interaction.

10. **Production Security Hardening** — Token bucket rate limiting (30 req/min per IP), 6 security headers (X-Frame-Options, CSP, XSS-Protection), and PII redaction ensure the system is production-ready, not just a hackathon prototype.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>अर्थसेतु</strong> — <em>The bridge between financial vulnerability and financial empowerment.</em>
  <br/>
  Built for the WeMakeDevs × AWS Hackathon 🇮🇳
</p>
