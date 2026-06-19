import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Try to use XGBoost as primary (PRD recommendation), fallback to RandomForest
try:
    from xgboost import XGBClassifier
    MODEL_TYPE = "XGBoost"
    print("XGBoost available - using XGBoost classifier (PRD recommended).")
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    MODEL_TYPE = "RandomForest"
    print("XGBoost not installed - using RandomForest classifier fallback.")

# Paths
MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.pkl")

# Features list used for the model
FEATURE_COLS = [
    "amount_ratio",        # transaction_amount / avg_transaction_amount
    "hour_of_day",         # transaction hour (0-23)
    "location_distance",   # numerical distance (e.g. km from usual)
    "device_changed",      # 1 if different from usual, 0 otherwise
    "vpn_usage",           # 1 if VPN used, 0 otherwise
    "velocity",            # transaction count in short window (1-10)
    "previous_fraud"       # 1 if user has history of fraud, 0 otherwise
]

def generate_synthetic_data(num_records=10000):
    """
    Generates synthetic transaction data that exhibits realistic fraud patterns.
    """
    np.random.seed(42)
    
    # 1. Generate core raw user and transaction profiles
    user_ids = [f"USR-{i:03d}" for i in range(1, 101)]
    user_avg_amounts = np.random.exponential(scale=15000, size=100) + 1000  # avg spending N1000 to N100k
    user_ages = np.random.randint(30, 1000, size=100)
    user_prev_fraud = np.random.choice([0, 1], size=100, p=[0.95, 0.05])
    
    users_df = pd.DataFrame({
        "user_id": user_ids,
        "avg_amount": user_avg_amounts,
        "account_age": user_ages,
        "previous_fraud": user_prev_fraud
    })
    
    # Generate transactions
    tx_users = np.random.choice(user_ids, size=num_records)
    tx_df = pd.DataFrame({"user_id": tx_users})
    tx_df = tx_df.merge(users_df, on="user_id")
    
    # Create transaction-level details
    tx_df["amount"] = tx_df.apply(lambda r: np.random.exponential(scale=r["avg_amount"]), axis=1)
    tx_df["hour_of_day"] = np.random.randint(0, 24, size=num_records)
    tx_df["location_distance"] = np.random.exponential(scale=20, size=num_records)
    tx_df["device_changed"] = np.random.choice([0, 1], size=num_records, p=[0.92, 0.08])
    tx_df["vpn_usage"] = np.random.choice([0, 1], size=num_records, p=[0.90, 0.10])
    tx_df["velocity"] = np.random.poisson(lam=1.2, size=num_records) + 1
    
    # Feature Engineering
    tx_df["amount_ratio"] = tx_df["amount"] / tx_df["avg_amount"]
    
    # Inject fraud rules to assign ground truth fraud_label
    # Base fraud probability
    fraud_prob = np.zeros(num_records)
    
    # Rules
    # 1. High Amount Rule
    fraud_prob += np.where(tx_df["amount_ratio"] > 15, 0.40, 0.0)
    fraud_prob += np.where(tx_df["amount_ratio"] > 50, 0.45, 0.0)
    
    # 2. Unusual Location
    fraud_prob += np.where(tx_df["location_distance"] > 300, 0.35, 0.0)
    
    # 3. Unusual Time + Device Change
    night_time = tx_df["hour_of_day"].isin([1, 2, 3, 4, 5])
    fraud_prob += np.where(night_time & (tx_df["device_changed"] == 1), 0.40, 0.0)
    
    # 4. VPN + Device Change
    fraud_prob += np.where((tx_df["vpn_usage"] == 1) & (tx_df["device_changed"] == 1), 0.35, 0.0)
    
    # 5. Velocity
    fraud_prob += np.where(tx_df["velocity"] > 4, 0.45, 0.0)
    
    # 6. Previous Fraud
    fraud_prob += np.where(tx_df["previous_fraud"] == 1, 0.15, 0.0)
    
    # Clip and threshold to make labels
    fraud_prob = np.clip(fraud_prob + 0.005, 0.0, 0.99)
    tx_df["fraud_label"] = np.random.binomial(1, fraud_prob)
    
    return tx_df

def init_model(retrain=False):
    """
    Trains the XGBoost/RandomForest model on synthetic data and saves weights.
    """
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and not retrain:
        return load_model()
        
    df = generate_synthetic_data()
    
    X = df[FEATURE_COLS]
    y = df["fraud_label"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # We train XGBoost (PRD recommended) or fallback to RandomForest if xgboost not installed.
    if MODEL_TYPE == "XGBoost":
        model = XGBClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1, eval_metric="logloss")
    else:
        model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    
    # Metrics
    metrics = {
        "model_type": MODEL_TYPE,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "feature_importances": {col: float(imp) for col, imp in zip(FEATURE_COLS, model.feature_importances_)}
    }
    
    # Save files
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
        
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
        
    with open(METRICS_PATH, "wb") as f:
        pickle.dump(metrics, f)
        
    return model, scaler, metrics

