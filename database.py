"""
Database module for Personal Expense Tracker with Multi-User isolation.
Manages PostgreSQL connections, schema creation, user accounts, and per-user data queries.
"""

import os
import ssl
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, unquote, urlparse

import pg8000.dbapi
from werkzeug.security import generate_password_hash

DEFAULT_DATABASE_URL = "postgresql://postgres@localhost:5432/expense_tracker"


def get_database_url() -> str:
    """Returns the PostgreSQL connection URL, normalizing postgres:// URLs."""
    url = os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = get_database_url()


def _connection_params(url: str) -> Dict[str, Any]:
    """Converts a PostgreSQL URL into pg8000 connection arguments."""
    parsed = urlparse(url)
    options = dict(parse_qsl(parsed.query))
    params: Dict[str, Any] = {
        "user": unquote(parsed.username) if parsed.username else "postgres",
        "password": unquote(parsed.password) if parsed.password else None,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "expense_tracker",
        "timeout": int(options.get("connect_timeout", "10")),
    }
    if options.get("sslmode") in ("require", "verify-ca", "verify-full"):
        context = ssl.create_default_context()
        if options["sslmode"] == "require":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        params["ssl_context"] = context
    return params


class DictCursor:
    """pg8000 cursor that returns rows as dictionaries."""

    def __init__(self, cursor: Any):
        self._cursor = cursor
        self._columns: List[str] = []

    def __enter__(self) -> "DictCursor":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._cursor.close()

    def execute(self, sql: str, params: Optional[Any] = None) -> None:
        self._cursor.execute(sql, params if params is not None else ())
        self._columns = [column[0] for column in (self._cursor.description or ())]

    def executemany(self, sql: str, params: Any) -> None:
        self._cursor.executemany(sql, params)
        self._columns = []

    def _to_dict(self, row: Any) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {name: row[index] for index, name in enumerate(self._columns)}

    def fetchone(self) -> Optional[Dict[str, Any]]:
        return self._to_dict(self._cursor.fetchone())

    def fetchall(self) -> List[Dict[str, Any]]:
        return [self._to_dict(row) for row in self._cursor.fetchall()]

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount


class PgConnection:
    """Thin pg8000 wrapper providing dictionary cursors."""

    def __init__(self, url: str):
        self._connection = pg8000.dbapi.connect(**_connection_params(url))

    def cursor(self) -> DictCursor:
        return DictCursor(self._connection.cursor())

    def commit(self) -> None:
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()


def get_db_connection() -> PgConnection:
    """Creates a pure-Python PostgreSQL connection, suitable for Vercel Functions."""
    return PgConnection(DATABASE_URL or get_database_url())


