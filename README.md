# 🏛 Smart FinOps – Real-Time Policy-Driven Financial Governance Platform

## 📌 Overview

Smart FinOps is a real-time financial governance system designed to ensure transparent, accountable, and policy-driven budget management.

The system integrates:

- Role-based access control
- Department-level budget enforcement
- Hierarchical approval workflow
- Blockchain-inspired tamper-evident audit logging
- Optional Ethereum smart contract anchoring

This project was developed as a prototype for the Tamil Nadu Hackathon.

---

# 🏗 System Architecture

Hybrid Web2 + Web3 Architecture:

Flask Backend (Python)
        ↓
Policy Engine + Budget Validation
        ↓
SHA-256 Hash Chain Audit Logs
        ↓
(Optional) Ethereum Smart Contract Anchor

---

# 🔐 Core Features

## 1️⃣ Role-Based Governance

Roles:
- Super Admin
- Manager
- Employee
- Auditor

Each role has defined financial limits and permissions.

---

## 2️⃣ Budget Allocation & Enforcement

- Department budgets are allocated
- Real-time tracking of used budget
- Automatic prevention of overspending
- Policy-driven rejection for rule violations

---

## 3️⃣ Hierarchical Approval Workflow

Transaction Flow:

1. Employee submits request → Status: Pending
2. Manager reviews and approves
3. Budget is deducted only after approval
4. Approved transactions are recorded in blockchain log

---

## 4️⃣ Blockchain-Inspired Audit Logging

Every approved transaction:

- Generates SHA-256 hash
- Links to previous block hash
- Stored in audit_logs table
- Can be verified via `/verify_chain`

Tampering detection is implemented.

---

## 5️⃣ Tamper Detection

If any audit record is altered:

- Hash mismatch is detected
- `/verify_chain` returns corruption alert

Demonstrates blockchain immutability principles.


---

## 🔐 Authentication APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/register` | Register new user (Admin / Manager / Employee) |
| POST | `/login` | Authenticate user and return role |

---

## 👤 User Management APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/users` | Get all users |
| GET | `/users/<id>` | Get user by ID |
| DELETE | `/users/<id>` | Delete user |

---

## 💰 Budget Management APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/set-budget` | Set department budget |
| GET | `/budget` | Get current budget details |
| PUT | `/update-budget` | Update department budget |

---

## 💳 Transaction APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/transaction` | Create new transaction |
| GET | `/transactions` | Get all transactions |
| GET | `/transactions/<id>` | Get transaction by ID |
| PUT | `/approve/<id>` | Approve transaction (Admin only) |
| DELETE | `/transaction/<id>` | Delete transaction |

---

## ⚖️ Policy Engine APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/validate-transaction` | Validate transaction against policies |
| POST | `/add-policy` | Add new financial policy |
| GET | `/policies` | Get all active policies |

---

## 📊 Reports & Audit APIs

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/dashboard-summary` | Get total budget, spent, remaining |
| GET | `/department-report` | Get department-wise spending report |
| GET | `/audit-log` | Get immutable audit logs |

---

## 🔄 System Workflow

1. User logs in.
2. User creates transaction.
3. Policy engine validates transaction.
4. If valid → Stored as Pending.
5. Admin approves transaction.
6. Audit log recorded and budget updated.

---

## 🛠 Tech Stack

- Flask (Python)
- SQLite
- Role-Based Access Control (RBAC)
- Policy-Driven Validation Engine
- Immutable Audit Logging