def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return init_model(retrain=True)
        
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    with open(METRICS_PATH, "rb") as f:
        metrics = pickle.load(f)
        
    return model, scaler, metrics

def predict_transaction(tx_data):
    """
    Predicts fraud risk for a transaction.
    tx_data should contain:
      - amount (float)
      - user_avg_amount (float)
      - hour_of_day (int)
      - location_distance (float)
      - device_changed (int, 0 or 1)
      - vpn_usage (int, 0 or 1)
      - velocity (int)
      - previous_fraud (int, 0 or 1)
    """
    model, scaler, metrics = load_model()
    
    # Feature Engineering
    amount_ratio = float(tx_data["amount"]) / max(float(tx_data["user_avg_amount"]), 1.0)
    
    features = pd.DataFrame([{
        "amount_ratio": amount_ratio,
        "hour_of_day": int(tx_data["hour_of_day"]),
        "location_distance": float(tx_data["location_distance"]),
        "device_changed": int(tx_data["device_changed"]),
        "vpn_usage": int(tx_data["vpn_usage"]),
        "velocity": int(tx_data["velocity"]),
        "previous_fraud": int(tx_data["previous_fraud"])
    }])[FEATURE_COLS]
    
    features_scaled = scaler.transform(features)
    
    # Predict probabilities
    prob = model.predict_proba(features_scaled)[0][1]
    prediction = int(model.predict(features_scaled)[0])
    
    # Compute score out of 100 - cast to native Python float to avoid numpy float32 serialization issues
    risk_score = float(round(float(prob) * 100, 1))
    
    # Determine Action Based on score
    # 0 - 30: Approve
    # 31 - 60: Monitor
    # 61 - 80: Hold for Review (Pending)
    # 81 - 100: Block
    if risk_score <= 30:
        action = "APPROVED"
    elif risk_score <= 60:
        action = "MONITOR"
    elif risk_score <= 80:
        action = "PENDING"
    else:
        action = "BLOCKED"
        
    # Explainability / Risk Indicators Breakdown (based on simple heuristic of contributors)
    indicators = []
    if amount_ratio > 10:
        indicators.append({"feature": "Amount Risk", "score": int(min(100, amount_ratio * 4)), "desc": f"Transaction amount is {amount_ratio:.1f}x higher than user average."})
    if float(tx_data["location_distance"]) > 100:
        indicators.append({"feature": "Location Shift", "score": int(min(100, float(tx_data["location_distance"]) / 10)), "desc": f"Transaction initiated {tx_data['location_distance']} km from usual locations."})
    if int(tx_data["hour_of_day"]) in [1, 2, 3, 4, 5]:
        indicators.append({"feature": "Time Risk", "score": 75, "desc": f"Executed at unusual time ({tx_data['hour_of_day']}:00 AM)."})
    if int(tx_data["device_changed"]) == 1:
        indicators.append({"feature": "Device Change", "score": 80, "desc": "Unknown device identifier used for transaction."})
    if int(tx_data["vpn_usage"]) == 1:
        indicators.append({"feature": "VPN Active", "score": 60, "desc": "Anonymized network connection detected."})
    if int(tx_data["velocity"]) > 3:
        indicators.append({"feature": "Velocity Velocity", "score": int(min(100, int(tx_data["velocity"]) * 20)), "desc": f"High frequency attempts ({tx_data['velocity']} requests in last 5m)."})
        
    # Sort indicators by score descending
    indicators = sorted(indicators, key=lambda x: x["score"], reverse=True)
    
    # Ensure there's at least one breakdown indicator if score > 30
    if not indicators and risk_score > 30:
        indicators.append({"feature": "Combined Features", "score": int(risk_score), "desc": "Aggregated patterns of device, location and timing flags."})
        
    # Ensure all values are native Python types for JSON serialization
    return {
        "risk_score": float(risk_score),
        "prediction": int(prediction),
        "action": str(action),
        "indicators": [
            {
                "feature": str(ind["feature"]),
                "score": int(ind["score"]),
                "desc": str(ind["desc"])
            }
            for ind in indicators
        ]
    }

if __name__ == "__main__":
    print("Training initial ML Model...")
    model, scaler, metrics = init_model(retrain=True)
    print("Initial metrics:")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1']:.4f}")