def init_db(seed_sample_data: bool = True) -> None:
    """Initializes tables with per-user schema and seeds sample user if requested."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            transaction_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            monthly_limit DOUBLE PRECISION NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, month, year),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_user_date ON transactions(user_id, transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_user_cat ON transactions(user_id, category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user_my ON budgets(user_id, month, year)")

        cursor.execute("SELECT COUNT(*) AS user_count FROM users")
        user_count = cursor.fetchone()["user_count"]
    conn.commit()

    if user_count == 0 and seed_sample_data:
        seed_data(conn)

    conn.close()

# User Management Functions
def create_user(username: str, password_hash: str) -> int:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s)
        RETURNING id
        """, (username.strip().lower(), password_hash))
        user_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (username.strip(),))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def seed_data(conn: Optional[PgConnection] = None) -> int:
    """Seeds a demo user with realistic sample transactions and budget."""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    with conn.cursor() as cursor:
        demo_pw = generate_password_hash("demo123")
        cursor.execute("""
        INSERT INTO users (username, password_hash)
        VALUES ('demo', %s)
        RETURNING id
        """, (demo_pw,))
        demo_user_id = cursor.fetchone()["id"]

        now = datetime.now()
        cur_year = now.year
        cur_month = now.month

        cursor.execute("""
        INSERT INTO budgets (user_id, monthly_limit, month, year)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, month, year) DO UPDATE SET
            monthly_limit = EXCLUDED.monthly_limit,
            created_at = CURRENT_TIMESTAMP
        """, (demo_user_id, 30000.0, cur_month, cur_year))

        prev_month = 12 if cur_month == 1 else cur_month - 1
        prev_year = cur_year - 1 if cur_month == 1 else cur_year

        cursor.execute("""
        INSERT INTO budgets (user_id, monthly_limit, month, year)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, month, year) DO NOTHING
        """, (demo_user_id, 30000.0, prev_month, prev_year))

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
        VALUES (%s, %s, %s, %s, %s)
        """, sample_records)

    conn.commit()
    if should_close:
        conn.close()
    return demo_user_id

# CRUD operations for Transactions - Scoped strictly per user
def get_all_transactions(user_id: int, category: Optional[str] = None, search: Optional[str] = None,
                         date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        query = "SELECT * FROM transactions WHERE user_id = %s"
        params: List[Any] = [user_id]

        if category and category.lower() != 'all':
            query += " AND LOWER(category) = LOWER(%s)"
            params.append(category)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query += " AND (note ILIKE %s OR category ILIKE %s)"
            params.extend([term, term])

        if date_from and date_from.strip():
            query += " AND transaction_date >= %s"
            params.append(date_from.strip())

        if date_to and date_to.strip():
            query += " AND transaction_date <= %s"
            params.append(date_to.strip())

        query += " ORDER BY transaction_date DESC, id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_transaction_by_id(user_id: int, transaction_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, user_id))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_transaction(user_id: int, amount: float, category: str, note: Optional[str], transaction_date: str) -> int:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO transactions (user_id, amount, category, note, transaction_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """, (user_id, amount, category.strip(), note.strip() if note else None, transaction_date.strip()))
        new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return new_id

def update_transaction(user_id: int, transaction_id: int, amount: float, category: str, note: Optional[str], transaction_date: str) -> bool:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        UPDATE transactions
        SET amount = %s, category = %s, note = %s, transaction_date = %s
        WHERE id = %s AND user_id = %s
        """, (amount, category.strip(), note.strip() if note else None, transaction_date.strip(), transaction_id, user_id))
        updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_transaction(user_id: int, transaction_id: int) -> bool:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, user_id))
        deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Budget operations - Scoped strictly per user
def get_budget_for_month(user_id: int, month: int, year: int) -> float:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = %s AND month = %s AND year = %s", (user_id, month, year))
        row = cursor.fetchone()
    conn.close()
    if row:
        return float(row["monthly_limit"])
    return 30000.0  # Default budget limit for any user

def set_budget_for_month(user_id: int, monthly_limit: float, month: int, year: int) -> None:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO budgets (user_id, monthly_limit, month, year)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, month, year) DO UPDATE SET
            monthly_limit = EXCLUDED.monthly_limit,
            created_at = CURRENT_TIMESTAMP
        """, (user_id, monthly_limit, month, year))
    conn.commit()
    conn.close()

# Analytics and Aggregations - Scoped strictly per user
def get_monthly_spent(user_id: int, month: int, year: int) -> float:
    conn = get_db_connection()
    month_start = date(year, month, 1)
    month_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT COALESCE(SUM(amount), 0.0) AS total
        FROM transactions
        WHERE user_id = %s AND transaction_date >= %s AND transaction_date < %s
        """, (user_id, month_start, month_end))
        total = cursor.fetchone()["total"]
    conn.close()
    return float(total)

def get_category_spending_for_month(user_id: int, month: int, year: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    month_start = date(year, month, 1)
    month_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT category, COALESCE(SUM(amount), 0.0) as total, COUNT(*) as count
        FROM transactions
        WHERE user_id = %s AND transaction_date >= %s AND transaction_date < %s
        GROUP BY category
        ORDER BY total DESC
        """, (user_id, month_start, month_end))
        rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
