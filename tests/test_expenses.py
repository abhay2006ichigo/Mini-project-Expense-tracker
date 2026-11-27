"""
Unit and integration tests for Expense Tracker endpoints with multi-user session management.
"""

import os
import unittest
from datetime import date
from werkzeug.security import generate_password_hash
import database
from app import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL must point to a PostgreSQL test database")
class TestExpenses(unittest.TestCase):
    def setUp(self):
        if TEST_DATABASE_URL.replace("postgres://", "postgresql://", 1) == database.get_database_url():
            raise RuntimeError("TEST_DATABASE_URL must be a separate database from DATABASE_URL")
        self.original_url = database.DATABASE_URL
        self.original_initialized = getattr(app, "_db_initialized", False)
        database.DATABASE_URL = TEST_DATABASE_URL
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS transactions, budgets, users CASCADE")
        conn.commit()
        conn.close()
        database.init_db(seed_sample_data=False)

        # Create two separate users
        self.user1_id = database.create_user("testuser1", generate_password_hash("pass123"))
        self.user2_id = database.create_user("testuser2", generate_password_hash("pass456"))

        app.config["TESTING"] = True
        app._db_initialized = True
        self.client = app.test_client()

    def tearDown(self):
        database.DATABASE_URL = self.original_url
        app._db_initialized = self.original_initialized

    def login_as(self, user_id: int, username: str):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username

    def test_unauthenticated_redirect(self):
        # Unauthenticated request to / should redirect to /login
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # Unauthenticated request to API should return 401
        res_api = self.client.get("/api/dashboard")
        self.assertEqual(res_api.status_code, 401)

    def test_authenticated_page_views(self):
        self.login_as(self.user1_id, "testuser1")

        # Test Dashboard view
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Spending Overview", res.data)

        # Test Transactions view
        res = self.client.get("/transactions")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Transactions", res.data)

        # Test Budget view
        res = self.client.get("/budget")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Budget", res.data)

    def test_user_starts_with_new_fresh_expense_list(self):
        # User 2 logs in
        self.login_as(self.user2_id, "testuser2")

        # Initially User 2 has 0 transactions
        res = self.client.get("/api/transactions")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["entries_count"], 0)
        self.assertEqual(data["total_spent"], 0.0)

    def test_api_add_transaction_isolated_per_user(self):
        # User 1 logs in and adds a transaction
        self.login_as(self.user1_id, "testuser1")
        payload = {
            "amount": 250.0,
            "category": "Food",
            "note": "User 1 Lunch",
            "transaction_date": date.today().isoformat()
        }
        res1 = self.client.post("/api/add-transaction", json=payload)
        self.assertEqual(res1.status_code, 201)

        # Verify User 1 sees it
        res_tx1 = self.client.get("/api/transactions")
        self.assertEqual(res_tx1.get_json()["entries_count"], 1)

        # Now switch to User 2
        self.login_as(self.user2_id, "testuser2")
        # Verify User 2 sees 0 transactions!
        res_tx2 = self.client.get("/api/transactions")
        self.assertEqual(res_tx2.get_json()["entries_count"], 0)

    def test_api_budget_isolation(self):
        # User 1 sets budget to 50000
        self.login_as(self.user1_id, "testuser1")
        self.client.post("/api/update-budget", json={"monthly_limit": 50000.0})

        # User 2 sets budget to 25000
        self.login_as(self.user2_id, "testuser2")
        self.client.post("/api/update-budget", json={"monthly_limit": 25000.0})

        # Check User 2 gets 25000
        res2 = self.client.get("/api/budget")
        self.assertEqual(res2.get_json()["monthly_limit"], 25000.0)

        # Check User 1 gets 50000
        self.login_as(self.user1_id, "testuser1")
        res1 = self.client.get("/api/budget")
        self.assertEqual(res1.get_json()["monthly_limit"], 50000.0)

if __name__ == "__main__":
    unittest.main()
