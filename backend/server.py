"""
PayGuard AI - Autonomous Payment Recovery & Frictionless Checkout Engine
Powered by PayPal Complete Payments & Pay Later APIs.
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import time
from typing import Dict, Any

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# Mock in-memory recovery metrics
METRICS = {
    "total_checkouts": 142,
    "failed_checkouts": 38,
    "recovered_checkouts": 31,
    "recovered_revenue": 4820.00,
    "recovery_rate_percent": 81.5
}

# PayPal Recovery Rules & AI Strategy Engine
def analyze_payment_failure(error_code: str, amount: float, currency: str, shopper_email: str) -> Dict[str, Any]:
    """
    AI Decision Engine: Analyzes gateway decline codes and formulates
    the highest-probability PayPal recovery route.
    """
    if error_code in ["INSUFFICIENT_FUNDS", "LIMIT_EXCEEDED"]:
        # Recommend PayPal Pay in 4 (Installments)
        installment = round(amount / 4.0, 2)
        return {
            "recovery_strategy": "PAYPAL_PAY_LATER",
            "headline": "Split this into 4 interest-free payments with PayPal",
            "explanation": f"Your bank declined the single charge of ${amount:.2f} due to account limits. We've arranged 0% APR installment recovery.",
            "recommended_action": "PAY_IN_4",
            "installment_amount": installment,
            "installments_count": 4,
            "paypal_flow": "PAY_LATER",
            "cta_label": f"Pay with PayPal: 4 payments of ${installment:.2f}",
            "confidence_score": 0.94
        }
    elif error_code in ["FRAUD_SUSPECTED", "BANK_HOLD", "RISK_DECLINE"]:
        # Recommend PayPal Fastlane / Verified Wallet (circumvents false-positive card fraud algorithms)
        return {
            "recovery_strategy": "PAYPAL_VERIFIED_WALLET",
            "headline": "Pay safely via verified PayPal Wallet",
            "explanation": "Your card issuer flagged this transaction under automated security rules. Checking out with your verified PayPal account bypasses cardholder risk blocks.",
            "recommended_action": "PAYPAL_WALLET",
            "paypal_flow": "ONE_CLICK_WALLET",
            "cta_label": "Authorize securely via PayPal Wallet",
            "confidence_score": 0.91
        }
    elif error_code in ["CURRENCY_MISMATCH", "CROSS_BORDER_RESTRICTION"]:
        # Recommend PayPal Multi-Currency Conversion
        return {
            "recovery_strategy": "PAYPAL_MULTI_CURRENCY",
            "headline": "Auto-convert currency via PayPal FX",
            "explanation": f"Your local card does not support direct USD billing. PayPal can automatically convert this into your local currency.",
            "recommended_action": "PAYPAL_FX",
            "paypal_flow": "MULTI_CURRENCY",
            "cta_label": "Settle with PayPal in Local Currency",
            "confidence_score": 0.88
        }
    else:
        # Default smart PayPal checkout recovery
        return {
            "recovery_strategy": "PAYPAL_INSTANT_RECOVERY",
            "headline": "Recover checkout via PayPal",
            "explanation": "Card authorization was interrupted. You can complete your order instantly using PayPal balance, bank debit, or Pay Later.",
            "recommended_action": "PAYPAL_CHECKOUT",
            "paypal_flow": "STANDARD_PAYPAL",
            "cta_label": "Complete Order with PayPal",
            "confidence_score": 0.85
        }

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/checkout", methods=["POST"])
def process_checkout():
    """Simulates payment gateway authorization or failure."""
    data = request.json or {}
    simulate_error = data.get("simulate_error")
    amount = float(data.get("amount", 180.00))
    currency = data.get("currency", "USD")
    email = data.get("email", "customer@example.com")

    METRICS["total_checkouts"] += 1

    if simulate_error:
        METRICS["failed_checkouts"] += 1
        # Trigger PayGuard AI Recovery analysis
        recovery_plan = analyze_payment_failure(simulate_error, amount, currency, email)
        return jsonify({
            "status": "declined",
            "error_code": simulate_error,
            "error_message": f"Payment gateway rejected authorization: {simulate_error}",
            "payguard_recovery": recovery_plan
        }), 402

    return jsonify({
        "status": "success",
        "transaction_id": f"TX-{uuid.uuid4().hex[:10].upper()}",
        "amount": amount,
        "currency": currency,
        "message": "Payment captured successfully."
    })

@app.route("/api/paypal/create-recovery-order", methods=["POST"])
def create_paypal_recovery():
    """Generates a PayPal recovery order ID and token."""
    data = request.json or {}
    amount = float(data.get("amount", 180.00))
    strategy = data.get("strategy", "PAYPAL_PAY_LATER")

    order_id = f"PAYPAL-REC-{uuid.uuid4().hex[:8].upper()}"
    return jsonify({
        "status": "created",
        "paypal_order_id": order_id,
        "strategy": strategy,
        "amount": amount,
        "currency": "USD",
        "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
    })

@app.route("/api/paypal/capture-recovery-order", methods=["POST"])
def capture_paypal_recovery():
    """Captures the recovered transaction and updates analytics."""
    data = request.json or {}
    order_id = data.get("paypal_order_id", "UNKNOWN")
    amount = float(data.get("amount", 180.00))

    METRICS["recovered_checkouts"] += 1
    METRICS["recovered_revenue"] += amount
    METRICS["recovery_rate_percent"] = round(
        (METRICS["recovered_checkouts"] / max(METRICS["failed_checkouts"], 1)) * 100, 1
    )

    return jsonify({
        "status": "completed",
        "paypal_order_id": order_id,
        "capture_id": f"CAP-{uuid.uuid4().hex[:10].upper()}",
        "recovered_amount": amount,
        "message": "Transaction successfully rescued by PayGuard AI!",
        "metrics": METRICS
    })

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    return jsonify(METRICS)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 PayGuard AI Backend running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
