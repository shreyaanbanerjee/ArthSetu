# ArthSetu (अर्थसेतू) — Demonstration & Presentation Guide

## 🚀 Running Services (Currently Active on your Mac)
* **Frontend Application:** [http://localhost:3000](http://localhost:3000)
* **Backend Multi-Agent API:** [http://localhost:8000](http://localhost:8000) (`/health` is `200 OK`)

---

## 🎬 Video Recording Walkthrough Script

When you record your demo video, follow this flow to showcase the full depth of the project:

### 1. Introduction (0:00 - 0:45)
* Open [http://localhost:3000](http://localhost:3000).
* Explain the problem: 500M+ vernacular and informal workers in India face predatory lending, complex welfare forms, and SMS phishing scams.
* Show the **Profile Setup**: Set Name to `Ramesh Kumar`, Occupation to `Street vendor`, Monthly income `25000`, and click **Continue**.

### 2. The Voice-First OLED Interface (0:45 - 1:30)
* Highlight the screen-free design philosophy: The **Pulsating Audio Visualizer Orb** provides visual biofeedback (idle, listening, thinking).
* Show the **Top Status Bar** with connection status, active agents, and security firewall.

### 3. Welfare Scheme Discovery with Shilpi (1:30 - 2:30)
* Click the quick nudge card or type:
  > *"Which government schemes am I eligible for as a street vendor?"*
* **What to highlight:**
  - Multi-agent orchestration via **Sutradhar**.
  - **Shilpi** matching schemes tailored to a street vendor earning ₹25k/month (PM SVANidhi with interest subsidy, PMJJBY insurance, PMSBY accident cover).
  - Unlocked welfare value in rupees per year.

### 4. Fraud Defense, SQS, DynamoDB & AWS Cedar Firewall (2:30 - 4:00)
* Type or speak:
  > *"URGENT: Your electricity power will be disconnected tonight. Pay ₹100 immediately at http://power-cut-bill.in"*
* **What to highlight:**
  - **Prahari** immediately identifies the urgency hook and phishing link.
  - **AWS Cedar Policy Engine** evaluates the action in `< 1ms` and triggers a **FORBID / DENIED** verdict, locking down payments.
  - **Amazon SQS (`ArthSetu-ScamReportQueue`)** queues the fraud fingerprint asynchronously.
  - **DynamoDB (`ArthSetu-ScamNetwork`)** cross-checks collective community intelligence.

### 5. Arth Score & Behavioral Mirror with Vivek (4:00 - 5:00)
* Click **Arth Score** in the navigation.
* Show the 5 dimensional score breakdown: Cashflow Buffer, Debt Health, Scheme Coverage, Fraud Immunity, and Advisory Engagement.
* Explain how it provides positive reinforcement rather than punitive credit scoring.

### 6. Vernacular Accessibility (5:00 - 5:30)
* Toggle the language dropdown between **हिंदी (Hindi)** and **English** to demonstrate multi-lingual inclusivity.

---

## 🏗️ Architecture & AWS Technology Stack
* **Orchestration:** Python Starlette / FastAPI, Multi-Agent A2A Graph (Sutradhar, Prahari, Shilpi, Vivek, Bodhak).
* **AI & Voice:** Gemini 2.5 Flash / Groq LLMs, Web Speech API.
* **Security:** AWS Cedar Policy Engine (`policies/guardrails.cedar`), Dual-layer PII & injection guardrails.
* **Cloud Infrastructure (Ship It Track):**
  - **Amazon SQS:** `ArthSetu-ScamReportQueue`
  - **AWS Lambda:** `ArthSetu-FraudParser` (`lambda/fraud_parser/handler.py`)
  - **Amazon DynamoDB:** `ArthSetu-ScamReports` & `ArthSetu-ScamNetwork`
  - **Amazon OpenSearch:** `arthsetu-schemes`
* **Frontend:** Next.js, OLED Dark Glassmorphism, Neon Radial Audio Visualizer.
