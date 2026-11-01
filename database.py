"""
Database module for Personal Expense Tracker with Multi-User isolation.
Manages SQLite connection, schema creation, user accounts, and per-user data queries.
"""

import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from werkzeug.security import generate_password_hash

def get_db_path() -> str:
    """Returns database file path, supporting serverless /tmp fallback and environment overrides."""
    if "EXPENSES_DB" in os.environ:
        return os.environ["EXPENSES_DB"]
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/expenses.db"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

DB_FILE = get_db_path()

def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite database with Row factory and foreign keys enabled."""
    db_path = DB_FILE or get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(seed_sample_data: bool = True) -> None:
    """Initializes tables with per-user schema and seeds sample user if requested."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check if existing transactions table has user_id; if not, migrate cleanly
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(transactions)")
        cols = [col["name"] for col in cursor.fetchall()]
        if "user_id" not in cols:
            cursor.execute("DROP TABLE IF EXISTS transactions")
            cursor.execute("DROP TABLE IF EXISTS budgets")

    # Create transactions table scoped to user_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        transaction_date DATE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Create budgets table scoped to user_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        monthly_limit REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, month, year),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Create indexes for fast querying per user
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_user_date ON transactions(user_id, transaction_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_user_cat ON transactions(user_id, category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user_my ON budgets(user_id, month, year);")

    conn.commit()

    # Seed demo user and records if requested and database is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0 and seed_sample_data:
        seed_data(conn)

    conn.close()

# User Management Functions
def create_user(username: str, password_hash: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (username, password_hash)
    VALUES (?, ?)
    """, (username.strip().lower(), password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def seed_data(conn: Optional[sqlite3.Connection] = None) -> int:
    """Seeds a demo user with realistic sample transactions and budget."""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()
    demo_pw = generate_password_hash("demo123")
    cursor.execute("""
    INSERT INTO users (username, password_hash)
    VALUES ('demo', ?)
    """, (demo_pw,))
    demo_user_id = cursor.lastrowid

    now = datetime.now()
    cur_year = now.year
    cur_month = now.month

    # Set default budget for demo user
    cursor.execute("""
    INSERT OR REPLACE INTO budgets (user_id, monthly_limit, month, year)
    VALUES (?, 30000.0, ?, ?)
    """, (demo_user_id, cur_month, cur_year))

    prev_month = 12 if cur_month == 1 else cur_month - 1
    prev_year = cur_year - 1 if cur_month == 1 else cur_year

    cursor.execute("""
    INSERT OR IGNORE INTO budgets (user_id, monthly_limit, month, year)
    VALUES (?, 30000.0, ?, ?)
    """, (demo_user_id, prev_month, prev_year))

    def date_offset(days_ago: int) -> str:
        return (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    sample_records = [
        # Today
        (demo_user_id, 999.0, "Entertainment", "Streaming sub", date_offset(0)),
        (demo_user_id, 160.0, "Food", "Breakfast", date_offset(0)),
        (demo_user_id, 50.0, "Health", "Medicine / Care", date_offset(0)),

        # Yesterday
        (demo_user_id, 540.0, "Food", "Groceries", date_offset(1)),
        (demo_user_id, 220.0, "Transport", "Fuel", date_offset(1)),

        # 2 days ago
        (demo_user_id, 130.0, "Food", "Coffee & Snacks", date_offset(2)),

        # 3 days ago
        (demo_user_id, 290.0, "Food", "Dinner", date_offset(3)),

        # 4 days ago
        (demo_user_id, 1750.0, "Bills", "Rent share", date_offset(4)),

        # 5 days ago
        (demo_user_id, 350.0, "Shopping", "Desk Organizer", date_offset(5)),

        # 6 days ago
        (demo_user_id, 450.0, "Entertainment", "Movie ticket", date_offset(6)),

        # 7 days ago
        (demo_user_id, 400.0, "Education", "Online Course Material", date_offset(7)),

        # 8 days ago
        (demo_user_id, 850.0, "Travel", "Weekend Train ticket", date_offset(8)),

        # Historical transactions to populate 30D, 6M, and comparison stats
        (demo_user_id, 1200.0, "Entertainment", "Concert pass", date_offset(14)),
        (demo_user_id, 1500.0, "Bills", "Utility bill", date_offset(18)),
        (demo_user_id, 650.0, "Food", "Supermarket run", date_offset(22)),
        (demo_user_id, 320.0, "Transport", "Metro recharge & Cab", date_offset(25)),
        (demo_user_id, 750.0, "Shopping", "Clothing item", date_offset(28)),
        (demo_user_id, 180.0, "Health", "Pharmacy essentials", date_offset(32)),
        (demo_user_id, 420.0, "Food", "Team Lunch", date_offset(35)),
        (demo_user_id, 110.0, "Food", "Cafe coffee", date_offset(38)),
        (demo_user_id, 500.0, "Education", "Books & Stationery", date_offset(42)),
        (demo_user_id, 800.0, "Travel", "Bus fare", date_offset(45)),
        (demo_user_id, 1600.0, "Bills", "Apartment Maintenance", date_offset(50))
    ]

    cursor.executemany("""
    INSERT INTO transactions (user_id, amount, category, note, transaction_date)
    VALUES (?, ?, ?, ?, ?)
    """, sample_records)

    conn.commit()
    if should_close:
        conn.close()
    return demo_user_id

# CRUD operations for Transactions - Scoped strictly per user
def get_all_transactions(user_id: int, category: Optional[str] = None, search: Optional[str] = None,
                         date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transactions WHERE user_id = ?"
    params: List[Any] = [user_id]

    if category and category.lower() != 'all':
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query += " AND (LOWER(note) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?))"
        params.extend([term, term])

    if date_from and date_from.strip():
        query += " AND transaction_date >= ?"
        params.append(date_from.strip())

    if date_to and date_to.strip():
        query += " AND transaction_date <= ?"
        params.append(date_to.strip())

    query += " ORDER BY transaction_date DESC, id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_transaction_by_id(user_id: int, transaction_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_transaction(user_id: int, amount: float, category: str, note: Optional[str], transaction_date: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (user_id, amount, category, note, transaction_date)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, category.strip(), note.strip() if note else None, transaction_date.strip()))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_transaction(user_id: int, transaction_id: int, amount: float, category: str, note: Optional[str], transaction_date: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE transactions
    SET amount = ?, category = ?, note = ?, transaction_date = ?
    WHERE id = ? AND user_id = ?
    """, (amount, category.strip(), note.strip() if note else None, transaction_date.strip(), transaction_id, user_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_transaction(user_id: int, transaction_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# Budget operations - Scoped strictly per user
def get_budget_for_month(user_id: int, month: int, year: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = ? AND month = ? AND year = ?", (user_id, month, year))
    row = cursor.fetchone()
    conn.close()
    if row:
        return float(row["monthly_limit"])
    return 30000.0  # Default budget limit for any user

def set_budget_for_month(user_id: int, monthly_limit: float, month: int, year: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO budgets (user_id, monthly_limit, month, year)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, month, year) DO UPDATE SET
        monthly_limit = excluded.monthly_limit,
        created_at = CURRENT_TIMESTAMP
    """, (user_id, monthly_limit, month, year))
    conn.commit()
    conn.close()

# Analytics and Aggregations - Scoped strictly per user
def get_monthly_spent(user_id: int, month: int, year: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()
    prefix = f"{year:04d}-{month:02d}-%"
    cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM transactions WHERE user_id = ? AND transaction_date LIKE ?", (user_id, prefix))
    total = cursor.fetchone()[0]
    conn.close()
    return float(total)

def get_category_spending_for_month(user_id: int, month: int, year: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    prefix = f"{year:04d}-{month:02d}-%"
    cursor.execute("""
    SELECT category, COALESCE(SUM(amount), 0.0) as total, COUNT(*) as count
    FROM transactions
    WHERE user_id = ? AND transaction_date LIKE ?
    GROUP BY category
    ORDER BY total DESC
    """, (user_id, prefix))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
