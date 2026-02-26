from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = "db.sqlite3"

# DATABASE CONNECTION

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# TABLE CREATION

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Roles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Departments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role_id INTEGER,
        department_id INTEGER
    )
    """)

    # Budgets
    cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER,
        total_budget REAL,
        used_budget REAL DEFAULT 0
    )
    """)

    # Transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        department_id INTEGER,
        amount REAL,
        status TEXT,
        reason TEXT,
        timestamp TEXT
    )
    """)

    # Audit Logs (Blockchain Simulation)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        data TEXT,
        previous_hash TEXT,
        current_hash TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

# ROLES

def seed_roles():
    conn = get_db()
    cur = conn.cursor()

    roles = ["super_admin", "manager", "employee", "auditor"]

    for role in roles:
        try:
            cur.execute("INSERT INTO roles (name) VALUES (?)", (role,))
        except:
            pass

    conn.commit()
    conn.close()

# SETUP

@app.route("/")
def home():
    return "Smart FinOps Backend Running"

# BLOCKCHAIN HASH FUNCTION

def generate_hash(data, previous_hash):
    block_string = json.dumps(data, sort_keys=True) + str(previous_hash)
    return hashlib.sha256(block_string.encode()).hexdigest()

# REJECTION HELPER ------------------

def reject_transaction(cur, conn, user_id, dept_id, amount, reason):
    cur.execute("""
        INSERT INTO transactions 
        (user_id, department_id, amount, status, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, dept_id, amount, "rejected", reason, datetime.now()))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "Rejected",
        "reason": reason
    })

# SMART TRANSACTION POLICY ENGINE -----------------

