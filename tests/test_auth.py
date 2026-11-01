"""
Session, registration, login, and security tests for Expense Tracker.
"""

import os
import unittest
import tempfile
import database
from app import app

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_auth_expenses.db")
        database.DB_FILE = self.test_db
        database.init_db(seed_sample_data=False)

        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

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
