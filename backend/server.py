"""
PayGuard AI - Enterprise Autonomous Payment Orchestration & Healing Platform
Built for the PayPal AI Hackathon ($67,500)
Architecture:
  - Multi-Agent Payment Diagnostic Pipeline (Sentinel -> Diagnostician -> Healer)
  - ISO 8583 Banking Gateway Simulator with 5 Real-world Decline Codes
  - PayPal Complete Payments (PPCP) Orders v2 Engine & Pay Later Orchestrator
  - SQLite Real-Time Event Store & Analytics Engine
  - Real-Time Streaming Agent Monologue & NLP Copilot
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="../frontend", static_url_path="")

DB_PATH = os.path.join(os.path.dirname(__file__), "payguard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        customer_name TEXT,
        customer_email TEXT,
        amount REAL,
        currency TEXT,
        initial_status TEXT,
        decline_code TEXT,
        recovery_strategy TEXT,
        final_status TEXT,
        paypal_order_id TEXT,
        recovered_amount REAL,
        resolution_time_ms INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        agent_role TEXT,
        step_name TEXT,
        thought TEXT,
        confidence REAL,
        execution_time_ms INTEGER
    )
    """)
    conn.commit()

    # Seed initial realistic historical data if empty
    cur.execute("SELECT COUNT(*) FROM transactions")
    count = cur.fetchone()[0]
    if count == 0:
        seed_historical_data(cur)
        conn.commit()
    conn.close()

def seed_historical_data(cur):
    strategies = [
        ("INSUFFICIENT_FUNDS", "PAYPAL_PAY_LATER", 240.00, "RECOVERED"),
        ("FRAUD_SUSPECTED", "PAYPAL_VERIFIED_WALLET", 380.00, "RECOVERED"),
        ("CURRENCY_MISMATCH", "PAYPAL_DYNAMIC_FX", 195.00, "RECOVERED"),
        ("LIMIT_EXCEEDED", "PAYPAL_PAY_LATER", 450.00, "RECOVERED"),
        ("BANK_TIMEOUT", "PAYPAL_FASTLANE", 120.00, "RECOVERED"),
        ("INSUFFICIENT_FUNDS", "PAYPAL_PAY_LATER", 310.00, "RECOVERED"),
        ("FRAUD_SUSPECTED", "PAYPAL_VERIFIED_WALLET", 520.00, "RECOVERED"),
        ("INSUFFICIENT_FUNDS", "ABANDONED", 280.00, "DROPPED"),
    ]
    base_time = datetime.now() - timedelta(hours=12)
    for i, (code, strat, amt, status) in enumerate(strategies * 4):
        tx_id = f"TX-INIT-{1000 + i}"
        t = base_time + timedelta(minutes=i * 18)
        cur.execute("""
        INSERT INTO transactions (id, timestamp, customer_name, customer_email, amount, currency, initial_status, decline_code, recovery_strategy, final_status, paypal_order_id, recovered_amount, resolution_time_ms)
        VALUES (?, ?, ?, ?, ?, 'USD', 'DECLINED', ?, ?, ?, ?, ?, ?)
        """, (
            tx_id, t.isoformat(), f"Shopper_{100+i}", f"shopper_{100+i}@domain.com", amt, code, strat,
            "COMPLETED" if status == "RECOVERED" else "ABANDONED",
            f"PP-REC-{uuid.uuid4().hex[:6].upper()}" if status == "RECOVERED" else None,
            amt if status == "RECOVERED" else 0.0,
            random.randint(1200, 3800)
        ))

# Initialize database on launch
init_db()


# ---------------------------------------------------------------------
# MULTI-AGENT DIAGNOSTIC & HEALING CORE
# ---------------------------------------------------------------------

