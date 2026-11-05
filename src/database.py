
import sqlite3
from pathlib import Path

# Resolve project root relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "payments.db"


def get_connection():
    """Create a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """Create the transactions table and insert sample records."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT,
                amount REAL,
                payment_method TEXT,
                status TEXT,
                failure_code TEXT,
                failure_message TEXT,
                retry_count INTEGER
            )
        """)

        sample_transactions = [
            (
                "TXN-10025", "CUS-101", 2500.00,
                "UPI", "FAILED", "UPI_TIMEOUT",
                "Bank server did not respond in time.", 2
            ),
            (
                "TXN-10026", "CUS-102", 1500.00,
                "CARD", "FAILED", "INSUFFICIENT_FUNDS",
                "The issuing bank declined the payment.", 1
            ),
            (
                "TXN-10027", "CUS-103", 5000.00,
                "UPI", "SUCCESS", None,
                None, 0
            ),
            (
                "TXN-10028", "CUS-104", 3200.00,
                "CARD", "PENDING", "GATEWAY_TIMEOUT",
                "Payment gateway response timed out.", 1
            ),
            (
                "TXN-10029", "CUS-105", 1800.00,
                "NET_BANKING", "FAILED", "BANK_DECLINED",
                "Transaction declined by the bank.", 3
            )
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO transactions
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_transactions)

        conn.commit()

    print("Payment database initialized successfully!")


def get_transaction(transaction_id):
    """Retrieve a transaction using its ID."""

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM transactions
            WHERE transaction_id = ?
        """, (transaction_id,))

        result = cursor.fetchone()

        return dict(result) if result else None


def initialize_review_table():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_records (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                reviewer TEXT NOT NULL,
                decision TEXT NOT NULL,
                review_notes TEXT,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id)
                    REFERENCES transactions(transaction_id)
            )
        """)

        conn.commit()

    print("Review records table initialized!")


def save_review(transaction_id, reviewer, decision, review_notes):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO review_records (
                transaction_id,
                reviewer,
                decision,
                review_notes
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(transaction_id)
            DO UPDATE SET
                reviewer = excluded.reviewer,
                decision = excluded.decision,
                review_notes = excluded.review_notes,
                reviewed_at = CURRENT_TIMESTAMP
        """, (
            transaction_id,
            reviewer,
            decision,
            review_notes
        ))

        conn.commit()

    return True


def get_review(transaction_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM review_records
            WHERE transaction_id = ?
        """, (transaction_id,))

        result = cursor.fetchone()

        return dict(result) if result else None
    

def get_all_reviews(limit=50):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.review_id,
                r.transaction_id,
                t.payment_method,
                t.failure_code,
                t.status AS transaction_status,
                r.reviewer,
                r.decision,
                r.review_notes,
                r.reviewed_at
            FROM review_records r
            JOIN transactions t
                ON r.transaction_id = t.transaction_id
            ORDER BY r.review_id DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    initialize_database()
    initialize_review_table()

    transaction = get_transaction("TXN-10025")
    print("\nTransaction details:")
    print(transaction)