import os
import uuid
import datetime
import functools
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import database
import ml_engine

app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24).hex()

# Auth decorators
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        roles = session.get("roles", [])
        if "admin" not in roles:
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

def require_role(*required_roles):
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            user_roles = session.get("roles", [])
            if not any(r in user_roles for r in required_roles):
                return jsonify({"success": False, "error": f"Access restricted to: {', '.join(required_roles)}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# Initialize database and model on start
with app.app_context():
    print("Initializing Database...")
    database.init_db()
    print("Initializing ML Model...")
    try:
        ml_engine.init_model()
        print("ML Model loaded successfully.")
    except Exception as e:
        print(f"Error initializing model: {e}. Re-training model...")
        ml_engine.init_model(retrain=True)

@app.route("/")
@login_required
def index():
    return render_template("index.html", user=session.get("user"), roles=session.get("roles", []))

# ==================== AUTHENTICATION ====================

@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    try:
        data = request.json
        username = data.get("username", "")
        password = data.get("password", "")
        user = database.authenticate_user(username, password)
        if user:
            role_names = [r["role_name"] for r in user.get("roles", [])]
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["user"] = user["full_name"]
            session["roles"] = role_names
            return jsonify({
                "success": True,
                "user": {
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "roles": role_names
                }
            })
        return jsonify({"success": False, "error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/auth/session", methods=["GET"])
def api_session():
    if "user_id" in session:
        return jsonify({
            "success": True,
            "user": {
                "username": session.get("username"),
                "full_name": session.get("user"),
                "roles": session.get("roles", [])
            }
        })
    return jsonify({"success": False, "error": "Not authenticated"}), 401

# ==================== PASSWORD RESET ====================

@app.route("/api/auth/change-password", methods=["POST"])
@login_required
def api_change_password():
    try:
        data = request.json
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        if len(new_password) < 6:
            return jsonify({"success": False, "error": "New password must be at least 6 characters"}), 400
        result = database.change_password(session["user_id"], current_password, new_password)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== PROFILE ====================

@app.route("/api/auth/profile", methods=["GET"])
@login_required
def api_get_profile():
    try:
        profile = database.get_user_profile(session["user_id"])
        if profile:
            # Calculate password change eligibility
            remaining_days = 0
            if profile.get("last_password_change"):
                last = datetime.datetime.fromisoformat(profile["last_password_change"])
                days_since = (datetime.datetime.now() - last).days
                remaining_days = max(0, 14 - days_since)
            profile["password_change_remaining_days"] = remaining_days
            return jsonify({"success": True, "profile": profile})
        return jsonify({"success": False, "error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auth/profile", methods=["PUT"])
@login_required
def api_update_profile():
    try:
        data = request.json
        bio = data.get("bio")
        profile_picture = data.get("profile_picture")
        database.update_profile(session["user_id"], bio=bio, profile_picture=profile_picture)
        return jsonify({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== USER MANAGEMENT (Admin only) ====================

@app.route("/api/app-users", methods=["GET"])
@admin_required
def api_get_app_users():
    try:
        users = database.get_all_app_users()
        return jsonify({"success": True, "users": users})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/app-users", methods=["POST"])
@admin_required
def api_create_app_user():
    try:
        data = request.json
        user_id = database.create_app_user(
            username=data.get("username"),
            password=data.get("password"),
            full_name=data.get("full_name"),
            email=data.get("email"),
            role_ids=data.get("role_ids", [])
        )
        if user_id:
            return jsonify({"success": True, "user_id": user_id})
        return jsonify({"success": False, "error": "Username already exists"}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/app-users/<int:user_id>", methods=["PUT"])
@admin_required
def api_update_app_user(user_id):
    try:
        data = request.json
        database.update_app_user(
            user_id=user_id,
            full_name=data.get("full_name"),
            email=data.get("email"),
            role_ids=data.get("role_ids"),
            is_active=data.get("is_active")
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/app-users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_delete_app_user(user_id):
    try:
        database.delete_app_user(user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/roles", methods=["GET"])
@login_required
def api_get_roles():
    try:
        roles = database.get_all_roles()
        return jsonify({"success": True, "roles": roles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: KPIs
@app.route("/api/kpis", methods=["GET"])
@login_required
def get_kpis():
    try:
        kpi_data = database.get_kpis()
        return jsonify({"success": True, "kpis": kpi_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Trends
@app.route("/api/trends", methods=["GET"])
@login_required
def get_trends():
    try:
        trends_data = database.get_trends()
        return jsonify({"success": True, "trends": trends_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Risk Distribution
@app.route("/api/risk-distribution", methods=["GET"])
@login_required
def get_risk_distribution():
    try:
        dist_data = database.get_risk_distribution()
        return jsonify({"success": True, "distribution": dist_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Top Regions
@app.route("/api/top-regions", methods=["GET"])
@login_required
def get_top_regions():
    try:
        regions = database.get_top_regions()
        return jsonify({"success": True, "regions": regions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Recent Alerts
@app.route("/api/recent-alerts", methods=["GET"])
@login_required
def get_recent_alerts():
    try:
        alerts = database.get_recent_alerts()
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Transactions list with filters
@app.route("/api/transactions", methods=["GET"])
@login_required
def get_transactions():
    try:
        filters = {
            "search": request.args.get("search", ""),
            "risk_tier": request.args.get("risk_tier", ""),
            "status": request.args.get("status", "")
        }
        txs = database.get_all_transactions(filters)
        return jsonify({"success": True, "transactions": txs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Alerts for Analyst Desk
@app.route("/api/alerts", methods=["GET"])
@login_required
def get_alerts():
    try:
        alerts = database.get_all_alerts()
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Update Alert Status
@app.route("/api/alerts/update", methods=["POST"])
@login_required
def update_alert():
    try:
        data = request.json
        alert_id = data.get("alert_id")
        status = data.get("status")
        comment = data.get("comment", "")
        
        if not alert_id or not status:
            return jsonify({"success": False, "error": "Missing alert_id or status"}), 400
            
        success = database.update_alert_status(alert_id, status, comment)
        if success:
            return jsonify({"success": True, "message": "Alert status updated successfully"})
        else:
            return jsonify({"success": False, "error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Retrieve registered customers
@app.route("/api/users", methods=["GET"])
@login_required
def get_users():
    try:
        users = database.get_users()
        return jsonify({"success": True, "users": users})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Simulate a new transaction
@app.route("/api/simulate", methods=["POST"])
@login_required
def simulate_transaction():
    try:
        data = request.json
        user_id = data.get("user_id")
        amount = float(data.get("amount", 0.0))
        location = data.get("location", "Lagos")
        transaction_type = data.get("transaction_type", "Transfer")
        destination_account = data.get("destination_account", "")
        source_account = data.get("source_account", "")
        vpn_usage = int(data.get("vpn_usage", 0))
        device_changed = int(data.get("device_changed", 0))
        velocity = int(data.get("velocity", 1))
        hour_of_day = int(data.get("hour_of_day", datetime.datetime.now().hour))
        location_distance = float(data.get("location_distance", 0.0))
        
        # Load user history properties to feed features
        users = database.get_users()
        selected_user = next((u for u in users if u["user_id"] == user_id), None)
        
        if not selected_user:
            return jsonify({"success": False, "error": "User profile not found"}), 404
            
        user_avg_amount = selected_user["avg_transaction_amount"]
        previous_fraud = selected_user["previous_fraud_history"]
        
        # Call machine learning prediction
        pred_input = {
            "amount": amount,
            "user_avg_amount": user_avg_amount,
            "hour_of_day": hour_of_day,
            "location_distance": location_distance,
            "device_changed": device_changed,
            "vpn_usage": vpn_usage,
            "velocity": velocity,
            "previous_fraud": previous_fraud
        }
        
        pred_res = ml_engine.predict_transaction(pred_input)
        
        # Prepare transaction record to save in db
        tx_id = f"#TXN-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now()
        
        tx_record = {
            "transaction_id": tx_id,
            "user_id": user_id,
            "amount": amount,
            "location": location,
            "transaction_type": transaction_type,
            "destination_account": destination_account,
            "source_account": source_account,
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "device_id": "DEV-" + uuid.uuid4().hex[:8].upper() if device_changed else "DEV-SamsungS21",
            "device_type": "iPhone" if device_changed else "Android",
            "browser_type": "Safari" if device_changed else "Chrome",
            "operating_system": "iOS" if device_changed else "Android",
            "ip_address": "41.210.88.9" if vpn_usage else "197.210.8.21",
            "vpn_usage": vpn_usage,
            "risk_score": pred_res["risk_score"],
            "fraud_prediction": pred_res["prediction"],
            "status": pred_res["action"]
        }
        
        # Save to DB (triggers alert creation inside database if critical/predicted)
        database.create_simulated_transaction(tx_record)
        
        return jsonify({
            "success": True,
            "transaction_id": tx_id,
            "prediction": pred_res["prediction"],
            "risk_score": pred_res["risk_score"],
            "action": pred_res["action"],
            "indicators": pred_res["indicators"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Model Metrics
@app.route("/api/model/metrics", methods=["GET"])
@login_required
def get_model_metrics():
    try:
        model, scaler, metrics = ml_engine.load_model()
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Model Retraining logs
@app.route("/api/model/logs", methods=["GET"])
@login_required
def get_model_logs():
    try:
        logs = database.get_model_logs()
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Trigger Model Retraining
@app.route("/api/model/retrain", methods=["POST"])
@login_required
def retrain_model():
    try:
        print("Model retraining triggered...")
        # Train new model instance and calculate metrics
        model, scaler, metrics = ml_engine.init_model(retrain=True)
        
        # Log to Database
        version = f"v1.{len(database.get_model_logs()) + 1}"
        database.add_model_log(
            version=version,
            model_type=metrics.get("model_type", "RandomForest"),
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1"]
        )
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "version": version,
            "message": "Model retrained successfully and metrics logged."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
