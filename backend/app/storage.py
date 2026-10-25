from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import RedactionJob


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
        connection.execute("""CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
            date_of_birth TEXT, phone TEXT, email TEXT, postal_address TEXT,
            customer_status TEXT NOT NULL, created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id TEXT PRIMARY KEY, owner_customer_id TEXT NOT NULL, registration_number TEXT,
            vin TEXT, manufacturer TEXT, model TEXT, production_year INTEGER, color TEXT
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY, policy_number TEXT UNIQUE NOT NULL, customer_id TEXT NOT NULL,
            insurance_product TEXT NOT NULL, effective_start TEXT NOT NULL, effective_end TEXT NOT NULL,
            policy_status TEXT NOT NULL, assigned_vehicle_id TEXT, insurer_reference TEXT
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY, job_id TEXT UNIQUE NOT NULL, customer_id TEXT, policy_id TEXT,
            vehicle_id TEXT, workflow_status TEXT NOT NULL, review_state TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS claim_evidence (
            evidence_id TEXT PRIMARY KEY, claim_id TEXT NOT NULL, recording_id TEXT NOT NULL,
            source_start_time REAL, source_end_time REAL, transcript_span TEXT,
            linked_fact_id TEXT, review_status TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS privacy_reviews (
            review_id TEXT PRIMARY KEY, claim_id TEXT NOT NULL, entity_id TEXT NOT NULL,
            privacy_policy TEXT NOT NULL, redaction_action TEXT NOT NULL,
            review_status TEXT NOT NULL, reviewed_at TEXT
        )""")
        _seed_demo_data(connection)


def _seed_demo_data(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]:
        return
    connection.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("CUST-001", "Karim", "Amrani", "1988-04-19", "0612345678", "karim.amrani@example.test", "Casablanca, Maroc", "ACTIVE", "2026-01-01T00:00:00Z"),
            ("CUST-002", "Karim", "Amrani", "1991-09-02", "0677889900", "karim.amrani.2@example.test", "Rabat, Maroc", "ACTIVE", "2026-01-01T00:00:00Z"),
            ("CUST-003", "Youssef", "Amrani", "1985-02-11", "0600112233", "youssef.amrani@example.test", "Casablanca, Maroc", "ACTIVE", "2026-01-01T00:00:00Z"),
        ],
    )
    connection.executemany(
        "INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("VEH-001", "CUST-001", "12345-A-6", "VF1DEMOCLAIM001", "Renault", "Clio", 2019, "Gris"),
            ("VEH-002", "CUST-002", "98765-B-4", "VF1DEMOCLAIM002", "Peugeot", "208", 2021, "Bleu"),
            ("VEH-003", "CUST-003", "45678-C-2", "VF1DEMOCLAIM003", "Dacia", "Sandero", 2018, "Blanc"),
        ],
    )
    connection.executemany(
        "INSERT INTO policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("POL-001", "AUTO-4582", "CUST-001", "Assurance Automobile", "2025-01-01", "2026-12-31", "ACTIVE", "VEH-001", "INS-DEMO-4582"),
            ("POL-002", "AUTO-7719", "CUST-002", "Assurance Automobile", "2026-01-01", "2026-12-31", "ACTIVE", "VEH-002", "INS-DEMO-7719"),
            ("POL-003", "AUTO-9901", "CUST-003", "Assurance Automobile", "2024-01-01", "2025-12-31", "EXPIRED", "VEH-003", "INS-DEMO-9901"),
        ],
    )


def save(path: Path, job: RedactionJob) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT OR REPLACE INTO jobs (id, payload, updated_at) VALUES (?, ?, datetime('now'))", (job.id, job.model_dump_json()))
        if job.claim and job.claim.claim_id:
            connection.execute(
                """INSERT OR REPLACE INTO claims
                (claim_id, job_id, customer_id, policy_id, vehicle_id, workflow_status, review_state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM claims WHERE claim_id = ?), datetime('now')), datetime('now'))""",
                (job.claim.claim_id, job.id, job.claim.selected_customer_id, job.claim.selected_policy_id,
                 job.claim.selected_vehicle_id, job.claim.workflow_status.value, job.claim.review_status.value, job.claim.claim_id),
            )
            connection.execute("DELETE FROM claim_evidence WHERE claim_id = ?", (job.claim.claim_id,))
            for fact in job.claim.facts:
                connection.execute(
                    "INSERT INTO claim_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (fact.id, job.claim.claim_id, job.id, fact.evidence.audio_start, fact.evidence.audio_end,
                     fact.evidence_text, fact.id, fact.verification_state.value),
                )


def load(path: Path, job_id: str) -> RedactionJob | None:
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT payload FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return RedactionJob.model_validate_json(row[0]) if row else None


def delete(path: Path, job_id: str) -> None:
    with sqlite3.connect(path) as connection:
        claim_ids = [row[0] for row in connection.execute("SELECT claim_id FROM claims WHERE job_id = ?", (job_id,)).fetchall()]
        for claim_id in claim_ids:
            connection.execute("DELETE FROM claim_evidence WHERE claim_id = ?", (claim_id,))
            connection.execute("DELETE FROM privacy_reviews WHERE claim_id = ?", (claim_id,))
        connection.execute("DELETE FROM claims WHERE job_id = ?", (job_id,))
        connection.execute("DELETE FROM jobs WHERE id = ?", (job_id,))


def list_jobs(path: Path) -> list[RedactionJob]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT payload FROM jobs ORDER BY updated_at DESC").fetchall()
    return [RedactionJob.model_validate_json(row[0]) for row in rows]


def search_customers(path: Path, query: str = "") -> list[dict]:
    normalized = f"%{query.strip().lower()}%"
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            """SELECT customer_id, first_name, last_name, phone, email, postal_address, customer_status
               FROM customers WHERE lower(first_name || ' ' || last_name) LIKE ? OR lower(customer_id) LIKE ?
               ORDER BY last_name, first_name""", (normalized, normalized),
        ).fetchall()
    return [{"customer_id": row[0], "full_name": f"{row[1]} {row[2]}", "phone": row[3], "email": row[4], "postal_address": row[5], "customer_status": row[6]} for row in rows]


def search_policies(path: Path, query: str = "") -> list[dict]:
    normalized = f"%{query.strip().lower()}%"
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            """SELECT p.policy_id, p.policy_number, p.insurance_product, p.policy_status,
                      p.effective_start, p.effective_end, p.customer_id,
                      c.first_name || ' ' || c.last_name, p.assigned_vehicle_id,
                      v.registration_number, v.manufacturer || ' ' || v.model
               FROM policies p JOIN customers c ON c.customer_id = p.customer_id
               LEFT JOIN vehicles v ON v.vehicle_id = p.assigned_vehicle_id
               WHERE lower(p.policy_number) LIKE ? OR lower(c.first_name || ' ' || c.last_name) LIKE ?
               ORDER BY p.policy_number""", (normalized, normalized),
        ).fetchall()
    return [{"policy_id": row[0], "policy_number": row[1], "insurance_product": row[2], "policy_status": row[3], "effective_start": row[4], "effective_end": row[5], "customer_id": row[6], "customer_name": row[7], "vehicle_id": row[8], "registration_number": row[9], "vehicle_label": row[10]} for row in rows]