class SentinelAgent:
    """Agent 1: Ingests raw gateway telemetry and detects failure signatures."""
    @staticmethod
    def inspect(payload: Dict[str, Any]) -> Dict[str, Any]:
        decline_code = payload.get("decline_code", "INSUFFICIENT_FUNDS")
        amount = float(payload.get("amount", 240.00))
        card_last4 = payload.get("card_last4", "4022")

        # Map ISO 8583 banking response
        iso_map = {
            "INSUFFICIENT_FUNDS": {"code": "51", "category": "LIQUIDITY_BREACH", "risk_level": "LOW"},
            "FRAUD_SUSPECTED": {"code": "59", "category": "FALSE_POSITIVE_HEURISTIC", "risk_level": "MEDIUM"},
            "CURRENCY_MISMATCH": {"code": "82", "category": "CROSS_BORDER_RESTRICTION", "risk_level": "LOW"},
            "LIMIT_EXCEEDED": {"code": "61", "category": "ISSUER_CARD_CEILING", "risk_level": "LOW"},
            "BANK_TIMEOUT": {"code": "91", "category": "INTERCHANGE_NETWORK_UNAVAILABLE", "risk_level": "NEUTRAL"}
        }
        meta = iso_map.get(decline_code, {"code": "05", "category": "GENERIC_DECLINE", "risk_level": "MEDIUM"})
        return {
            "iso_code": meta["code"],
            "decline_category": meta["category"],
            "risk_level": meta["risk_level"],
            "card_fingerprint": f"BIN_411124_L4_{card_last4}",
            "amount": amount,
            "detected_at": datetime.utcnow().isoformat()
        }

import numpy as np
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

class MLPropensityEngine:
    """
    ML Decision Engine:
    Loads pre-trained Scikit-Learn model trained on domain-documented decline heuristics.
    In production, this model is retrained continuously on real merchant settlement and
    dispute logs to optimize tender recovery conversion.
    """
    def __init__(self):
        self.classes = [
            "PAYPAL_PAY_LATER",
            "PAYPAL_VERIFIED_WALLET",
            "PAYPAL_DYNAMIC_FX",
            "PAYPAL_FASTLANE"
        ]
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            from train_model import train_and_export
            train_and_export()
            self.model = joblib.load(MODEL_PATH)

    def predict_propensities(self, amount: float, category: str, velocity: float = 0.2) -> List[Dict[str, Any]]:
        norm_amt = amount / 1000.0
        is_liq = 1.0 if category == "LIQUIDITY_BREACH" else 0.0
        is_fraud = 1.0 if category == "FALSE_POSITIVE_HEURISTIC" else 0.0
        is_fx = 1.0 if category == "CROSS_BORDER_RESTRICTION" else 0.0
        is_timeout = 1.0 if category == "INTERCHANGE_NETWORK_UNAVAILABLE" else 0.0

        sample = np.array([[norm_amt, is_liq, is_fraud, is_fx, is_timeout, velocity]])
        probs = self.model.predict_proba(sample)[0]

        results = []
        for idx, prob in enumerate(probs):
            results.append({
                "strategy": self.classes[idx],
                "propensity": round(float(prob), 4)
            })
        return sorted(results, key=lambda x: x["propensity"], reverse=True)

ML_SCORER = MLPropensityEngine()

class DiagnosticianAgent:
    """Agent 2: Propensity Scoring & Eligibility Verification."""
    @staticmethod
    def score_strategies(telemetry: Dict[str, Any]) -> List[Dict[str, Any]]:
        category = telemetry["decline_category"]
        amount = telemetry["amount"]
        ranked = ML_SCORER.predict_propensities(amount, category)

        # Eligibility verification: Pay in 4 is restricted to purchases between $30 and $1,500
        # If amount is outside bounds, fall back to Verified Wallet or Instant Checkout
        if ranked[0]["strategy"] == "PAYPAL_PAY_LATER" and not (30.0 <= amount <= 1500.0):
            # Demote Pay Later due to threshold ineligibility
            for item in ranked:
                if item["strategy"] == "PAYPAL_PAY_LATER":
                    item["propensity"] = 0.0
                    item["ineligible_reason"] = "Cart total outside PayPal Pay in 4 limit ($30 - $1,500)"
            ranked = sorted(ranked, key=lambda x: x["propensity"], reverse=True)

        return ranked

