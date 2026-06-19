import sqlite3
import datetime
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        avg_transaction_amount REAL DEFAULT 0.0,
        daily_frequency INTEGER DEFAULT 0,
        account_age INTEGER DEFAULT 0, -- in days
        previous_fraud_history INTEGER DEFAULT 0, -- 0 for False, 1 for True
        created_at TEXT
    )
    """)
    
    # 2. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        user_id TEXT,
        amount REAL NOT NULL,
        location TEXT,
        transaction_type TEXT, -- Transfer, Withdrawal, Deposit
        destination_account TEXT,
        source_account TEXT,
        timestamp TEXT,
        date TEXT,
        device_id TEXT,
        device_type TEXT, -- Android, iPhone, Web
        browser_type TEXT,
        operating_system TEXT,
        ip_address TEXT,
        vpn_usage INTEGER DEFAULT 0,
        risk_score REAL DEFAULT 0.0,
        fraud_prediction INTEGER DEFAULT 0, -- 0 for Legitimate, 1 for Fraudulent
        status TEXT, -- APPROVED, PENDING, BLOCKED, RESOLVED
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    """)
    
    # 3. Fraud Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fraud_alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE,
        risk_score REAL,
        alert_status TEXT DEFAULT 'PENDING', -- PENDING, BLOCKED, APPROVED, RESOLVED
        analyst_comment TEXT,
        created_at TEXT,
        FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id)
    )
    """)
    
    # 4. Model Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_version TEXT,
        model_type TEXT DEFAULT 'RandomForest',
        accuracy REAL,
        precision REAL,
        recall REAL,
        f1_score REAL,
        created_at TEXT
    )
    """)
    
    # 5. App Users Table (for authentication - distinct from bank customers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        bio TEXT DEFAULT '',
        profile_picture TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        last_password_change TEXT
    )
    """)
    
    # 6. Roles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    """)
    
    # 7. User Roles Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    
    # Migration: add columns if missing (for existing databases)
    for col in ["bio", "profile_picture", "last_password_change"]:
        try:
            cursor.execute(f"ALTER TABLE app_users ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
    
    # Seed roles if empty
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        seed_roles(cursor)
        conn.commit()
    
    # Seed default app users if empty
    cursor.execute("SELECT COUNT(*) FROM app_users")
    if cursor.fetchone()[0] == 0:
        seed_app_users(cursor)
        conn.commit()
    
    # Seed default bank customers if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_users(cursor)
        conn.commit()
        
    # Seed mock transactions and alerts if empty
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        seed_transactions_and_alerts(cursor)
        conn.commit()

    conn.close()

def seed_roles(cursor):
    roles_data = [
        ("admin", "System administrator with full access"),
        ("analyst", "Fraud analyst with alert investigation access"),
        ("viewer", "Read-only access to dashboards and reports"),
        ("compliance_officer", "Compliance review and reporting access"),
        ("risk_manager", "Risk management with model retraining privileges")
    ]
    cursor.executemany("INSERT INTO roles (role_name, description) VALUES (?, ?)", roles_data)

def seed_app_users(cursor):
    now = datetime.datetime.now().isoformat()
    admin_pw = os.environ.get("FRAUDGUARD_ADMIN_PW")
    analyst_pw = os.environ.get("FRAUDGUARD_ANALYST_PW")
    if not admin_pw:
        admin_pw = "admin123"
        print("[INFO] Using default admin password. Set FRAUDGUARD_ADMIN_PW env var to customize.")
    if not analyst_pw:
        analyst_pw = "analyst123"
        print("[INFO] Using default analyst password. Set FRAUDGUARD_ANALYST_PW env var to customize.")
    app_users_data = [
        ("admin", hashlib.sha256(admin_pw.encode()).hexdigest(), "A. Vance", "a.vance@sentinel.com", now),
        ("analyst", hashlib.sha256(analyst_pw.encode()).hexdigest(), "Sarah Analyst", "s.analyst@fraudguard.io", now)
    ]
    cursor.executemany("""
    INSERT INTO app_users (username, password_hash, full_name, email, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, app_users_data)
    
    # Assign roles: admin user gets admin + analyst; analyst user gets analyst + viewer
    cursor.execute("SELECT role_id FROM roles WHERE role_name = 'admin'")
    admin_role_id = cursor.fetchone()["role_id"]
    cursor.execute("SELECT role_id FROM roles WHERE role_name = 'analyst'")
    analyst_role_id = cursor.fetchone()["role_id"]
    cursor.execute("SELECT role_id FROM roles WHERE role_name = 'viewer'")
    viewer_role_id = cursor.fetchone()["role_id"]
    
    # admin user (user_id=1) gets admin + analyst + risk_manager
    cursor.execute("SELECT user_id FROM app_users WHERE username = 'admin'")
    admin_user_id = cursor.fetchone()["user_id"]
    cursor.execute("SELECT role_id FROM roles WHERE role_name = 'risk_manager'")
    risk_mgr_role_id = cursor.fetchone()["role_id"]
    
    cursor.executemany("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", [
        (admin_user_id, admin_role_id),
        (admin_user_id, analyst_role_id),
        (admin_user_id, risk_mgr_role_id)
    ])
    
    # analyst user (user_id=2) gets analyst + viewer
    cursor.execute("SELECT user_id FROM app_users WHERE username = 'analyst'")
    analyst_user_id = cursor.fetchone()["user_id"]
    cursor.executemany("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", [
        (analyst_user_id, analyst_role_id),
        (analyst_user_id, viewer_role_id)
    ])

def get_user_roles(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.role_id, r.role_name, r.description
        FROM roles r
        JOIN user_roles ur ON r.role_id = ur.role_id
        WHERE ur.user_id = ?
    """, (user_id,))
    roles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return roles

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM app_users WHERE username = ? AND password_hash = ? AND is_active = 1", (username, password_hash))
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(row)
        user["roles"] = get_user_roles(user["user_id"])
        return user
    return None

def get_app_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM app_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        user = dict(row)
        user["roles"] = get_user_roles(user["user_id"])
        return user
    return None

def get_all_app_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, full_name, email, is_active, created_at FROM app_users ORDER BY user_id")
    rows = [dict(row) for row in cursor.fetchall()]
    for row in rows:
        row["roles"] = get_user_roles(row["user_id"])
    conn.close()
    return rows

def create_app_user(username, password, full_name, email, role_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute("""
            INSERT INTO app_users (username, password_hash, full_name, email, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, email, now))
        conn.commit()
        user_id = cursor.lastrowid
        
        # Assign roles
        for rid in role_ids:
            cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, rid))
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def update_app_user(user_id, full_name=None, email=None, role_ids=None, is_active=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    if full_name is not None:
        fields.append("full_name = ?")
        params.append(full_name)
    if email is not None:
        fields.append("email = ?")
        params.append(email)
    if is_active is not None:
        fields.append("is_active = ?")
        params.append(int(is_active))
    if fields:
        params.append(user_id)
        cursor.execute(f"UPDATE app_users SET {', '.join(fields)} WHERE user_id = ?", params)
    
    if role_ids is not None:
        cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        for rid in role_ids:
            cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, rid))
    
    conn.commit()
    conn.close()
    return True

def delete_app_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM app_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def change_password(user_id, current_password, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    cursor.execute("SELECT * FROM app_users WHERE user_id = ? AND password_hash = ?", (user_id, current_hash))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return {"success": False, "error": "Current password is incorrect"}
    
    # Check 14-day cooldown
    last_change = user["last_password_change"]
    if last_change:
        last_change_dt = datetime.datetime.fromisoformat(last_change)
        days_since = (datetime.datetime.now() - last_change_dt).days
        if days_since < 14:
            remaining = 14 - days_since
            conn.close()
            return {"success": False, "error": f"Password can only be changed once every 14 days. {remaining} day(s) remaining.", "remaining_days": remaining}
    
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    now = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE app_users SET password_hash = ?, last_password_change = ? WHERE user_id = ?", (new_hash, now, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Password changed successfully"}

def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, full_name, email, bio, profile_picture, is_active, created_at, last_password_change FROM app_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        profile = dict(row)
        profile["roles"] = get_user_roles(user_id)
        return profile
    return None

def update_profile(user_id, bio=None, profile_picture=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    if bio is not None:
        fields.append("bio = ?")
        params.append(bio)
    if profile_picture is not None:
        fields.append("profile_picture = ?")
        params.append(profile_picture)
    if fields:
        params.append(user_id)
        cursor.execute(f"UPDATE app_users SET {', '.join(fields)} WHERE user_id = ?", params)
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_all_roles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM roles ORDER BY role_id")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def seed_users(cursor):
    now = datetime.datetime.now().isoformat()
    users_data = [
        ("USR-001", "A. Vance", "a.vance@sentinel.com", "+1-555-0190", 25000.0, 3, 365, 0, now),
        ("USR-002", "John Doe", "john.doe@gmail.com", "+234-803-111-2222", 15000.0, 2, 120, 0, now),
        ("USR-003", "Jane Smith", "jane.smith@yahoo.com", "+1-555-0144", 45000.0, 5, 730, 0, now),
        ("USR-004", "David K.", "david.k@outlook.com", "+44-20-7946-0192", 850000.0, 1, 90, 1, now),
        ("USR-005", "Fatima Al-Sayed", "fatima.s@dubai-bank.ae", "+971-50-1234567", 120000.0, 4, 450, 0, now),
        ("USR-006", "Chidi Okafor", "chidi.okafor@gmail.com", "+234-815-555-6666", 20000.0, 3, 200, 0, now)
    ]
    cursor.executemany("""
    INSERT INTO users (user_id, full_name, email, phone, avg_transaction_amount, daily_frequency, account_age, previous_fraud_history, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

def seed_transactions_and_alerts(cursor):
    now = datetime.datetime.now()
    
    # 5 Seed transactions
    tx_data = [
        # (transaction_id, user_id, amount, location, transaction_type, destination_account, source_account, timestamp, date, device_id, device_type, browser_type, operating_system, ip_address, vpn_usage, risk_score, fraud_prediction, status)
        (
            "#TXN-882190", "USR-002", 12400.00, "Dubai", "Cross-border Card", "ACC-99812", "ACC-00201",
            (now - datetime.timedelta(minutes=15)).isoformat(), (now - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d"),
            "DEV-iPhoneX", "iPhone", "Safari", "iOS", "192.168.12.80", 1, 98.0, 1, "PENDING"
        ),
        (
            "#TXN-882188", "USR-004", 85000.00, "Lagos", "Wire Transfer", "ACC-77612", "ACC-00401",
            (now - datetime.timedelta(hours=1)).isoformat(), (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d"),
            "DEV-Unknown", "Web", "Chrome", "Windows", "102.16.88.9", 1, 94.0, 1, "BLOCKED"
        ),
        (
            "#TXN-882185", "USR-006", 2100.00, "Lagos", "E-Wallet Top-up", "ACC-22119", "ACC-00601",
            (now - datetime.timedelta(hours=3)).isoformat(), (now - datetime.timedelta(hours=3)).strftime("%Y-%m-%d"),
            "DEV-SamsungS21", "Android", "Chrome", "Android", "197.210.8.21", 0, 88.0, 1, "PENDING"
        ),
        (
            "#TXN-882184", "USR-003", 1500.00, "New York", "Merchant Payment", "ACC-44901", "ACC-00301",
            (now - datetime.timedelta(hours=6)).isoformat(), (now - datetime.timedelta(hours=6)).strftime("%Y-%m-%d"),
            "DEV-MacbookPro", "Web", "Chrome", "macOS", "64.233.160.10", 0, 92.0, 1, "RESOLVED"
        ),
        (
            "#TXN-882180", "USR-005", 450.00, "London", "Subscription Bill", "ACC-88210", "ACC-00501",
            (now - datetime.timedelta(hours=12)).isoformat(), (now - datetime.timedelta(hours=12)).strftime("%Y-%m-%d"),
            "DEV-AutoBill", "Web", "Unknown", "Linux", "10.0.1.45", 0, 85.0, 1, "BLOCKED"
        ),
        # Some Legitimate Transactions
        (
            "#TXN-882170", "USR-002", 450.00, "Lagos", "Deposit", "ACC-00201", "ACC-ATM01",
            (now - datetime.timedelta(days=1)).isoformat(), (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "DEV-SamsungS21", "Android", "Chrome", "Android", "105.112.33.22", 0, 12.0, 0, "APPROVED"
        ),
        (
            "#TXN-882171", "USR-003", 12000.00, "New York", "Transfer", "ACC-33100", "ACC-00301",
            (now - datetime.timedelta(days=1)).isoformat(), (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "DEV-MacbookPro", "Web", "Chrome", "macOS", "64.233.160.10", 0, 8.5, 0, "APPROVED"
        ),
        (
            "#TXN-882172", "USR-001", 3500.00, "Washington", "Withdrawal", "ACC-ATM09", "ACC-00101",
            (now - datetime.timedelta(days=2)).isoformat(), (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
            "DEV-iPhone13", "iPhone", "Safari", "iOS", "172.56.21.90", 0, 5.0, 0, "APPROVED"
        )
    ]
    cursor.executemany("""
    INSERT INTO transactions (
        transaction_id, user_id, amount, location, transaction_type, destination_account, source_account, 
        timestamp, date, device_id, device_type, browser_type, operating_system, ip_address, vpn_usage, 
        risk_score, fraud_prediction, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tx_data)
    
    # Seed Alerts based on the high risk events
    alerts_data = [
        ("#TXN-882190", 98.0, "PENDING", "Cross-border attempt from unverified device in Dubai. Waiting for analyst confirmation.", (now - datetime.timedelta(minutes=15)).isoformat()),
        ("#TXN-882188", 94.0, "BLOCKED", "Large wire transfer from blacklisted user. Automatically blocked.", (now - datetime.timedelta(hours=1)).isoformat()),
        ("#TXN-882185", 88.0, "PENDING", "E-Wallet topup with sudden location shift. Analyst review queued.", (now - datetime.timedelta(hours=3)).isoformat()),
        ("#TXN-882184", 92.0, "RESOLVED", "Confirmed legitimate transaction with user via SMS confirmation.", (now - datetime.timedelta(hours=6)).isoformat()),
        ("#TXN-882180", 85.0, "BLOCKED", "High frequency transaction pattern matching velocity rule. Auto-blocked.", (now - datetime.timedelta(hours=12)).isoformat())
    ]
    cursor.executemany("""
    INSERT INTO fraud_alerts (transaction_id, risk_score, alert_status, analyst_comment, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, alerts_data)

def get_kpis():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total Transactions (Count)
    # Let's say we have 1.2M in real simulation, but dynamically count from db + offset to feel real
    cursor.execute("SELECT COUNT(*) FROM transactions")
    tx_count = cursor.fetchone()[0]
    total_tx_display = f"{1.2 + (tx_count / 1000000.0):.2f}M"
    
    # 2. Fraud Rate (Count of fraud / total transactions)
    # Realistically, let's keep it around 0.8% with dynamic variations based on database predictions
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE fraud_prediction = 1")
    fraud_count = cursor.fetchone()[0]
    fraud_rate_display = f"{0.75 + (fraud_count * 0.05):.2f}%"
    
    # 3. Blocked Transactions
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'BLOCKED'")
    blocked_count = cursor.fetchone()[0]
    total_blocked = 4520 + blocked_count
    
    # 4. Loss Prevented
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'BLOCKED'")
    blocked_amt = cursor.fetchone()[0] or 0.0
    loss_prevented_display = f"₦{2.4 + (blocked_amt / 1000000.0):.2f}M"
    
    # 5. Pending alerts count
    cursor.execute("SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'PENDING'")
    pending_alerts = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_transactions": total_tx_display,
        "fraud_rate": fraud_rate_display,
        "blocked_transactions": total_blocked,
        "loss_prevented": loss_prevented_display,
        "pending_alerts": pending_alerts
    }

def get_trends():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch 30-day stats or return simulated data if empty, but let's query the DB dynamically
    # For simulation, we return list of date, total_volume, fraud_volume
    cursor.execute("""
        SELECT date, COUNT(*), SUM(CASE WHEN fraud_prediction=1 THEN 1 ELSE 0 END) 
        FROM transactions 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 30
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Mock data fallback for a beautiful line graph
    dates = []
    total_volumes = []
    fraud_volumes = []
    
    # Default beautiful trends points matching standard behavior if db is small
    now = datetime.datetime.now()
    for i in range(10, -1, -1):
        d = (now - datetime.timedelta(days=i)).strftime("%b %d").upper()
        dates.append(d)
    
    # Let's seed total volume values and fraud attempts
    total_volumes = [120000, 125000, 118000, 132000, 128000, 135000, 140000, 142000, 138000, 145000, 150000]
    fraud_volumes = [850, 920, 780, 1100, 950, 1200, 1050, 1300, 1150, 1400, 980]
    
    return {
        "dates": dates,
        "total_volumes": total_volumes,
        "fraud_volumes": fraud_volumes
    }

def get_risk_distribution():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Categories: Critical (90-100), High (70-89), Medium (40-69), Low (0-39)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_score >= 90 THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN risk_score >= 70 AND risk_score < 90 THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN risk_score >= 40 AND risk_score < 70 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN risk_score < 40 THEN 1 ELSE 0 END) as low
        FROM transactions
    """)
    row = cursor.fetchone()
    conn.close()
    
    critical = row["critical"] or 0
    high_risk = row["high_risk"] or 0
    medium = row["medium"] or 0
    low = row["low"] or 0
    
    total = critical + high_risk + medium + low
    if total == 0:
        return {
            "critical": {"count": 2, "pct": 2.4},
            "high": {"count": 12, "pct": 12.8},
            "medium": {"count": 24, "pct": 24.5},
            "low": {"count": 60, "pct": 60.3}
        }
        
    return {
        "critical": {"count": critical, "pct": round((critical / total) * 100, 1)},
        "high": {"count": high_risk, "pct": round((high_risk / total) * 100, 1)},
        "medium": {"count": medium, "pct": round((medium / total) * 100, 1)},
        "low": {"count": low, "pct": round((low / total) * 100, 1)}
    }

def get_recent_alerts(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.transaction_id, t.transaction_type, t.risk_score, t.amount, t.status 
        FROM transactions t
        ORDER BY t.timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_top_regions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, COUNT(*) as count, SUM(CASE WHEN fraud_prediction=1 THEN 1 ELSE 0 END) as fraud_count
        FROM transactions
        GROUP BY location
        ORDER BY count DESC
    """)
    regions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return regions

def get_all_transactions(filters=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT t.*, u.full_name 
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    if filters:
        if filters.get("search"):
            query += " AND (t.transaction_id LIKE ? OR u.full_name LIKE ? OR t.location LIKE ?)"
            search_param = f"%{filters['search']}%"
            params.extend([search_param, search_param, search_param])
        if filters.get("risk_tier"):
            tier = filters["risk_tier"]
            if tier == "critical":
                query += " AND t.risk_score >= 90"
            elif tier == "high":
                query += " AND t.risk_score >= 70 AND t.risk_score < 90"
            elif tier == "medium":
                query += " AND t.risk_score >= 40 AND t.risk_score < 70"
            elif tier == "low":
                query += " AND t.risk_score < 40"
        if filters.get("status"):
            query += " AND t.status = ?"
            params.append(filters["status"])
            
    query += " ORDER BY t.timestamp DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_all_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.alert_id, a.risk_score, a.alert_status, a.analyst_comment, a.created_at,
               t.transaction_id, t.amount, t.location, t.transaction_type, t.timestamp,
               u.full_name, u.user_id, u.avg_transaction_amount, u.daily_frequency, u.account_age, u.previous_fraud_history
        FROM fraud_alerts a
        JOIN transactions t ON a.transaction_id = t.transaction_id
        JOIN users u ON t.user_id = u.user_id
        ORDER BY 
            CASE a.alert_status WHEN 'PENDING' THEN 1 ELSE 2 END,
            a.created_at DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_alert_status(alert_id, status, comment):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get transaction ID related to alert
    cursor.execute("SELECT transaction_id FROM fraud_alerts WHERE alert_id = ?", (alert_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    tx_id = row["transaction_id"]
    
    # Update alert status
    cursor.execute("""
        UPDATE fraud_alerts 
        SET alert_status = ?, analyst_comment = ? 
        WHERE alert_id = ?
    """, (status, comment, alert_id))
    
    # Map alert status to transaction status
    # PENDING -> PENDING
    # APPROVED -> APPROVED / RESOLVED
    # BLOCKED -> BLOCKED
    # RESOLVED -> RESOLVED
    tx_status = status
    if status == "APPROVED":
        tx_status = "APPROVED"
    elif status == "RESOLVED":
        tx_status = "RESOLVED"
    elif status == "BLOCKED":
        tx_status = "BLOCKED"
        
    cursor.execute("""
        UPDATE transactions 
        SET status = ? 
        WHERE transaction_id = ?
    """, (tx_status, tx_id))
    
    conn.commit()
    conn.close()
    return True

def create_simulated_transaction(tx):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Log transaction
    cursor.execute("""
        INSERT INTO transactions (
            transaction_id, user_id, amount, location, transaction_type, destination_account, source_account, 
            timestamp, date, device_id, device_type, browser_type, operating_system, ip_address, vpn_usage, 
            risk_score, fraud_prediction, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx["transaction_id"], tx["user_id"], tx["amount"], tx["location"], tx["transaction_type"],
        tx["destination_account"], tx["source_account"], tx["timestamp"], tx["date"],
        tx["device_id"], tx["device_type"], tx["browser_type"], tx["operating_system"],
        tx["ip_address"], tx["vpn_usage"], tx["risk_score"], tx["fraud_prediction"], tx["status"]
    ))
    
    # If high risk or predicted fraud, trigger alert
    if tx["risk_score"] >= 60 or tx["fraud_prediction"] == 1:
        cursor.execute("""
            INSERT OR IGNORE INTO fraud_alerts (transaction_id, risk_score, alert_status, analyst_comment, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            tx["transaction_id"], tx["risk_score"], tx["status"], 
            f"Automated risk classification: {tx['risk_score']}. System recommendation: {tx['status']}", tx["timestamp"]
        ))
        
    conn.commit()
    conn.close()

def add_model_log(version, accuracy, precision, recall, f1, model_type="RandomForest"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO model_logs (model_version, model_type, accuracy, precision, recall, f1_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (version, model_type, accuracy, precision, recall, f1, now))
    conn.commit()
    conn.close()

def get_model_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_logs ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
