"""
Unit tests for database module with multi-user isolation.
"""

import os
import unittest
import tempfile
from datetime import date
from werkzeug.security import generate_password_hash
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_expenses.db")
        database.DB_FILE = self.test_db
        database.init_db(seed_sample_data=False)
        self.user1_id = database.create_user("alice", generate_password_hash("pass123"))
        self.user2_id = database.create_user("bob", generate_password_hash("pass456"))

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_user_creation_and_retrieval(self):
        user = database.get_user_by_username("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], self.user1_id)
        self.assertEqual(user["username"], "alice")

    def test_per_user_transaction_isolation(self):
        today_str = date.today().isoformat()
        # Alice logs expense
        tx1_id = database.add_transaction(self.user1_id, amount=250.0, category="Food", note="Alice Lunch", transaction_date=today_str)
        # Bob logs expense
        tx2_id = database.add_transaction(self.user2_id, amount=999.0, category="Entertainment", note="Bob Game", transaction_date=today_str)

        # Alice's transactions
        alice_txs = database.get_all_transactions(self.user1_id)
        self.assertEqual(len(alice_txs), 1)
        self.assertEqual(alice_txs[0]["note"], "Alice Lunch")

        # Bob's transactions
        bob_txs = database.get_all_transactions(self.user2_id)
        self.assertEqual(len(bob_txs), 1)
        self.assertEqual(bob_txs[0]["note"], "Bob Game")

        # Alice cannot see Bob's transaction by ID
        self.assertIsNone(database.get_transaction_by_id(self.user1_id, tx2_id))
        self.assertIsNotNone(database.get_transaction_by_id(self.user2_id, tx2_id))

    def test_update_transaction_scoped(self):
        today_str = date.today().isoformat()
        tx_id = database.add_transaction(self.user1_id, amount=100.0, category="Transport", note="Cab", transaction_date=today_str)

        # Bob tries to update Alice's transaction -> fails
        updated_by_bob = database.update_transaction(self.user2_id, tx_id, amount=999.0, category="Transport", note="Hacked", transaction_date=today_str)
        self.assertFalse(updated_by_bob)

        # Alice updates her own transaction -> succeeds
        updated_by_alice = database.update_transaction(self.user1_id, tx_id, amount=150.0, category="Transport", note="Cab with tip", transaction_date=today_str)
        self.assertTrue(updated_by_alice)

        tx = database.get_transaction_by_id(self.user1_id, tx_id)
        self.assertEqual(tx["amount"], 150.0)

    def test_delete_transaction_scoped(self):
        today_str = date.today().isoformat()
        tx_id = database.add_transaction(self.user1_id, amount=50.0, category="Bills", note="Tea", transaction_date=today_str)

        # Bob tries to delete Alice's transaction -> fails
        deleted_by_bob = database.delete_transaction(self.user2_id, tx_id)
        self.assertFalse(deleted_by_bob)
        self.assertIsNotNone(database.get_transaction_by_id(self.user1_id, tx_id))

        # Alice deletes her own transaction -> succeeds
        deleted_by_alice = database.delete_transaction(self.user1_id, tx_id)
        self.assertTrue(deleted_by_alice)
        self.assertIsNone(database.get_transaction_by_id(self.user1_id, tx_id))

    def test_per_user_budget_isolation(self):
        database.set_budget_for_month(self.user1_id, 40000.0, month=11, year=2026)
        database.set_budget_for_month(self.user2_id, 15000.0, month=11, year=2026)

        self.assertEqual(database.get_budget_for_month(self.user1_id, month=11, year=2026), 40000.0)
        self.assertEqual(database.get_budget_for_month(self.user2_id, month=11, year=2026), 15000.0)

    def test_analytics_calculations_per_user(self):
        database.add_transaction(self.user1_id, amount=500.0, category="Food", note="Groceries", transaction_date="2026-11-01")
        database.add_transaction(self.user1_id, amount=300.0, category="Food", note="Dinner", transaction_date="2026-11-02")
        database.add_transaction(self.user2_id, amount=700.0, category="Entertainment", note="Cinema", transaction_date="2026-11-03")

        # Alice's total spent is 800, Bob's is 700
        self.assertEqual(database.get_monthly_spent(self.user1_id, month=11, year=2026), 800.0)
        self.assertEqual(database.get_monthly_spent(self.user2_id, month=11, year=2026), 700.0)

        alice_cat = database.get_category_spending_for_month(self.user1_id, month=11, year=2026)
        self.assertEqual(len(alice_cat), 1)
        self.assertEqual(alice_cat[0]["category"], "Food")
        self.assertEqual(alice_cat[0]["total"], 800.0)

        bob_cat = database.get_category_spending_for_month(self.user2_id, month=11, year=2026)
        self.assertEqual(len(bob_cat), 1)
        self.assertEqual(bob_cat[0]["category"], "Entertainment")
        self.assertEqual(bob_cat[0]["total"], 700.0)

if __name__ == "__main__":
    unittest.main()