class HealerAgent:
    """Agent 3: Synthesizes the optimal recovery UI payload and PayPal v2 Order spec."""
    @staticmethod
    def construct_recovery_package(top_strategy: str, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        amount = telemetry["amount"]

        if top_strategy == "PAYPAL_PAY_LATER":
            installment = round(amount / 4.0, 2)
            return {
                "strategy": "PAYPAL_PAY_LATER",
                "headline": "Split this purchase into 4 payments with PayPal",
                "subheadline": "0% interest, no late fees. Short-term installment option (for eligible $30-$1,500 carts).",
                "explanation": f"Your bank declined the single lump-sum charge of ${amount:.2f}. If eligible, you can complete this order via 4 bi-weekly payments of ${installment:.2f} with zero interest.",
                "badge": "0% INTEREST • NO LATE FEES • ELIGIBLE ORDERS",
                "cta_text": f"Pay with PayPal: 4 payments of ${installment:.2f}",
                "installment_schedule": [
                    {"due": "Due today", "amount": installment, "status": "UPCOMING"},
                    {"due": "In 2 weeks", "amount": installment, "status": "SCHEDULED"},
                    {"due": "In 4 weeks", "amount": installment, "status": "SCHEDULED"},
                    {"due": "In 6 weeks", "amount": installment, "status": "SCHEDULED"}
                ],
                "paypal_component": "pay-later-button",
                "confidence": 0.96
            }
        elif top_strategy == "PAYPAL_VERIFIED_WALLET":
            return {
                "strategy": "PAYPAL_VERIFIED_WALLET",
                "headline": "Authenticate securely with your verified PayPal Wallet",
                "subheadline": "Avoid unguided card declines through independent 2FA / biometric authentication.",
                "explanation": "Your card issuer triggered a heuristic security decline. Checking out with your verified PayPal account uses independent authentication and may be covered under PayPal Seller Protection if criteria are met.",
                "badge": "BIOMETRIC / 2FA PROTECTED • SELLER PROTECTION ELIGIBLE",
                "cta_text": "Continue with 1-Click PayPal Wallet",
                "installment_schedule": [],
                "paypal_component": "wallet-button",
                "confidence": 0.94
            }
        elif top_strategy == "PAYPAL_DYNAMIC_FX":
            local_amt = round(amount * 84.50, 2)
            return {
                "strategy": "PAYPAL_DYNAMIC_FX",
                "headline": "Auto-convert foreign currency with PayPal Dynamic FX",
                "subheadline": "Direct cross-border clearance without international card blocks.",
                "explanation": f"Your issuer restricted the direct USD transaction. PayPal can settle this order directly in your local currency (approx. ₹{local_amt:,.2f}) at competitive exchange rates.",
                "badge": "REAL-TIME FX RATE LOCKED • 100+ CURRENCIES",
                "cta_text": "Settle via PayPal Local Currency",
                "installment_schedule": [],
                "paypal_component": "multi-currency-button",
                "confidence": 0.95
            }
        else: # PAYPAL_FASTLANE
            return {
                "strategy": "PAYPAL_FASTLANE",
                "headline": "Instant Guest Checkout with PayPal Fastlane",
                "subheadline": "Accelerated guest checkout when card interchange experiences latency.",
                "explanation": "Card interchange experienced network latency. Complete this checkout with 1 tap using your saved Fastlane profile.",
                "badge": "FASTLANE ACTIVATED • 1-TAP CHECKOUT",
                "cta_text": "Complete with Fastlane by PayPal",
                "installment_schedule": [],
                "paypal_component": "fastlane-button",
                "confidence": 0.92
            }


# ---------------------------------------------------------------------
# ROUTES & CONTROLLERS
# ---------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/checkout", methods=["POST"])
def process_checkout():
    """Simulates card submission & triggers multi-agent diagnostic orchestration."""
    data = request.json or {}
    decline_code = data.get("simulate_error", "INSUFFICIENT_FUNDS")
    amount = float(data.get("amount", 240.00))
    customer_name = data.get("customer_name", "Krish Punia")
    customer_email = data.get("customer_email", "krish@example.com")
    card_last4 = data.get("card_last4", "4022")
    tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
    start_time = time.perf_counter()

    # Step 1: Sentinel Agent analyzes failure
    telemetry = SentinelAgent.inspect({
        "decline_code": decline_code,
        "amount": amount,
        "card_last4": card_last4
    })

    # Step 2: Diagnostician Agent computes strategy propensities
    ranked_strategies = DiagnosticianAgent.score_strategies(telemetry)
    top_choice = ranked_strategies[0]["strategy"]

    # Step 3: Healer Agent creates recovery package
    recovery_pkg = HealerAgent.construct_recovery_package(top_choice, telemetry)

    elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

    # Log to SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO transactions (id, customer_name, customer_email, amount, currency, initial_status, decline_code, recovery_strategy, final_status, resolution_time_ms)
    VALUES (?, ?, ?, ?, 'USD', 'DECLINED', ?, ?, 'IN_RECOVERY', ?)
    """, (tx_id, customer_name, customer_email, amount, decline_code, top_choice, elapsed_ms))

    # Log Agent Reasoning Traces
    traces = [
        ("SentinelAgent", "INGEST_TELEMETRY", f"Detected ISO-8583 decline code {telemetry['iso_code']} ({telemetry['decline_category']}) on card ...{card_last4}. Risk Level: {telemetry['risk_level']}.", 0.98),
        ("DiagnosticianAgent", "PROPENSITY_EVALUATION", f"Evaluated 4 remediation vectors. Top choice {top_choice} with {ranked_strategies[0]['propensity']*100:.1f}% confidence score.", ranked_strategies[0]['propensity']),
        ("HealerAgent", "PACKAGE_SYNTHESIS", f"Constructed PayPal Complete Payments package for {top_choice}. Ready for user approval.", recovery_pkg['confidence'])
    ]
    for role, step, thought, conf in traces:
        cur.execute("""
        INSERT INTO agent_logs (transaction_id, agent_role, step_name, thought, confidence, execution_time_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (tx_id, role, step, thought, conf, elapsed_ms))
    conn.commit()
    conn.close()

    return jsonify({
        "transaction_id": tx_id,
        "status": "DECLINED",
        "telemetry": telemetry,
        "ranked_strategies": ranked_strategies,
        "recovery_package": recovery_pkg,
        "agent_traces": [
            {"role": t[0], "step": t[1], "thought": t[2], "confidence": t[3]}
            for t in traces
        ],
        "latency_ms": elapsed_ms
    }), 402

@app.route("/api/paypal/create-order", methods=["POST"])
def create_paypal_order():
    """Generates official PayPal Orders v2 payload."""
    data = request.json or {}
    tx_id = data.get("transaction_id", "UNKNOWN")
    amount = float(data.get("amount", 240.00))
    strategy = data.get("strategy", "PAYPAL_PAY_LATER")

    order_id = f"PP-ORD-{uuid.uuid4().hex[:10].upper()}"

    # PayPal v2 Order Object Structure
    order_payload = {
        "id": order_id,
        "status": "CREATED",
        "intent": "CAPTURE",
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "brand_name": "DevTools Studio (Protected by PayGuard AI)",
                    "locale": "en-US",
                    "landing_page": "GUEST_CHECKOUT",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW"
                }
            }
        },
        "purchase_units": [
            {
                "reference_id": tx_id,
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}",
                    "breakdown": {
                        "item_total": {"currency_code": "USD", "value": f"{amount:.2f}"}
                    }
                },
                "payee": {
                    "email_address": "merchant-pro@payguard.ai",
                    "merchant_id": "PAYGUARD_MERCHANT_V2"
                }
            }
        ],
        "create_time": datetime.utcnow().isoformat() + "Z"
    }

    return jsonify(order_payload)

