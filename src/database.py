
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


if __name__ == "__main__":

    initialize_database()

    transaction = get_transaction("TXN-10025")

    print("\nTransaction details:")
    print(transaction)
