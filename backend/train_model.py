"""
PayGuard AI - Model Training Pipeline
Heuristic-to-ML Transition Engine

Note on Methodology:
In development/hackathon environments without access to proprietary merchant
loss/decline logs, training labels are generated from domain-documented payment
heuristics. This script trains a Scikit-Learn Logistic Regression model on this
synthetic dataset to prove the pipeline architecture.

In production, this module would be retrained on real merchant checkout outcome
logs (conversion rates, dispute rates, and customer acceptance per tender).
"""

import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

CLASSES = [
    "PAYPAL_PAY_LATER",
    "PAYPAL_VERIFIED_WALLET",
    "PAYPAL_DYNAMIC_FX",
    "PAYPAL_FASTLANE"
]

def generate_heuristic_dataset(num_samples=500):
    """
    Generates synthetic feature vectors based on payment gateway decline heuristics.
    Features:
      0: Normalized Transaction Amount (amount / 1000.0)
      1: Is Liquidity Breach (Code 51 / NSF)
      2: Is Fraud Suspected (Code 59 / Heuristic Risk)
      3: Is Cross Border (Code 82 / Currency Mismatch)
      4: Is Network Latency (Code 91 / Interchange Timeout)
      5: Simulated Session Velocity (attempts per session)
    """
    np.random.seed(42)
    X, y = [], []

    # 1. Liquidity breach (insufficient funds on $30-$1500 purchases) -> Pay Later
    for _ in range(num_samples // 4):
        amt = np.random.uniform(30, 800) / 1000.0
        velocity = np.random.uniform(0.1, 0.4)
        X.append([amt, 1.0, 0.0, 0.0, 0.0, velocity])
        y.append(0)

    # 2. Heuristic fraud flags (medium-high amounts, rapid attempts) -> Verified Wallet
    for _ in range(num_samples // 4):
        amt = np.random.uniform(80, 600) / 1000.0
        velocity = np.random.uniform(0.6, 1.0)
        X.append([amt, 0.0, 1.0, 0.0, 0.0, velocity])
        y.append(1)

    # 3. Currency / Cross-border mismatch -> Dynamic FX
    for _ in range(num_samples // 4):
        amt = np.random.uniform(40, 450) / 1000.0
        velocity = np.random.uniform(0.1, 0.3)
        X.append([amt, 0.0, 0.0, 1.0, 0.0, velocity])
        y.append(2)

    # 4. Interchange network lag / timeout -> Fastlane accelerated checkout
    for _ in range(num_samples // 4):
        amt = np.random.uniform(20, 200) / 1000.0
        velocity = np.random.uniform(0.0, 0.2)
        X.append([amt, 0.0, 0.0, 0.0, 1.0, velocity])
        y.append(3)

    return np.array(X), np.array(y)

def train_and_export():
    print("Generating heuristic training dataset...")
    X, y = generate_heuristic_dataset(600)

    print("Training LogisticRegression classifier...")
    model = LogisticRegression(max_iter=300, random_state=42)
    model.fit(X, y)

    y_pred = model.predict(X)
    print("\n--- Training Set Evaluation ---")
    print(classification_report(y, y_pred, target_names=CLASSES))

    model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
    joblib.dump(model, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    train_and_export()