@app.route("/api/paypal/capture-order", methods=["POST"])
def capture_paypal_order():
    """Simulates PayPal Order Capture and finalizes recovery in database."""
    data = request.json or {}
    order_id = data.get("order_id", "UNKNOWN")
    tx_id = data.get("transaction_id", "UNKNOWN")
    amount = float(data.get("amount", 240.00))

    capture_id = f"CAP-{uuid.uuid4().hex[:10].upper()}"
    now = datetime.utcnow().isoformat() + "Z"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    UPDATE transactions
    SET final_status = 'COMPLETED',
        paypal_order_id = ?,
        recovered_amount = ?,
        resolution_time_ms = ?
    WHERE id = ?
    """, (order_id, amount, random.randint(850, 1800), tx_id))
    conn.commit()
    conn.close()

    return jsonify({
        "capture_id": capture_id,
        "status": "COMPLETED",
        "order_id": order_id,
        "transaction_id": tx_id,
        "captured_amount": amount,
        "currency": "USD",
        "captured_at": now,
        "payment_method": "PAYPAL_COMPLETE_PAYMENTS",
        "message": "Payment captured cleanly! Cart successfully rescued."
    })

@app.route("/api/merchant/analytics", methods=["GET"])
def get_analytics():
    """Generates high-fidelity metrics, decline distributions, and recovery lift."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*), SUM(amount) FROM transactions")
    total_tx, total_attempted_gmv = cur.fetchone()
    total_tx = total_tx or 0
    total_attempted_gmv = total_attempted_gmv or 0.0

    cur.execute("SELECT COUNT(*), SUM(recovered_amount) FROM transactions WHERE final_status = 'COMPLETED'")
    recovered_tx, recovered_gmv = cur.fetchone()
    recovered_tx = recovered_tx or 0
    recovered_gmv = recovered_gmv or 0.0

    cur.execute("SELECT decline_code, COUNT(*) FROM transactions GROUP BY decline_code")
    decline_breakdown = dict(cur.fetchall())

    cur.execute("SELECT recovery_strategy, COUNT(*) FROM transactions WHERE final_status = 'COMPLETED' GROUP BY recovery_strategy")
    strategy_breakdown = dict(cur.fetchall())

    # Recent 10 transactions with traces
    cur.execute("""
    SELECT id, timestamp, customer_name, amount, decline_code, recovery_strategy, final_status, resolution_time_ms
    FROM transactions ORDER BY timestamp DESC LIMIT 10
    """)
    recent = []
    for r in cur.fetchall():
        recent.append({
            "id": r[0],
            "timestamp": r[1],
            "customer": r[2],
            "amount": r[3],
            "decline_code": r[4],
            "strategy": r[5],
            "status": r[6],
            "resolution_time_ms": r[7]
        })

    conn.close()

    recovery_rate = round((recovered_tx / max(total_tx, 1)) * 100, 1)

    return jsonify({
        "total_transactions": total_tx,
        "total_attempted_gmv": round(total_attempted_gmv, 2),
        "recovered_transactions": recovered_tx,
        "recovered_gmv": round(recovered_gmv, 2),
        "recovery_rate": recovery_rate,
        "decline_breakdown": decline_breakdown,
        "strategy_breakdown": strategy_breakdown,
        "recent_transactions": recent
    })

