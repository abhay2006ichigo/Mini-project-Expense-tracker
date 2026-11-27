"""
Session, registration, login, and security tests for Expense Tracker.
"""

import os
import unittest
import database
from app import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL must point to a PostgreSQL test database")
class TestAuth(unittest.TestCase):
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

        app.config["TESTING"] = True
        app._db_initialized = True
        self.client = app.test_client()

    def tearDown(self):
        database.DATABASE_URL = self.original_url
        app._db_initialized = self.original_initialized

    def test_register_and_auto_login(self):
        res = self.client.post("/register", data={
            "username": "newuser",
            "password": "mypassword",
            "confirm_password": "mypassword"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Spending Overview", res.data)

        # Verify user is created in DB
        user = database.get_user_by_username("newuser")
        self.assertIsNotNone(user)

    def test_guest_mode_creates_fresh_user(self):
        res = self.client.get("/guest", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Spending Overview", res.data)

        # Verify in session
        with self.client.session_transaction() as sess:
            self.assertIn("user_id", sess)
            self.assertTrue(sess["username"].startswith("guest_"))

    def test_logout(self):
        # First register/login
        self.client.get("/guest", follow_redirects=True)
        # Now logout
        res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome back", res.data)

        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

if __name__ == "__main__":
    unittest.main()
