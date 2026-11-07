# PayGuard AI 🛡️💳
> **Enterprise Autonomous Payment Orchestration & Healing Platform**  
> Built for the **PayPal AI Hackathon ($67,500)** on Devpost.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PayPal](https://img.shields.io/badge/PayPal-Complete_Payments-003087.svg?logo=paypal&logoColor=white)](https://developer.paypal.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Real--time_Store-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-Analytics_Engine-FF6384.svg?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)

---

## 💡 The Problem: The $260 Billion Checkout Failure Void

Global e-commerce merchants lose **$260 Billion annually** to checkout friction and payment declines. When a shopper's credit or debit card is declined due to strict issuer fraud heuristics, velocity caps, or international currency blocks, traditional payment gateways present an unhelpful error:

> *"Card Declined. Please use another payment method."*

**Over 72% of shoppers abandon their cart immediately** upon seeing this screen.

**PayGuard AI** eliminates cart abandonment by transforming failed checkout events into instant, automated revenue recovery. Operating directly in the payment flow, PayGuard AI uses a 3-agent autonomous architecture to intercept declines in real time, diagnose root causes via ISO 8583 banking telemetry, and heal the transaction through the optimal **PayPal Complete Payments** product.

---

## 🧠 Autonomous Multi-Agent Diagnostic Pipeline

```mermaid
flowchart TD
    User["🛒 Shopper Checkout"] -->|Card Payment Attempt| Gateway["Payment Gateway Simulator"]
    Gateway -->|ISO 8583 Decline Code| Sentinel["Agent 01: Sentinel Agent\n(Telemetry & Ingestion)"]
    
    subgraph PayGuard AI Core Engine
        Sentinel -->|Raw Card Metadata & ISO Code| Diagnostician["Agent 02: Diagnostician Agent\n(Bayesian Propensity Scoring)"]
        Diagnostician -->|Optimal Remediation Vector| Healer["Agent 03: Healer Agent\n(PayPal Complete Payments Orchestrator)"]
        Healer --> OrdersV2["PayPal Orders v2 API & Pay Later Synthesis"]
    end
    
    OrdersV2 --> Copilot["PayGuard Interactive AI Copilot"]
    Copilot -->|1-Click PayPal Recovery UI| User
    User -->|Instant Approval| Captured["✅ Rescued & Captured in SQLite Event Store"]
```

### The 3 Core Agents:
1. **Sentinel Agent (Telemetry & Ingestion):**
   - Intercepts raw ISO 8583 banking response codes (`51: NSF`, `59: Suspected Fraud`, `82: Currency Mismatch`, `91: Interchange Latency`).
   - Extracts BIN range, risk heuristics, and liquidity telemetry in under **15 milliseconds**.
2. **Diagnostician Agent (Propensity Scoring Engine):**
   - Evaluates a multi-dimensional propensity vector across 4 PayPal remediation strategies:
     * `PAYPAL_PAY_LATER` (Pay in 4 installments)
     * `PAYPAL_VERIFIED_WALLET` (Biometric / 2FA authenticated wallet)
     * `PAYPAL_DYNAMIC_FX` (Real-time foreign exchange clearance)
     * `PAYPAL_FASTLANE` (Accelerated 1-tap guest checkout)
3. **Healer Agent (PayPal Orders v2 Synthesizer):**
   - Constructs production-grade PayPal Orders v2 payloads with strict authorization schemas.
   - Formulates dynamic Pay in 4 installment schedules and powers the real-time NLP Shopper Copilot.

---

## 🚀 Key Platform Views

### 1. 🛒 Shopper Checkout & AI Copilot Experience
- **Interactive Decline Simulator:** Toggle 4 realistic banking decline scenarios live.
- **Real-Time Agent Monologue:** Shows the AI's step-by-step diagnostic reasoning in real time.
- **Pay in 4 Installment Calculator:** Automatically calculates bi-weekly 0% interest schedules.
- **Conversational Shopper Copilot:** Contextual NLP chat assistant with FAQ quick pills (*"Any interest or fees?"*, *"Why did it decline?"*, *"Is my purchase protected?"*).
- **Web Audio Feedback:** Native Web Audio API synthesizer for tactile UI sound effects.

### 2. 📊 Merchant AI Operations War Room
- **Live Revenue Tickers:** Real-time Rescued GMV, Recovery Lift Rate (%), and Rescued Carts.
- **Interactive Visualizations (Chart.js):**
  - Doughnut chart of ingested decline signatures.
  - Bar chart of recovered orders by PayPal product.
- **Live SQLite Event Audit Stream:** Complete transaction log tracking timestamps, customers, amounts, decline codes, strategies, and execution latencies.

### 3. 🧠 Neural Architecture Visualizer
- Deep-dive inspection into the 3-agent pipeline and the Remediation Strategy Decision Matrix.

---

## 🏃 Quick Start

### 1. Clone & Enter Repository
```bash
git clone https://github.com/kpunia306/payguard-ai.git
cd payguard-ai
```

### 2. Launch the Platform
```bash
cd backend
python3 server.py
```
*Platform starts at `http://localhost:5055`.*

### 3. Open in Browser
Open `http://localhost:5055` in Google Chrome or Safari to test the live checkout, AI reasoning stream, and Merchant War Room!

---

## 📡 Production-Grade REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/checkout` | Simulates ISO 8583 banking decline & triggers 3-agent diagnosis |
| `POST` | `/api/paypal/create-order` | Synthesizes compliant PayPal Orders v2 JSON object |
| `POST` | `/api/paypal/capture-order` | Captures order, updates SQLite database, and recalculates lift |
| `GET` | `/api/merchant/analytics` | Returns real-time GMV metrics, charts data, and audit feed |
| `POST` | `/api/copilot/chat` | Contextual NLP assistant answering checkout questions |

---

## 🏆 Hackathon Details
- **Hackathon:** PayPal AI Hackathon (Devpost)
- **Author:** Krish Punia ([@kpunia306](https://github.com/kpunia306))
- **Track:** AI Agents & Intelligent Commerce
- **License:** MIT