@app.route("/request_transaction", methods=["POST"])
def request_transaction():
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")

    if not user_id or not amount:
        return jsonify({"error": "User ID and amount required"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Get User
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    dept_id = user["department_id"]

    # Get Budget
    cur.execute("SELECT * FROM budgets WHERE department_id=?", (dept_id,))
    budget = cur.fetchone()

    if not budget:
        return jsonify({"error": "No budget allocated"}), 400

    remaining_budget = budget["total_budget"] - budget["used_budget"]

    # Get Role
    cur.execute("SELECT name FROM roles WHERE id=?", (user["role_id"],))
    role = cur.fetchone()["name"]

    # ROLE POLICY CHECKS
    if role == "employee" and amount > 25000:
        return reject_transaction(cur, conn, user_id, dept_id, amount, "Employee limit exceeded")

    if role == "manager" and amount > 100000:
        return reject_transaction(cur, conn, user_id, dept_id, amount, "Manager limit exceeded")

    if amount > remaining_budget:
        return reject_transaction(cur, conn, user_id, dept_id, amount, "Budget exceeded")

    # ONLY CREATE PENDING TRANSACTION
    cur.execute("""
        INSERT INTO transactions
        (user_id, department_id, amount, status, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, dept_id, amount, "pending", "", datetime.now()))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "Pending Approval",
        "message": "Transaction submitted for approval"
    })

# APPROVAL ROUTES

@app.route("/approve_transaction", methods=["POST"])
def approve_transaction():
    data = request.json
    transaction_id = data.get("transaction_id")
    approver_id = data.get("approver_id")

    conn = get_db()
    cur = conn.cursor()

    # Get transaction
    cur.execute("SELECT * FROM transactions WHERE id=?", (transaction_id,))
    tx = cur.fetchone()

    if not tx:
        return jsonify({"error": "Transaction not found"}), 404

    if tx["status"] != "pending":
        return jsonify({"error": "Transaction already processed"}), 400

    dept_id = tx["department_id"]
    amount = tx["amount"]

    # Check budget
    cur.execute("SELECT * FROM budgets WHERE department_id=?", (dept_id,))
    budget = cur.fetchone()

    # Check approver role
    cur.execute("SELECT role_id FROM users WHERE id=?", (approver_id,))
    approver = cur.fetchone()

    if not approver:
        return jsonify({"error": "Approver not found"}), 404

    cur.execute("SELECT name FROM roles WHERE id=?", (approver["role_id"],))
    role = cur.fetchone()["name"]

    if role != "manager":
        return jsonify({"error": "Only managers can approve"}), 403

    remaining = budget["total_budget"] - budget["used_budget"]

    if amount > remaining:
        return jsonify({"error": "Budget exceeded"}), 400

    # Deduct budget
    cur.execute("""
        UPDATE budgets
        SET used_budget = used_budget + ?
        WHERE department_id=?
    """, (amount, dept_id))

    # Update transaction status
    cur.execute("""
        UPDATE transactions
        SET status='approved'
        WHERE id=?
    """, (transaction_id,))

    # BLOCKCHAIN LOGGING AFTER APPROVAL

    cur.execute("SELECT current_hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    prev = cur.fetchone()
    previous_hash = prev["current_hash"] if prev else "0"

    log_data = {
        "transaction_id": transaction_id,
        "department_id": dept_id,
        "amount": amount,
        "approved_by": approver_id,
        "timestamp": str(datetime.now())
    }

    current_hash = generate_hash(log_data, previous_hash)

    cur.execute("""
        INSERT INTO audit_logs
        (action, data, previous_hash, current_hash, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, ("approved_transaction", json.dumps(log_data),
        previous_hash, current_hash, datetime.now()))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "Approved",
        "remaining_budget": remaining - amount
    })

# SEE TRANSACTIONS

@app.route("/list_transactions", methods=["GET"])
def list_transactions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    txs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(txs)

# EXISITING USERS

@app.route("/list_users", methods=["GET"])
def list_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(users)


# AUDIT LOGS

@app.route("/audit_logs", methods=["GET"])
def get_audit_logs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_logs ORDER BY id ASC")
    logs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(logs)

# BLOCKCHAIN INTEGRITY VERIFICATION

@app.route("/verify_chain", methods=["GET"])
def verify_chain():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_logs ORDER BY id ASC")
    logs = cur.fetchall()

    previous_hash = "0"

    for log in logs:
        try:
            data = json.loads(log["data"])
        except:
            return jsonify({
                "status": "Tampering Detected (Invalid JSON)",
                "log_id": log["id"]
            })

        recalculated_hash = generate_hash(data, previous_hash)

        if log["current_hash"] != recalculated_hash:
            return jsonify({
                "status": "Tampering Detected (Hash Mismatch)",
                "log_id": log["id"]
            })

        previous_hash = log["current_hash"]

    return jsonify({"status": "Blockchain Integrity Verified"})

# API CONNECTION -------------------------------

# DEPARTMENT CREATION API

@app.route("/create_department", methods=["POST"])
def create_department():
    data = request.json
    name = data.get("name")

    if not name:
        return jsonify({"error": "Department name required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO departments (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Department created successfully"})

# BUDGET API

@app.route("/allocate_budget", methods=["POST"])
def allocate_budget():
    data = request.json
    dept_id = data.get("department_id")
    amount = data.get("amount")

    if not dept_id or not amount:
        return jsonify({"error": "Department ID and amount required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO budgets (department_id, total_budget) VALUES (?, ?)",
        (dept_id, amount),
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Budget allocated successfully"})

# USER API

@app.route("/create_user", methods=["POST"])
def create_user():
    data = request.json
    name = data.get("name")
    role_id = data.get("role_id")
    department_id = data.get("department_id")

    if not name or not role_id:
        return jsonify({"error": "Name and role required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name, role_id, department_id) VALUES (?, ?, ?)",
        (name, role_id, department_id),
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "User created successfully"})

# TAMPERING

@app.route("/tamper_demo", methods=["GET"])
def tamper_demo():
    conn = get_db()
    cur = conn.cursor()

    # Modify first audit log entry
    cur.execute("UPDATE audit_logs SET data='tampered data' WHERE id=1")

    conn.commit()
    conn.close()

    return jsonify({"message": "Audit log manually altered"})

# DEFAULT -------------------------------------------

if __name__ == "__main__":
    init_db()
    seed_roles()
    app.run(debug=True)