@app.route("/api/copilot/chat", methods=["POST"])
def copilot_chat():
    """NLP Contextual Assistant for Shoppers in Checkout."""
    data = request.json or {}
    msg = data.get("message", "").strip().lower()
    strategy = data.get("strategy", "PAYPAL_PAY_LATER")
    amount = float(data.get("amount", 240.00))

    if any(k in msg for k in ["fee", "interest", "cost", "charge", "apr"]):
        reply = (
            f"PayPal Pay in 4 is an interest-free installment option with 0% APR and no late fees. "
            f"For eligible orders from $30 to $1,500, shoppers make 4 bi-weekly payments of ${amount/4:.2f}."
        )
    elif any(k in msg for k in ["why", "decline", "reason", "fail", "rejected"]):
        reply = (
            f"Your card issuer issued a specific cardholder decline for this ${amount:.2f} transaction. "
            f"PayGuard AI provides a guided tender switch to PayPal Complete Payments so you can complete "
            f"your checkout with your preferred alternative tender without manual re-entry."
        )
    elif any(k in msg for k in ["safe", "protect", "secure", "trust", "guarantee"]):
        reply = (
            "All payment transactions are encrypted end-to-end. Eligible purchases are supported by "
            "PayPal Buyer Protection, and your raw bank credentials are never exposed to the merchant."
        )
    elif any(k in msg for k in ["bank", "debit", "card", "pay later"]):
        reply = (
            f"Inside the PayPal recovery modal, you can select any funding source: your linked bank account, "
            f"debit card, PayPal balance, or choose PayPal Pay Later for 4 easy bi-weekly splits."
        )
    else:
        reply = (
            f"I have activated your recovery path via {strategy.replace('_', ' ')}. Click the gold PayPal recovery "
            f"button to finalize your purchase in one click!"
        )

    return jsonify({
        "reply": reply,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"🚀 PayGuard AI Enterprise Platform running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
